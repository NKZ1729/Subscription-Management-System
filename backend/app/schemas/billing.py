from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

BillingStatus = Literal["Pending", "Processing", "Completed", "Failed"]


class BillingRunRequest(BaseModel):
    run_date: Optional[date] = Field(None, description="Billing day to process up to (defaults to today)")
    dry_run: bool = Field(False, description="Simulate generation without writing to database")


class BillingRecordResponse(BaseModel):
    billing_record_id: int
    subscription_id: int
    invoice_id: Optional[int] = None
    billing_period_start: date
    billing_period_end: date
    scheduled_date: date
    billing_status: BillingStatus
    attempt_count: int
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BillingRunResponse(BaseModel):
    run_date: date
    subscriptions_processed: int
    invoices_generated: int
    total_billed_amount: str
    errors_count: int
    details: List[BillingRecordResponse] = []
