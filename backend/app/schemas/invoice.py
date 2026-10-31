from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse

InvoiceStatus = Literal["Draft", "Confirmed", "Partially Paid", "Paid", "Cancelled"]


class InvoiceDiscountResponse(BaseModel):
    invoice_discount_id: int
    discount_id: int
    discount_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceLineResponse(BaseModel):
    invoice_line_id: int
    product_id: int
    description: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    tax_name: Optional[str] = None
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    invoice_id: int
    invoice_number: str
    subscription_id: int
    customer_id: int
    issue_date: date
    due_date: date
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_amount: Decimal = Decimal("0.00")
    outstanding_amount: Decimal = Decimal("0.00")
    is_overdue: bool = False
    customer: Optional[CustomerResponse] = None
    lines: List[InvoiceLineResponse] = []
    discounts: List[InvoiceDiscountResponse] = []

    class Config:
        from_attributes = True


class InvoiceStatusUpdate(BaseModel):
    status: Literal["Confirmed", "Cancelled"]
    note: Optional[str] = None

