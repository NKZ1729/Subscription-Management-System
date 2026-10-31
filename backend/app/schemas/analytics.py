from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class OverdueInvoiceSummary(BaseModel):
    invoice_id: int
    invoice_number: str
    company_name: str
    due_date: date
    days_overdue: int
    total_amount: Decimal
    outstanding_amount: Decimal


class MonthlyRevenuePoint(BaseModel):
    month: str  # YYYY-MM
    revenue: Decimal
    collections: Decimal


class FinanceDashboardResponse(BaseModel):
    active_subscriptions_count: int
    paused_subscriptions_count: int
    closed_subscriptions_count: int
    total_revenue_invoiced: Decimal
    total_payments_collected: Decimal
    total_amount_outstanding: Decimal
    overdue_invoices_count: int
    overdue_amount_total: Decimal
    mrr_estimate: Decimal  # Monthly Recurring Revenue
    arr_estimate: Decimal  # Annual Recurring Revenue
    recent_overdue_invoices: List[OverdueInvoiceSummary] = []
    revenue_trend: List[MonthlyRevenuePoint] = []
