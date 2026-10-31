from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserResponse(UserBase):
    user_id: int
    role_id: int
    role: Optional[RoleResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
