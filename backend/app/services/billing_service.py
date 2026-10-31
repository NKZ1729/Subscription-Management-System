import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.billing import BillingRecord
from app.models.invoice import Invoice, InvoiceDiscount, InvoiceLine
from app.models.product import Plan
from app.models.subscription import Subscription
from app.models.tax_discount import DiscountUsage
from app.services.discount_service import evaluate_eligible_discounts


def _calculate_next_date(start: date, interval: str, count: int) -> date:
    count = max(1, count)
    if interval == "daily":
        return start + timedelta(days=count)
    elif interval == "weekly":
        return start + timedelta(weeks=count)
    elif interval == "monthly":
        year = start.year + (start.month + count - 1) // 12
        month = (start.month + count - 1) % 12 + 1
        day = min(start.day, 28)
        return date(year, month, day)
    elif interval == "yearly":
        return date(start.year + count, start.month, min(start.day, 28))
    return start + timedelta(days=30)


def _determine_due_date(issue_date: date, terms: Optional[str]) -> date:
    terms_lower = (terms or "").lower().strip()
    if "immediate" in terms_lower or "due on receipt" in terms_lower:
        return issue_date
    elif "net 30" in terms_lower or "30 days" in terms_lower:
        return issue_date + timedelta(days=30)
    elif "net 15" in terms_lower or "15 days" in terms_lower:
        return issue_date + timedelta(days=15)
    elif "net 60" in terms_lower:
        return issue_date + timedelta(days=60)
    return issue_date + timedelta(days=15)


def run_billing_day(
    db: Session,
    run_date: Optional[date] = None,
    dry_run: bool = False,
) -> Tuple[int, int, Decimal, int, List[BillingRecord]]:
    """
    Core recurring billing engine that processes all active subscriptions due for billing.
    Guarantees idempotency via billing_records to ensure no double-billing or skipped cycles.
    """
    billing_date = run_date or date.today()

    due_subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.status == "Active",
            Subscription.next_billing_date != None,
            Subscription.next_billing_date <= billing_date,
        )
        .all()
    )

    subscriptions_processed = 0
    invoices_generated = 0
    total_billed = Decimal("0.00")
    errors_count = 0
    records: List[BillingRecord] = []

    for sub in due_subscriptions:
        subscriptions_processed += 1
        period_start = sub.next_billing_date
        period_end = _calculate_next_date(
            period_start, sub.plan.billing_interval, sub.plan.interval_count
        ) - timedelta(days=1)

        # 1. Idempotency Check: prevent double billing
        existing_record = (
            db.query(BillingRecord)
            .filter(
                BillingRecord.subscription_id == sub.subscription_id,
                BillingRecord.billing_period_start == period_start,
                BillingRecord.billing_period_end == period_end,
            )
            .first()
        )

        if existing_record and existing_record.billing_status in ["Completed", "Processing"]:
            # Already billed for this period!
            continue

        if dry_run:
            invoices_generated += 1
            continue

        try:
            # 2. Compute Invoice Lines, Subtotals, and Taxes
            subtotal = Decimal("0.00")
            tax_total = Decimal("0.00")
            total_qty = 0
            lines_data = []

            for line in sub.lines:
                qty = line.quantity
                u_price = Decimal(str(line.unit_price))
                line_sub = u_price * Decimal(str(qty))
                total_qty += qty
                subtotal += line_sub

                tax_name = None
                tax_rate = Decimal("0.00")
                tax_amt = Decimal("0.00")

                if line.tax:
                    tax_name = line.tax.tax_name
                    tax_rate = Decimal(str(line.tax.tax_rate))
                    tax_amt = line_sub * (tax_rate / Decimal("100.00"))
                    tax_total += tax_amt

                line_tot = line_sub + tax_amt
                lines_data.append({
                    "product_id": line.product_id,
                    "description": line.product.name if line.product else "Subscription Product",
                    "quantity": qty,
                    "unit_price": u_price,
                    "subtotal": line_sub,
                    "tax_name": tax_name,
                    "tax_rate": tax_rate,
                    "tax_amount": tax_amt,
                    "line_total": line_tot,
                })

            # 3. Evaluate and Apply Discounts
            eligible_discounts = evaluate_eligible_discounts(
                subscription=sub,
                subtotal=subtotal,
                total_quantity=total_qty,
                db=db,
                eval_date=billing_date,
            )

            discount_total = Decimal("0.00")
            for disc, d_amt in eligible_discounts:
                discount_total += d_amt

            # Cap discount at subtotal
            discount_total = min(discount_total, subtotal)
            invoice_total = subtotal - discount_total + tax_total

            due_date = _determine_due_date(billing_date, sub.payment_terms)
            inv_number = f"INV-{billing_date.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

            # 4. Create Invoice
            invoice = Invoice(
                invoice_number=inv_number,
                subscription_id=sub.subscription_id,
                customer_id=sub.customer_id,
                issue_date=billing_date,
                due_date=due_date,
                billing_period_start=period_start,
                billing_period_end=period_end,
                subtotal=subtotal,
                discount_total=discount_total,
                tax_total=tax_total,
                total_amount=invoice_total,
                status="Draft",
                notes=f"Recurring billing for {sub.subscription_number}",
            )
            db.add(invoice)
            db.flush()

            # 5. Create Invoice Lines
            for ld in lines_data:
                inv_line = InvoiceLine(
                    invoice_id=invoice.invoice_id,
                    product_id=ld["product_id"],
                    description=ld["description"],
                    quantity=ld["quantity"],
                    unit_price=ld["unit_price"],
                    subtotal=ld["subtotal"],
                    discount_amount=Decimal("0.00"),
                    tax_name=ld["tax_name"],
                    tax_rate=ld["tax_rate"],
                    tax_amount=ld["tax_amount"],
                    line_total=ld["line_total"],
                )
                db.add(inv_line)

            # 6. Record Applied Discounts
            for disc, d_amt in eligible_discounts:
                inv_disc = InvoiceDiscount(
                    invoice_id=invoice.invoice_id,
                    discount_id=disc.discount_id,
                    discount_amount=d_amt,
                )
                db.add(inv_disc)

                disc_usage = DiscountUsage(
                    discount_id=disc.discount_id,
                    subscription_id=sub.subscription_id,
                    discount_amount=d_amt,
                )
                db.add(disc_usage)

            # 7. Create/Update Billing Record
            if not existing_record:
                existing_record = BillingRecord(
                    subscription_id=sub.subscription_id,
                    invoice_id=invoice.invoice_id,
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                    scheduled_date=billing_date,
                    billing_status="Completed",
                    attempt_count=1,
                    processed_at=datetime.now(timezone.utc),
                )
                db.add(existing_record)
            else:
                existing_record.invoice_id = invoice.invoice_id
                existing_record.billing_status = "Completed"
                existing_record.attempt_count += 1
                existing_record.processed_at = datetime.now(timezone.utc)

            # 8. Advance Subscription next_billing_date
            next_date = _calculate_next_date(period_start, sub.plan.billing_interval, sub.plan.interval_count)
            sub.next_billing_date = next_date

            # Auto-close check if plan specifies auto_close
            if sub.plan.auto_close and sub.expiry_date and next_date > sub.expiry_date:
                sub.status = "Closed"

            db.commit()
            invoices_generated += 1
            total_billed += invoice_total
            records.append(existing_record)

        except Exception as e:
            db.rollback()
            errors_count += 1
            # Record failed attempt
            failed_record = BillingRecord(
                subscription_id=sub.subscription_id,
                billing_period_start=period_start,
                billing_period_end=period_end,
                scheduled_date=billing_date,
                billing_status="Failed",
                attempt_count=1,
                processed_at=datetime.now(timezone.utc),
                error_message=str(e),
            )
            db.add(failed_record)
            db.commit()
            records.append(failed_record)

    return subscriptions_processed, invoices_generated, total_billed, errors_count, records

