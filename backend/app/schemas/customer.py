from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    company_name: str
    contact_email: EmailStr
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
