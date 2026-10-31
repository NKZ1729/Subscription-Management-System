from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ----------------- Product Variants -----------------

class VariantBase(BaseModel):
    variant_name: str = Field(..., max_length=100, example="Odoo Brand")
    additional_price: Decimal = Field(default=Decimal("0.00"), ge=0, example=560.00)
    is_active: bool = True


class VariantCreate(VariantBase):
    pass


class VariantUpdate(BaseModel):
    variant_name: Optional[str] = Field(None, max_length=100)
    additional_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class VariantResponse(VariantBase):
    variant_id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- Products -----------------

class ProductBase(BaseModel):
    name: str = Field(..., max_length=200, example="BrightERP Subscription Core")
    product_type: str = Field(..., max_length=50, example="Software")
    sales_price: Decimal = Field(..., ge=0, example=1200.00)
    cost_price: Decimal = Field(..., ge=0, example=300.00)
    notes: Optional[str] = Field(None, example="Core ERP license with cloud backup")
    is_active: bool = True


class ProductCreate(ProductBase):
    variants: Optional[List[VariantCreate]] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    product_type: Optional[str] = Field(None, max_length=50)
    sales_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime
    variants: List[VariantResponse] = []

    class Config:
        from_attributes = True
