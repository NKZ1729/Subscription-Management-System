from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Numeric,
    String,
    Boolean,
    Text,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    product_type = Column(String(50), nullable=False)
    sales_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    plan_products = relationship("PlanProduct", back_populates="product")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    variant_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    variant_name = Column(String(100), nullable=False)
    additional_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "variant_name", name="unique_product_variant"),
    )

    product = relationship("Product", back_populates="variants")


class Plan(Base):
    __tablename__ = "plans"

    plan_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    plan_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    billing_interval = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    interval_count = Column(Integer, nullable=False, default=1)
    minimum_quantity = Column(Integer, nullable=False, default=1)
    available_from = Column(Date, nullable=False)
    available_until = Column(Date, nullable=True)
    auto_close = Column(Boolean, nullable=False, default=False)
    allow_early_close = Column(Boolean, nullable=False, default=True)
    allow_pause = Column(Boolean, nullable=False, default=True)
    allow_renewal = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    plan_products = relationship("PlanProduct", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="plan")
    templates = relationship("QuotationTemplate", back_populates="plan")


class PlanProduct(Base):
    __tablename__ = "plan_products"

    plan_product_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    plan_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("plans.plan_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    plan = relationship("Plan", back_populates="plan_products")
    product = relationship("Product", back_populates="plan_products")
    variant = relationship("ProductVariant")
