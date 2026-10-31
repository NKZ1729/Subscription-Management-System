from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

PaymentStatus = Literal["Pending", "Completed", "Failed", "Refunded"]
PaymentMethod = Literal["Credit Card", "Bank Transfer", "Cash", "UPI", "Cheque", "Other"]


class PaymentAllocationCreate(BaseModel):
    invoice_id: int
    allocated_amount: Decimal = Field(..., gt=0, example=500.00)


class PaymentAllocationResponse(BaseModel):
    allocation_id: int
    payment_id: int
    invoice_id: int
    allocated_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    payment_method: str = Field(..., example="Bank Transfer")
    amount: Decimal = Field(..., gt=0, example=1200.00)
    payment_date: Optional[datetime] = Field(None, example="2026-10-31T12:00:00Z")
    reference_number: Optional[str] = Field(None, example="TXN-987654321")
    note: Optional[str] = Field(None, example="October subscription fee paid in full")
    allocations: List[PaymentAllocationCreate] = Field(
        ..., min_length=1, description="One or more invoices this payment applies to"
    )


class PaymentResponse(BaseModel):
    payment_id: int
    payment_method: str
    amount: Decimal
    payment_date: datetime
    reference_number: Optional[str] = None
    note: Optional[str] = None
    status: PaymentStatus
    created_at: datetime
    allocations: List[PaymentAllocationResponse] = []

    class Config:
        from_attributes = True

