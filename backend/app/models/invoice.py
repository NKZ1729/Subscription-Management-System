from datetime import datetime, timezone, date
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Numeric,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    subscription_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("subscriptions.subscription_id", ondelete="RESTRICT"), nullable=False)
    customer_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False)
    issue_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=False)
    billing_period_start = Column(Date, nullable=True)
    billing_period_end = Column(Date, nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.0)
    discount_total = Column(Numeric(12, 2), nullable=False, default=0.0)
    tax_total = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="Draft")  # 'Draft', 'Confirmed', 'Partially Paid', 'Paid', 'Cancelled'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    discounts = relationship("InvoiceDiscount", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", back_populates="invoice")
    billing_record = relationship("BillingRecord", back_populates="invoice", uselist=False)


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    invoice_line_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.invoice_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    tax_name = Column(String(100), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0.0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    line_total = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product")


class InvoiceDiscount(Base):
    __tablename__ = "invoice_discounts"

    invoice_discount_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.invoice_id", ondelete="CASCADE"), nullable=False)
    discount_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("discounts.discount_id", ondelete="RESTRICT"), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice = relationship("Invoice", back_populates="discounts")
    discount = relationship("Discount")

