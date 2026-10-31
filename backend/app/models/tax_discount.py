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
    Table,
)
from sqlalchemy.orm import relationship
from app.core.database import Base

discount_products = Table(
    "discount_products",
    Base.metadata,
    Column("discount_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("discounts.discount_id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True),
)


class Tax(Base):
    __tablename__ = "taxes"

    tax_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tax_name = Column(String(100), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Discount(Base):
    __tablename__ = "discounts"

    discount_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    discount_name = Column(String(150), nullable=False)
    discount_type = Column(String(20), nullable=False)  # 'fixed', 'percentage'
    discount_value = Column(Numeric(12, 2), nullable=False)
    applies_to = Column(String(20), nullable=False)  # 'product', 'subscription'
    minimum_purchase = Column(Numeric(12, 2), default=0.0)
    minimum_quantity = Column(Integer, default=1)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    applicable_products = relationship("Product", secondary=discount_products)
    usages = relationship("DiscountUsage", back_populates="discount")
    creator = relationship("User")


class DiscountUsage(Base):
    __tablename__ = "discount_usages"

    usage_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    discount_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("discounts.discount_id", ondelete="RESTRICT"), nullable=False)
    subscription_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("subscriptions.subscription_id", ondelete="RESTRICT"), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    discount = relationship("Discount", back_populates="usages")
    subscription = relationship("Subscription", back_populates="discount_usages")
