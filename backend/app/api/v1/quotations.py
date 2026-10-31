from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_staff_or_admin
from app.models.product import Plan, Product, ProductVariant
from app.models.subscription import QuotationTemplate, QuotationTemplateLine
from app.models.user import User
from app.schemas.quotation import (
    QuotationTemplateCreate,
    QuotationTemplateUpdate,
    QuotationTemplateResponse,
    QuotationTemplateLineCreate,
    QuotationTemplateLineResponse,
)

router = APIRouter(prefix="/quotation-templates", tags=["Quotation Templates"])


@router.get("", response_model=List[QuotationTemplateResponse])
def list_quotation_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: List all available quotation templates.
    """
    query = db.query(QuotationTemplate)
    if active_only:
        query = query.filter(QuotationTemplate.is_active == True)

    return query.offset(skip).limit(limit).all()


@router.get("/{template_id}", response_model=QuotationTemplateResponse)
def get_quotation_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Get details of a quotation template.
    """
    template = db.query(QuotationTemplate).filter(QuotationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation template with ID {template_id} not found",
        )
    return template


@router.post("", response_model=QuotationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_template(
    template_in: QuotationTemplateCreate,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Create a new quotation template with predefined plan and product lines.
    """
    plan = db.query(Plan).filter(Plan.plan_id == template_in.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with ID {template_in.plan_id} does not exist",
        )

    template = QuotationTemplate(
        template_name=template_in.template_name,
        plan_id=template_in.plan_id,
        validity_days=template_in.validity_days,
        created_by=current_staff.user_id,
        is_active=template_in.is_active,
    )
    db.add(template)
    db.flush()

    # Prepopulate lines from template_in or directly from plan's default products if lines are empty
    lines_to_add = template_in.lines
    if not lines_to_add and plan.plan_products:
        for pp in plan.plan_products:
            line = QuotationTemplateLine(
                template_id=template.template_id,
                product_id=pp.product_id,
                variant_id=pp.variant_id,
                quantity=pp.quantity,
                unit_price=pp.unit_price,
            )
            db.add(line)
    else:
        for l_in in lines_to_add:
            product = db.query(Product).filter(Product.product_id == l_in.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {l_in.product_id} not found",
                )
            if l_in.variant_id:
                variant = (
                    db.query(ProductVariant)
                    .filter(
                        ProductVariant.variant_id == l_in.variant_id,
                        ProductVariant.product_id == l_in.product_id,
                    )
                    .first()
                )
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant ID {l_in.variant_id} does not belong to product {l_in.product_id}",
                    )
            line = QuotationTemplateLine(
                template_id=template.template_id,
                product_id=l_in.product_id,
                variant_id=l_in.variant_id,
                quantity=l_in.quantity,
                unit_price=l_in.unit_price,
            )
            db.add(line)

    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=QuotationTemplateResponse)
def update_quotation_template(
    template_id: int,
    template_update: QuotationTemplateUpdate,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Update quotation template settings.
    """
    template = db.query(QuotationTemplate).filter(QuotationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation template with ID {template_id} not found",
        )

    update_data = template_update.model_dump(exclude_unset=True)
    if "plan_id" in update_data:
        plan = db.query(Plan).filter(Plan.plan_id == update_data["plan_id"]).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with ID {update_data['plan_id']} does not exist",
            )

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}")
def delete_quotation_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Soft-deactivate a quotation template.
    """
    template = db.query(QuotationTemplate).filter(QuotationTemplate.template_id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation template with ID {template_id} not found",
        )

    template.is_active = False
    db.commit()
    return {"message": f"Template '{template.template_name}' has been deactivated"}

