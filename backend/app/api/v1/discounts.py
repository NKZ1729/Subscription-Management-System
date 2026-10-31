from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_admin
from app.models.product import Product
from app.models.tax_discount import Discount, DiscountUsage, Tax
from app.models.user import User
from app.schemas.discount import (
    TaxCreate,
    TaxUpdate,
    TaxResponse,
    DiscountCreate,
    DiscountUpdate,
    DiscountResponse,
)

router = APIRouter(prefix="", tags=["Taxes & Discounts"])


# ----------------- Taxes -----------------

@router.get("/taxes", response_model=List[TaxResponse])
def list_taxes(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all configured tax rates.
    """
    query = db.query(Tax)
    if active_only:
        query = query.filter(Tax.is_active == True)
    return query.all()


@router.post("/taxes", response_model=TaxResponse, status_code=status.HTTP_201_CREATED)
def create_tax(
    tax_in: TaxCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Create a new tax rate rule (e.g. GST 18%, VAT 5%).
    """
    tax = Tax(
        tax_name=tax_in.tax_name,
        tax_rate=tax_in.tax_rate,
        description=tax_in.description,
        is_active=tax_in.is_active,
    )
    db.add(tax)
    db.commit()
    db.refresh(tax)
    return tax


@router.put("/taxes/{tax_id}", response_model=TaxResponse)
def update_tax(
    tax_id: int,
    tax_update: TaxUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Update an existing tax rule.
    """
    tax = db.query(Tax).filter(Tax.tax_id == tax_id).first()
    if not tax:
        raise HTTPException(status_code=404, detail="Tax rule not found")

    update_data = tax_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tax, field, value)

    db.commit()
    db.refresh(tax)
    return tax


# ----------------- Discounts -----------------

def _format_discount_response(discount: Discount, db: Session) -> DiscountResponse:
    applied_count = (
        db.query(func.count(DiscountUsage.usage_id))
        .filter(DiscountUsage.discount_id == discount.discount_id)
        .scalar()
        or 0
    )
    product_ids = [p.product_id for p in discount.applicable_products]

    resp = DiscountResponse.model_validate(discount)
    resp.applied_count = applied_count
    resp.product_ids = product_ids
    return resp


@router.get("/discounts", response_model=List[DiscountResponse])
def list_discounts(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all discount rules with their current usage statistics.
    """
    query = db.query(Discount)
    if active_only:
        query = query.filter(Discount.is_active == True)

    discounts = query.all()
    return [_format_discount_response(d, db) for d in discounts]


@router.get("/discounts/{discount_id}", response_model=DiscountResponse)
def get_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details of a specific discount rule.
    """
    discount = db.query(Discount).filter(Discount.discount_id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount rule not found")
    return _format_discount_response(discount, db)


@router.post("/discounts", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(
    disc_in: DiscountCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Create a discount rule (fixed amount or percentage, min spend, seat quantity, validity, usage limit).
    """
    if disc_in.discount_type == "percentage" and disc_in.discount_value > 100:
        raise HTTPException(status_code=400, detail="Percentage discount cannot exceed 100%")

    if disc_in.end_date and disc_in.end_date < disc_in.start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be earlier than start_date")

    discount = Discount(
        discount_name=disc_in.discount_name,
        discount_type=disc_in.discount_type,
        discount_value=disc_in.discount_value,
        applies_to=disc_in.applies_to,
        minimum_purchase=disc_in.minimum_purchase,
        minimum_quantity=disc_in.minimum_quantity,
        start_date=disc_in.start_date,
        end_date=disc_in.end_date,
        usage_limit=disc_in.usage_limit,
        is_active=disc_in.is_active,
        created_by=current_admin.user_id,
    )
    db.add(discount)
    db.flush()

    if disc_in.applies_to == "product" and disc_in.product_ids:
        products = db.query(Product).filter(Product.product_id.in_(disc_in.product_ids)).all()
        discount.applicable_products = products

    db.commit()
    db.refresh(discount)
    return _format_discount_response(discount, db)


@router.put("/discounts/{discount_id}", response_model=DiscountResponse)
def update_discount(
    discount_id: int,
    disc_update: DiscountUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Update an existing discount rule.
    """
    discount = db.query(Discount).filter(Discount.discount_id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount rule not found")

    update_data = disc_update.model_dump(exclude_unset=True)
    product_ids = update_data.pop("product_ids", None)

    for field, value in update_data.items():
        setattr(discount, field, value)

    if product_ids is not None:
        products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()
        discount.applicable_products = products

    db.commit()
    db.refresh(discount)
    return _format_discount_response(discount, db)


@router.delete("/discounts/{discount_id}")
def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Soft-deactivate a discount rule.
    """
    discount = db.query(Discount).filter(Discount.discount_id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount rule not found")

    discount.is_active = False
    db.commit()
    return {"message": f"Discount rule '{discount.discount_name}' has been deactivated"}

