from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Numeric,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reference_number = Column(String(150), nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="Completed")  # 'Pending', 'Completed', 'Failed', 'Refunded'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    allocation_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    payment_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("payments.payment_id", ondelete="RESTRICT"), nullable=False)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.invoice_id", ondelete="RESTRICT"), nullable=False)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_id", name="unique_payment_invoice"),
    )

    payment = relationship("Payment", back_populates="allocations")
    invoice = relationship("Invoice", back_populates="allocations")

