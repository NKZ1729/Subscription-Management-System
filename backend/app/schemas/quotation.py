from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse, VariantResponse
from app.schemas.plan import PlanResponse


# ----------------- Quotation Template Lines -----------------

class QuotationTemplateLineBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(default=1, gt=0, example=1)
    unit_price: Decimal = Field(..., ge=0, example=1200.00)


class QuotationTemplateLineCreate(QuotationTemplateLineBase):
    pass


class QuotationTemplateLineResponse(QuotationTemplateLineBase):
    template_line_id: int
    template_id: int
    product: Optional[ProductResponse] = None
    variant: Optional[VariantResponse] = None

    class Config:
        from_attributes = True


# ----------------- Quotation Templates -----------------

class QuotationTemplateBase(BaseModel):
    template_name: str = Field(..., max_length=150, example="Standard SaaS Annual Offer")
    plan_id: int
    validity_days: int = Field(default=30, gt=0, example=30)
    is_active: bool = True


class QuotationTemplateCreate(QuotationTemplateBase):
    lines: Optional[List[QuotationTemplateLineCreate]] = Field(default_factory=list)


class QuotationTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, max_length=150)
    plan_id: Optional[int] = None
    validity_days: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class QuotationTemplateResponse(QuotationTemplateBase):
    template_id: int
    created_by: int
    created_at: datetime
    plan: Optional[PlanResponse] = None
    lines: List[QuotationTemplateLineResponse] = []

    class Config:
        from_attributes = True

