from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    role_name = Column(String(30), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    role_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(150), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    role = relationship("Role", back_populates="users")
    customer_associations = relationship("CustomerUser", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=False)
    contact_email = Column(String(255), nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    billing_address = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user_associations = relationship("CustomerUser", back_populates="customer", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")


class CustomerUser(Base):
    __tablename__ = "customer_users"

    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.customer_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    is_primary_contact = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    customer = relationship("Customer", back_populates="user_associations")
    user = relationship("User", back_populates="customer_associations")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="reset_tokens")

