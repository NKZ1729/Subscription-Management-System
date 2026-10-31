from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_staff_or_admin
from app.models.invoice import Invoice
from app.models.payment import Payment, PaymentAllocation
from app.models.subscription import Subscription, SubscriptionLine
from app.models.user import Customer, User
from app.schemas.analytics import (
    FinanceDashboardResponse,
    MonthlyRevenuePoint,
    OverdueInvoiceSummary,
)

router = APIRouter(prefix="/analytics", tags=["Finance & Analytics"])


@router.get("/dashboard", response_model=FinanceDashboardResponse)
def get_finance_dashboard(
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Finance Lead Executive Dashboard:
    Aggregated KPIs optimized for sub-second query execution across large datasets:
    - Active, Paused, and Closed subscriptions
    - Invoiced Revenue, Collections, and Outstanding balances
    - Overdue invoices count and total amount
    - MRR and ARR estimations
    """
    today = date.today()

    # 1. Subscriptions KPIs
    sub_counts = (
        db.query(
            func.count(case((Subscription.status == "Active", 1))).label("active"),
            func.count(case((Subscription.status == "Paused", 1))).label("paused"),
            func.count(case((Subscription.status == "Closed", 1))).label("closed"),
        )
        .first()
    )
    active_subs = sub_counts.active or 0
    paused_subs = sub_counts.paused or 0
    closed_subs = sub_counts.closed or 0

    # 2. Invoicing & Collections KPIs
    total_invoiced = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")))
        .filter(Invoice.status != "Cancelled")
        .scalar()
        or Decimal("0.00")
    )

    total_collected = (
        db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
        .filter(Payment.status == "Completed")
        .scalar()
        or Decimal("0.00")
    )

    outstanding = max(Decimal("0.00"), total_invoiced - total_collected)

    # 3. Overdue Invoices
    overdue_invoices_query = (
        db.query(Invoice)
        .join(Customer, Invoice.customer_id == Customer.customer_id)
        .filter(
            Invoice.due_date < today,
            Invoice.status.notin_(["Paid", "Cancelled"]),
        )
        .all()
    )

    overdue_count = len(overdue_invoices_query)
    overdue_total = Decimal("0.00")
    overdue_summaries: List[OverdueInvoiceSummary] = []

    for inv in overdue_invoices_query[:10]:  # Top 10 for dashboard preview
        paid_sum = (
            db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00")))
            .filter(PaymentAllocation.invoice_id == inv.invoice_id)
            .scalar()
            or Decimal("0.00")
        )
        inv_tot = Decimal(str(inv.total_amount))
        inv_outstanding = max(Decimal("0.00"), inv_tot - paid_sum)
        overdue_total += inv_outstanding

        days = (today - inv.due_date).days
        overdue_summaries.append(
            OverdueInvoiceSummary(
                invoice_id=inv.invoice_id,
                invoice_number=inv.invoice_number,
                company_name=inv.customer.company_name if inv.customer else "Unknown",
                due_date=inv.due_date,
                days_overdue=days,
                total_amount=inv_tot,
                outstanding_amount=inv_outstanding,
            )
        )

    # For overdue total across all (not just top 10)
    if overdue_count > 10:
        overdue_total = Decimal("0.00")
        for inv in overdue_invoices_query:
            paid_sum = (
                db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00")))
                .filter(PaymentAllocation.invoice_id == inv.invoice_id)
                .scalar()
                or Decimal("0.00")
            )
            overdue_total += max(Decimal("0.00"), Decimal(str(inv.total_amount)) - paid_sum)

    # 4. MRR / ARR Estimation across Active subscriptions
    active_subscriptions = (
        db.query(Subscription)
        .filter(Subscription.status == "Active")
        .all()
    )

    mrr = Decimal("0.00")
    for s in active_subscriptions:
        sub_sum = Decimal("0.00")
        for l in s.lines:
            sub_sum += Decimal(str(l.unit_price)) * Decimal(str(l.quantity))

        interval = s.plan.billing_interval if s.plan else "monthly"
        count = s.plan.interval_count if s.plan else 1
        count = max(1, count)

        if interval == "monthly":
            mrr += sub_sum / Decimal(str(count))
        elif interval == "yearly":
            mrr += sub_sum / (Decimal(str(count)) * Decimal("12.00"))
        elif interval == "weekly":
            mrr += (sub_sum * Decimal("4.33")) / Decimal(str(count))
        elif interval == "daily":
            mrr += (sub_sum * Decimal("30.00")) / Decimal(str(count))

    arr = mrr * Decimal("12.00")

    # 5. Monthly Revenue Trend (Last 6 Months)
    revenue_trend: List[MonthlyRevenuePoint] = []
    current_month_start = date(today.year, today.month, 1)

    for i in range(5, -1, -1):
        # Calculate target month
        year = current_month_start.year
        month = current_month_start.month - i
        while month <= 0:
            month += 12
            year -= 1
        
        m_start = date(year, month, 1)
        next_m_year = year + (month // 12)
        next_m_month = (month % 12) + 1
        m_end = date(next_m_year, next_m_month, 1) - timedelta(days=1)

        m_invoiced = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")))
            .filter(
                Invoice.issue_date >= m_start,
                Invoice.issue_date <= m_end,
                Invoice.status != "Cancelled",
            )
            .scalar()
            or Decimal("0.00")
        )

        m_collected = (
            db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
            .filter(
                func.date(Payment.payment_date) >= m_start,
                func.date(Payment.payment_date) <= m_end,
                Payment.status == "Completed",
            )
            .scalar()
            or Decimal("0.00")
        )

        revenue_trend.append(
            MonthlyRevenuePoint(
                month=f"{year}-{month:02d}",
                revenue=m_invoiced,
                collections=m_collected,
            )
        )

    return FinanceDashboardResponse(
        active_subscriptions_count=active_subs,
        paused_subscriptions_count=paused_subs,
        closed_subscriptions_count=closed_subs,
        total_revenue_invoiced=total_invoiced,
        total_payments_collected=total_collected,
        total_amount_outstanding=outstanding,
        overdue_invoices_count=overdue_count,
        overdue_amount_total=overdue_total,
        mrr_estimate=mrr.quantize(Decimal("0.01")),
        arr_estimate=arr.quantize(Decimal("0.01")),
        recent_overdue_invoices=overdue_summaries,
        revenue_trend=revenue_trend,
    )
