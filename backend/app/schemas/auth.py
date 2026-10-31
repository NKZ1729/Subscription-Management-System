from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.core.security import validate_password_strength


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    email: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str
    phone: Optional[str] = None
    billing_address: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class StaffCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_id: int

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        is_valid, msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(msg)
        return v

