from datetime import date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_admin
from app.models.product import Plan, PlanProduct, Product, ProductVariant
from app.models.user import User
from app.schemas.plan import (
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanProductCreate,
    PlanProductResponse,
)

router = APIRouter(prefix="/plans", tags=["Plans"])


def _compute_plan_response(plan: Plan) -> PlanResponse:
    total_cost = Decimal("0.00")
    for pp in plan.plan_products:
        total_cost += Decimal(str(pp.unit_price)) * Decimal(str(pp.quantity))
    
    response = PlanResponse.model_validate(plan)
    response.total_cost = total_cost
    return response


@router.get("", response_model=List[PlanResponse])
def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(True),
    currently_available: bool = Query(False),
    billing_interval: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all subscription plans.
    Supports filtering by active status, currently available dates, and billing cadence.
    """
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.is_active == True)
    if currently_available:
        today = date.today()
        query = query.filter(
            Plan.available_from <= today,
            (Plan.available_until == None) | (Plan.available_until >= today),
        )
    if billing_interval:
        query = query.filter(Plan.billing_interval == billing_interval)

    plans = query.offset(skip).limit(limit).all()
    return [_compute_plan_response(p) for p in plans]


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single plan details, included products, variants, and total plan cost.
    """
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )
    return _compute_plan_response(plan)


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_in: PlanCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Create a new subscription plan with lifecycle policies and bundled products.
    """
    new_plan = Plan(
        plan_name=plan_in.plan_name,
        description=plan_in.description,
        billing_interval=plan_in.billing_interval,
        interval_count=plan_in.interval_count,
        minimum_quantity=plan_in.minimum_quantity,
        available_from=plan_in.available_from,
        available_until=plan_in.available_until,
        auto_close=plan_in.auto_close,
        allow_early_close=plan_in.allow_early_close,
        allow_pause=plan_in.allow_pause,
        allow_renewal=plan_in.allow_renewal,
        is_active=plan_in.is_active,
    )
    db.add(new_plan)
    db.flush()

    if plan_in.products:
        for p_in in plan_in.products:
            # Validate product exists
            product = db.query(Product).filter(Product.product_id == p_in.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {p_in.product_id} does not exist",
                )
            
            # Validate variant if specified
            if p_in.variant_id:
                variant = (
                    db.query(ProductVariant)
                    .filter(
                        ProductVariant.variant_id == p_in.variant_id,
                        ProductVariant.product_id == p_in.product_id,
                    )
                    .first()
                )
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant ID {p_in.variant_id} does not belong to product ID {p_in.product_id}",
                    )

            plan_prod = PlanProduct(
                plan_id=new_plan.plan_id,
                product_id=p_in.product_id,
                variant_id=p_in.variant_id,
                quantity=p_in.quantity,
                unit_price=p_in.unit_price,
            )
            db.add(plan_prod)

    db.commit()
    db.refresh(new_plan)
    return _compute_plan_response(new_plan)


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan_update: PlanUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Update plan details and lifecycle rules.
    """
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )

    update_data = plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    # Validate updated dates
    if plan.available_until and plan.available_until < plan.available_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="available_until cannot be earlier than available_from",
        )

    db.commit()
    db.refresh(plan)
    return _compute_plan_response(plan)


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Soft-deactivate a plan.
    """
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )

    plan.is_active = False
    db.commit()
    return {"message": f"Plan '{plan.plan_name}' has been deactivated"}


@router.post("/{plan_id}/products", response_model=PlanProductResponse, status_code=status.HTTP_201_CREATED)
def add_product_to_plan(
    plan_id: int,
    product_in: PlanProductCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Add a product/variant line to an existing plan.
    """
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found",
        )

    product = db.query(Product).filter(Product.product_id == product_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID {product_in.product_id} not found",
        )

    if product_in.variant_id:
        variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.variant_id == product_in.variant_id,
                ProductVariant.product_id == product_in.product_id,
            )
            .first()
        )
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variant ID {product_in.variant_id} does not belong to product {product_in.product_id}",
            )

    plan_prod = PlanProduct(
        plan_id=plan_id,
        product_id=product_in.product_id,
        variant_id=product_in.variant_id,
        quantity=product_in.quantity,
        unit_price=product_in.unit_price,
    )
    db.add(plan_prod)
    db.commit()
    db.refresh(plan_prod)
    return plan_prod


@router.delete("/{plan_id}/products/{plan_product_id}")
def remove_product_from_plan(
    plan_id: int,
    plan_product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Remove a product line from a plan.
    """
    plan_prod = (
        db.query(PlanProduct)
        .filter(
            PlanProduct.plan_product_id == plan_product_id,
            PlanProduct.plan_id == plan_id,
        )
        .first()
    )
    if not plan_prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan product item not found",
        )

    db.delete(plan_prod)
    db.commit()
    return {"message": "Product removed from plan"}

