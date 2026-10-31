from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_admin
from app.models.product import Product, ProductVariant
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    VariantCreate,
    VariantUpdate,
    VariantResponse,
)

router = APIRouter(prefix="/products", tags=["Products & Variants"])


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all products with variants. Accessible to all authenticated users.
    Supports search query and product_type filtering.
    """
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if product_type:
        query = query.filter(Product.product_type == product_type)

    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single product by ID with its variants.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Create a new product. Can optionally include product variants (e.g., Odoo brand variant).
    """
    new_product = Product(
        name=product_in.name,
        product_type=product_in.product_type,
        sales_price=product_in.sales_price,
        cost_price=product_in.cost_price,
        notes=product_in.notes,
        is_active=product_in.is_active,
    )
    db.add(new_product)
    db.flush()

    # Create nested variants if provided
    if product_in.variants:
        for var_in in product_in.variants:
            variant = ProductVariant(
                product_id=new_product.product_id,
                variant_name=var_in.variant_name,
                additional_price=var_in.additional_price,
                is_active=var_in.is_active,
            )
            db.add(variant)

    db.commit()
    db.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Update product details.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Soft-deactivate a product.
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    product.is_active = False
    db.commit()
    return {"message": f"Product '{product.name}' has been deactivated"}


# ----------------- Variant Endpoints -----------------

@router.post("/{product_id}/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def add_product_variant(
    product_id: int,
    variant_in: VariantCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Add a new variant to an existing product (e.g. Brand: Odoo +560).
    """
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    existing_var = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.variant_name == variant_in.variant_name,
        )
        .first()
    )
    if existing_var:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Variant '{variant_in.variant_name}' already exists for this product",
        )

    variant = ProductVariant(
        product_id=product_id,
        variant_name=variant_in.variant_name,
        additional_price=variant_in.additional_price,
        is_active=variant_in.is_active,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.put("/{product_id}/variants/{variant_id}", response_model=VariantResponse)
def update_product_variant(
    product_id: int,
    variant_id: int,
    variant_update: VariantUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Update an existing product variant.
    """
    variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.variant_id == variant_id,
            ProductVariant.product_id == product_id,
        )
        .first()
    )
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found for the given product",
        )

    update_data = variant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)

    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/{product_id}/variants/{variant_id}")
def delete_product_variant(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin only: Soft-deactivate a product variant.
    """
    variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.variant_id == variant_id,
            ProductVariant.product_id == product_id,
        )
        .first()
    )
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found for the given product",
        )

    variant.is_active = False
    db.commit()
    return {"message": f"Variant '{variant.variant_name}' has been deactivated"}
