from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_staff_or_admin
from app.models.invoice import Invoice
from app.models.payment import Payment, PaymentAllocation
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


def _update_invoice_payment_status(invoice: Invoice, db: Session) -> None:
    total_allocated = (
        db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00")))
        .filter(PaymentAllocation.invoice_id == invoice.invoice_id)
        .scalar()
        or Decimal("0.00")
    )

    tot = Decimal(str(invoice.total_amount))
    if total_allocated >= tot and tot > 0:
        invoice.status = "Paid"
    elif total_allocated > 0:
        invoice.status = "Partially Paid"
    elif invoice.status in ["Paid", "Partially Paid"]:
        invoice.status = "Confirmed"


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    method: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: List recorded payments with their invoice allocations.
    """
    query = db.query(Payment)
    if method:
        query = query.filter(Payment.payment_method == method)
    if status_filter:
        query = query.filter(Payment.status == status_filter)

    return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Retrieve single payment transaction details.
    """
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Record payment and allocate funds against one or more invoices.
    Automatically updates affected invoices to 'Paid' or 'Partially Paid'.
    """
    # 1. Validate allocation sum does not exceed total payment amount
    alloc_sum = sum(a.allocated_amount for a in payment_in.allocations)
    if alloc_sum > payment_in.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Total allocated amount ({alloc_sum}) exceeds payment amount ({payment_in.amount})",
        )

    # 2. Create Payment record
    payment = Payment(
        payment_method=payment_in.payment_method,
        amount=payment_in.amount,
        payment_date=payment_in.payment_date or datetime.now(timezone.utc),
        reference_number=payment_in.reference_number,
        note=payment_in.note,
        status="Completed",
    )
    db.add(payment)
    db.flush()

    # 3. Create Allocations and update invoices
    affected_invoices: List[Invoice] = []
    for alloc_in in payment_in.allocations:
        invoice = db.query(Invoice).filter(Invoice.invoice_id == alloc_in.invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=400,
                detail=f"Invoice with ID {alloc_in.invoice_id} not found",
            )
        if invoice.status == "Cancelled":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot apply payment to cancelled invoice {invoice.invoice_number}",
            )

        allocation = PaymentAllocation(
            payment_id=payment.payment_id,
            invoice_id=invoice.invoice_id,
            allocated_amount=alloc_in.allocated_amount,
        )
        db.add(allocation)
        affected_invoices.append(invoice)

    db.flush()

    # 4. Recalculate invoice statuses
    for inv in affected_invoices:
        _update_invoice_payment_status(inv, db)

    db.commit()
    db.refresh(payment)
    return payment
