from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class BillingRecord(Base):
    __tablename__ = "billing_records"

    billing_record_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("subscriptions.subscription_id", ondelete="RESTRICT"), nullable=False)
    invoice_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("invoices.invoice_id", ondelete="RESTRICT"), unique=True, nullable=True)
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    billing_status = Column(String(30), nullable=False, default="Pending")  # 'Pending', 'Processing', 'Completed', 'Failed'
    attempt_count = Column(Integer, nullable=False, default=0)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("subscription_id", "billing_period_start", "billing_period_end", name="unique_subscription_billing_period"),
    )

    subscription = relationship("Subscription", back_populates="billing_records")
    invoice = relationship("Invoice", back_populates="billing_record")
