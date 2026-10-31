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
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"

    template_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    template_name = Column(String(150), nullable=False)
    plan_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("plans.plan_id", ondelete="RESTRICT"), nullable=False)
    validity_days = Column(Integer, nullable=False, default=30)
    created_by = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    plan = relationship("Plan", back_populates="templates")
    creator = relationship("User")
    lines = relationship("QuotationTemplateLine", back_populates="template", cascade="all, delete-orphan")


class QuotationTemplateLine(Base):
    __tablename__ = "quotation_template_lines"

    template_line_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    template_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("quotation_templates.template_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)

    template = relationship("QuotationTemplate", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False)
    plan_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("plans.plan_id", ondelete="RESTRICT"), nullable=False)
    template_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("quotation_templates.template_id", ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    quotation_valid_until = Column(Date, nullable=True)
    next_billing_date = Column(Date, nullable=True)
    payment_terms = Column(String(150), nullable=True)
    status = Column(String(30), nullable=False, default="Draft")  # 'Draft', 'Quotation', 'Confirmed', 'Active', 'Paused', 'Closed'
    created_by = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    template = relationship("QuotationTemplate")
    creator = relationship("User")
    lines = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription")
    discount_usages = relationship("DiscountUsage", back_populates="subscription")
    billing_records = relationship("BillingRecord", back_populates="subscription")


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    subscription_line_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("product_variants.variant_id", ondelete="RESTRICT"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("taxes.tax_id", ondelete="RESTRICT"), nullable=True)

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    tax = relationship("Tax")

