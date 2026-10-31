import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_staff_or_admin
from app.models.product import Plan, Product, ProductVariant
from app.models.subscription import QuotationTemplate, Subscription, SubscriptionLine
from app.models.tax_discount import Tax
from app.models.user import Customer, CustomerUser, User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionLineCreate,
    SubscriptionLineResponse,
    SubscriptionStatusTransition,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def _calculate_next_billing_date(start: date, interval: str, count: int) -> date:
    count = max(1, count)
    if interval == "daily":
        return start + timedelta(days=count)
    elif interval == "weekly":
        return start + timedelta(weeks=count)
    elif interval == "monthly":
        # Add count months
        year = start.year + (start.month + count - 1) // 12
        month = (start.month + count - 1) % 12 + 1
        day = min(start.day, 28)  # conservative safe day
        return date(year, month, day)
    elif interval == "yearly":
        return date(start.year + count, start.month, min(start.day, 28))
    return start + timedelta(days=30)


def _compute_subscription_response(sub: Subscription) -> SubscriptionResponse:
    subtotal = Decimal("0.00")
    total_tax = Decimal("0.00")
    line_responses = []

    for line in sub.lines:
        line_sub = Decimal(str(line.unit_price)) * Decimal(str(line.quantity))
        subtotal += line_sub

        line_tax = Decimal("0.00")
        if line.tax:
            tax_rate = Decimal(str(line.tax.tax_rate))
            line_tax = line_sub * (tax_rate / Decimal("100.00"))
            total_tax += line_tax

        line_resp = SubscriptionLineResponse.model_validate(line)
        line_resp.line_total = line_sub + line_tax
        line_responses.append(line_resp)

    resp = SubscriptionResponse.model_validate(sub)
    resp.lines = line_responses
    resp.subtotal = subtotal
    resp.total_amount = subtotal + total_tax
    return resp


def _get_customer_id_for_user(user: User, db: Session) -> Optional[int]:
    cust_user = db.query(CustomerUser).filter(CustomerUser.user_id == user.user_id).first()
    return cust_user.customer_id if cust_user else None


@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List subscriptions.
    - Customers: view only their own subscriptions.
    - Staff & Admins: view all subscriptions, with optional filtering by status and customer.
    """
    query = db.query(Subscription)

    user_role = current_user.role.role_name if current_user.role else "Customer"
    if user_role == "Customer":
        user_cust_id = _get_customer_id_for_user(current_user, db)
        if not user_cust_id:
            return []
        query = query.filter(Subscription.customer_id == user_cust_id)
    else:
        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)

    if status_filter:
        query = query.filter(Subscription.status == status_filter)

    subscriptions = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
    return [_compute_subscription_response(s) for s in subscriptions]


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single subscription details, line items, plan policies, and calculated totals.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    # RBAC check: Customer cannot access other customers' subscriptions
    user_role = current_user.role.role_name if current_user.role else "Customer"
    if user_role == "Customer":
        user_cust_id = _get_customer_id_for_user(current_user, db)
        if sub.customer_id != user_cust_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this subscription",
            )

    return _compute_subscription_response(sub)


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    sub_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Create a new subscription or quote.
    - Can instantiate from a quotation template (`template_id`), auto-loading plan and product lines.
    - Generates unique subscription number if omitted.
    - Default initial state: 'Draft'.
    """
    # Validate Customer exists
    customer = db.query(Customer).filter(Customer.customer_id == sub_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with ID {sub_in.customer_id} not found",
        )

    plan_id = sub_in.plan_id
    quotation_valid_until = sub_in.quotation_valid_until

    # If starting from a quotation template
    template = None
    if sub_in.template_id:
        template = db.query(QuotationTemplate).filter(QuotationTemplate.template_id == sub_in.template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quotation template with ID {sub_in.template_id} not found",
            )
        if not plan_id:
            plan_id = template.plan_id
        if not quotation_valid_until and template.validity_days:
            quotation_valid_until = date.today() + timedelta(days=template.validity_days)

    if not plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="plan_id must be provided or derived from a template_id",
        )

    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with ID {plan_id} not found",
        )

    # Unique subscription number
    sub_num = sub_in.subscription_number
    if not sub_num:
        sub_num = f"SUB-{date.today().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    subscription = Subscription(
        subscription_number=sub_num,
        customer_id=sub_in.customer_id,
        plan_id=plan_id,
        template_id=sub_in.template_id,
        start_date=sub_in.start_date,
        expiry_date=sub_in.expiry_date,
        quotation_valid_until=quotation_valid_until,
        payment_terms=sub_in.payment_terms or "Immediate",
        status="Draft",
        created_by=current_staff.user_id,
    )
    db.add(subscription)
    db.flush()

    # Prepopulate lines from template if no custom lines passed
    if sub_in.lines:
        for line_in in sub_in.lines:
            sub_line = SubscriptionLine(
                subscription_id=subscription.subscription_id,
                product_id=line_in.product_id,
                variant_id=line_in.variant_id,
                quantity=line_in.quantity,
                unit_price=line_in.unit_price,
                tax_id=line_in.tax_id,
            )
            db.add(sub_line)
    elif template and template.lines:
        for t_line in template.lines:
            sub_line = SubscriptionLine(
                subscription_id=subscription.subscription_id,
                product_id=t_line.product_id,
                variant_id=t_line.variant_id,
                quantity=t_line.quantity,
                unit_price=t_line.unit_price,
            )
            db.add(sub_line)
    elif plan.plan_products:
        for pp in plan.plan_products:
            sub_line = SubscriptionLine(
                subscription_id=subscription.subscription_id,
                product_id=pp.product_id,
                variant_id=pp.variant_id,
                quantity=pp.quantity,
                unit_price=pp.unit_price,
            )
            db.add(sub_line)

    db.commit()
    db.refresh(subscription)
    return _compute_subscription_response(subscription)


# ----------------- Lifecycle Actions -----------------

@router.post("/{subscription_id}/action/send-quote", response_model=SubscriptionResponse)
def send_quotation(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Moves status Draft -> Quotation. Sets quotation_valid_until date if unset.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status != "Draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition to Quotation from status '{sub.status}'. Must be in 'Draft'.",
        )

    sub.status = "Quotation"
    if not sub.quotation_valid_until:
        validity = 30
        if sub.template and sub.template.validity_days:
            validity = sub.template.validity_days
        sub.quotation_valid_until = date.today() + timedelta(days=validity)

    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/confirm", response_model=SubscriptionResponse)
def confirm_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Moves status Quotation / Draft -> Confirmed.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status not in ["Draft", "Quotation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm subscription from status '{sub.status}'.",
        )

    sub.status = "Confirmed"
    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Moves status Confirmed -> Active.
    Initializes start_date (if unset) and calculates initial next_billing_date based on plan cadence.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status not in ["Confirmed", "Draft", "Quotation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate subscription from status '{sub.status}'.",
        )

    today = date.today()
    sub.status = "Active"
    if not sub.start_date:
        sub.start_date = today

    # Calculate next billing date
    plan = sub.plan
    sub.next_billing_date = _calculate_next_billing_date(
        sub.start_date, plan.billing_interval, plan.interval_count
    )

    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Moves status Active -> Paused.
    Validates plan rule: 'allow_pause'.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status != "Active":
        raise HTTPException(status_code=400, detail="Only Active subscriptions can be paused.")

    if not sub.plan.allow_pause:
        raise HTTPException(
            status_code=400,
            detail=f"Plan '{sub.plan.plan_name}' does not permit pausing subscriptions.",
        )

    sub.status = "Paused"
    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Moves status Paused -> Active.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status != "Paused":
        raise HTTPException(status_code=400, detail="Only Paused subscriptions can be resumed.")

    sub.status = "Active"
    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/close", response_model=SubscriptionResponse)
def close_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Moves status Active/Paused -> Closed.
    Validates plan rule: 'allow_early_close' if closing prior to expiry.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status in ["Closed", "Draft"]:
        raise HTTPException(status_code=400, detail=f"Cannot close subscription in '{sub.status}' state.")

    # Check early closure policy
    today = date.today()
    if sub.expiry_date and sub.expiry_date > today and not sub.plan.allow_early_close:
        raise HTTPException(
            status_code=400,
            detail=f"Plan '{sub.plan.plan_name}' does not allow early closure before expiry date.",
        )

    sub.status = "Closed"
    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)


@router.post("/{subscription_id}/action/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: int,
    months_to_extend: int = Query(12, ge=1, le=120),
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Renews subscription:
    - Validates plan rule: 'allow_renewal'
    - Extends expiry_date and restores Active status if previously Closed/Expired.
    """
    sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if not sub.plan.allow_renewal:
        raise HTTPException(
            status_code=400,
            detail=f"Plan '{sub.plan.plan_name}' does not permit renewal.",
        )

    base_date = sub.expiry_date or date.today()
    if base_date < date.today():
        base_date = date.today()

    new_year = base_date.year + (base_date.month + months_to_extend - 1) // 12
    new_month = (base_date.month + months_to_extend - 1) % 12 + 1
    new_expiry = date(new_year, new_month, min(base_date.day, 28))

    sub.expiry_date = new_expiry
    sub.status = "Active"
    db.commit()
    db.refresh(sub)
    return _compute_subscription_response(sub)
