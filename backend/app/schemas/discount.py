from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ----------------- Taxes -----------------

class TaxBase(BaseModel):
    tax_name: str = Field(..., max_length=100, example="GST 18%")
    tax_rate: Decimal = Field(..., ge=0, le=100, example=18.00)
    description: Optional[str] = Field(None, example="Standard Goods and Services Tax")
    is_active: bool = True


class TaxCreate(TaxBase):
    pass


class TaxUpdate(BaseModel):
    tax_name: Optional[str] = Field(None, max_length=100)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TaxResponse(TaxBase):
    tax_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- Discounts -----------------

DiscountType = Literal["fixed", "percentage"]
DiscountAppliesTo = Literal["product", "subscription"]


class DiscountBase(BaseModel):
    discount_name: str = Field(..., max_length=150, example="Volume Seat Discount")
    discount_type: DiscountType = Field(..., example="percentage")
    discount_value: Decimal = Field(..., gt=0, example=15.00)
    applies_to: DiscountAppliesTo = Field(..., example="subscription")
    minimum_purchase: Decimal = Field(default=Decimal("0.00"), ge=0, example=500.00)
    minimum_quantity: int = Field(default=1, gt=0, example=5)
    start_date: date = Field(..., example="2026-01-01")
    end_date: Optional[date] = Field(None, example="2026-12-31")
    usage_limit: Optional[int] = Field(None, gt=0, example=100)
    is_active: bool = True


class DiscountCreate(DiscountBase):
    product_ids: Optional[List[int]] = Field(default_factory=list, description="Associated product IDs if applies_to == 'product'")


class DiscountUpdate(BaseModel):
    discount_name: Optional[str] = Field(None, max_length=150)
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, gt=0)
    applies_to: Optional[DiscountAppliesTo] = None
    minimum_purchase: Optional[Decimal] = Field(None, ge=0)
    minimum_quantity: Optional[int] = Field(None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    product_ids: Optional[List[int]] = None


class DiscountResponse(DiscountBase):
    discount_id: int
    created_by: int
    created_at: datetime
    applied_count: int = 0
    product_ids: List[int] = []

    class Config:
        from_attributes = True
