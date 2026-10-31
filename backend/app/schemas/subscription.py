from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse, VariantResponse
from app.schemas.plan import PlanResponse


SubscriptionStatus = Literal["Draft", "Quotation", "Confirmed", "Active", "Paused", "Closed"]


# ----------------- Subscription Lines -----------------

class SubscriptionLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, gt=0, example=1)
    unit_price: Decimal = Field(..., ge=0, example=1200.00)
    tax_id: Optional[int] = None


class SubscriptionLineCreate(SubscriptionLineBase):
    pass


class SubscriptionLineResponse(SubscriptionLineBase):
    subscription_line_id: int
    subscription_id: int
    product: Optional[ProductResponse] = None
    variant: Optional[VariantResponse] = None
    line_total: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ----------------- Subscriptions -----------------

class SubscriptionBase(BaseModel):
    customer_id: int
    plan_id: Optional[int] = None
    template_id: Optional[int] = None
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quotation_valid_until: Optional[date] = None
    payment_terms: Optional[str] = Field("Immediate", example="Net 30")


class SubscriptionCreate(SubscriptionBase):
    subscription_number: Optional[str] = Field(None, example="SUB-2026-0001")
    lines: Optional[List[SubscriptionLineCreate]] = Field(default_factory=list)


class SubscriptionUpdate(BaseModel):
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    quotation_valid_until: Optional[date] = None
    payment_terms: Optional[str] = None


class SubscriptionStatusTransition(BaseModel):
    note: Optional[str] = Field(None, example="Approved by customer via email")


class SubscriptionResponse(SubscriptionBase):
    subscription_id: int
    subscription_number: str
    status: SubscriptionStatus
    next_billing_date: Optional[date] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerResponse] = None
    plan: Optional[PlanResponse] = None
    lines: List[SubscriptionLineResponse] = []
    subtotal: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")

    class Config:
        from_attributes = True
