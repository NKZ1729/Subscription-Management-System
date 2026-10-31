from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.product import ProductResponse, VariantResponse


# ----------------- Plan Products -----------------

class PlanProductBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, gt=0, example=1)
    unit_price: Decimal = Field(..., ge=0, example=1200.00)


class PlanProductCreate(PlanProductBase):
    pass


class PlanProductResponse(PlanProductBase):
    plan_product_id: int
    plan_id: int
    created_at: datetime
    product: Optional[ProductResponse] = None
    variant: Optional[VariantResponse] = None

    class Config:
        from_attributes = True


# ----------------- Plans -----------------

BillingIntervalType = Literal["daily", "weekly", "monthly", "yearly"]


class PlanBase(BaseModel):
    plan_name: str = Field(..., max_length=150, example="Enterprise Monthly Plan")
    description: Optional[str] = Field(None, example="Complete suite for enterprise accounts billed monthly")
    billing_interval: BillingIntervalType = Field(default="monthly", example="monthly")
    interval_count: int = Field(default=1, gt=0, example=1)
    minimum_quantity: int = Field(default=1, gt=0, example=1)
    available_from: date = Field(..., example="2026-01-01")
    available_until: Optional[date] = Field(None, example="2026-12-31")
    auto_close: bool = Field(default=False, description="Closes automatically when validity ends")
    allow_early_close: bool = Field(default=True, description="Allows early termination")
    allow_pause: bool = Field(default=True, description="Allows customer or staff to pause subscription")
    allow_renewal: bool = Field(default=True, description="Allows renewing subscription")
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self):
        if self.available_until and self.available_until < self.available_from:
            raise ValueError("available_until cannot be earlier than available_from")
        return self


class PlanCreate(PlanBase):
    products: Optional[List[PlanProductCreate]] = Field(default_factory=list)


class PlanUpdate(BaseModel):
    plan_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    billing_interval: Optional[BillingIntervalType] = None
    interval_count: Optional[int] = Field(None, gt=0)
    minimum_quantity: Optional[int] = Field(None, gt=0)
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    auto_close: Optional[bool] = None
    allow_early_close: Optional[bool] = None
    allow_pause: Optional[bool] = None
    allow_renewal: Optional[bool] = None
    is_active: Optional[bool] = None


class PlanResponse(PlanBase):
    plan_id: int
    created_at: datetime
    updated_at: datetime
    plan_products: List[PlanProductResponse] = []
    total_cost: Optional[Decimal] = Decimal("0.00")

    class Config:
        from_attributes = True

