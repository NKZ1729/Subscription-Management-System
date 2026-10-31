from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_staff_or_admin
from app.models.invoice import Invoice, InvoiceLine, InvoiceDiscount
from app.models.payment import PaymentAllocation
from app.models.user import Customer, CustomerUser, User
from app.schemas.invoice import InvoiceResponse, InvoiceStatusUpdate

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def _compute_invoice_response(inv: Invoice, db: Session) -> InvoiceResponse:
    # Sum paid allocations
    paid_sum = (
        db.query(func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00")))
        .filter(PaymentAllocation.invoice_id == inv.invoice_id)
        .scalar()
        or Decimal("0.00")
    )

    tot = Decimal(str(inv.total_amount))
    outstanding = max(Decimal("0.00"), tot - paid_sum)
    today = date.today()
    is_overdue = (inv.due_date < today) and (inv.status not in ["Paid", "Cancelled"])

    resp = InvoiceResponse.model_validate(inv)
    resp.paid_amount = paid_sum
    resp.outstanding_amount = outstanding
    resp.is_overdue = is_overdue
    return resp


def _get_customer_id_for_user(user: User, db: Session) -> Optional[int]:
    cust_user = db.query(CustomerUser).filter(CustomerUser.user_id == user.user_id).first()
    return cust_user.customer_id if cust_user else None


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    subscription_id: Optional[int] = Query(None),
    overdue_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List invoices.
    - Customers: view only their own invoices through self-service portal.
    - Staff & Admins: view all invoices with status, customer, subscription, and overdue filters.
    """
    query = db.query(Invoice)

    user_role = current_user.role.role_name if current_user.role else "Customer"
    if user_role == "Customer":
        user_cust_id = _get_customer_id_for_user(current_user, db)
        if not user_cust_id:
            return []
        query = query.filter(Invoice.customer_id == user_cust_id)
    else:
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)

    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    if overdue_only:
        today = date.today()
        query = query.filter(
            Invoice.due_date < today,
            Invoice.status.notin_(["Paid", "Cancelled"]),
        )

    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return [_compute_invoice_response(inv, db) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single invoice by ID with line items, tax breakdown, and applied discounts.
    """
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    user_role = current_user.role.role_name if current_user.role else "Customer"
    if user_role == "Customer":
        user_cust_id = _get_customer_id_for_user(current_user, db)
        if inv.customer_id != user_cust_id:
            raise HTTPException(status_code=403, detail="Access denied to this invoice")

    return _compute_invoice_response(inv, db)


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Move invoice from Draft to Confirmed.
    """
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.status != "Draft":
        raise HTTPException(status_code=400, detail=f"Cannot confirm invoice in status '{inv.status}'")

    inv.status = "Confirmed"
    db.commit()
    db.refresh(inv)
    return _compute_invoice_response(inv, db)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Cancel an invoice.
    """
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if inv.status == "Paid":
        raise HTTPException(status_code=400, detail="Cannot cancel a fully paid invoice")

    inv.status = "Cancelled"
    db.commit()
    db.refresh(inv)
    return _compute_invoice_response(inv, db)


@router.get("/{invoice_id}/print")
def print_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Formatted invoice printable layout data ready for rendering or PDF generation.
    """
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    user_role = current_user.role.role_name if current_user.role else "Customer"
    if user_role == "Customer":
        user_cust_id = _get_customer_id_for_user(current_user, db)
        if inv.customer_id != user_cust_id:
            raise HTTPException(status_code=403, detail="Access denied")

    details = _compute_invoice_response(inv, db)
    return {
        "company": {
            "name": "Brightloop Software Inc.",
            "address": "100 Innovation Way, Tech Park",
            "support_email": "billing@brightloop.com",
        },
        "invoice": details,
    }

