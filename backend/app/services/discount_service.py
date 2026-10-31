from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.subscription import Subscription, SubscriptionLine
from app.models.tax_discount import Discount, DiscountUsage


def evaluate_eligible_discounts(
    subscription: Subscription,
    subtotal: Decimal,
    total_quantity: int,
    db: Session,
    eval_date: Optional[date] = None,
) -> List[Tuple[Discount, Decimal]]:
    """
    Evaluates all active discount rules against the subscription and returns
    a list of (Discount, discount_amount) pairs that qualify.
    """
    today = eval_date or date.today()

    active_discounts = (
        db.query(Discount)
        .filter(
            Discount.is_active == True,
            Discount.start_date <= today,
            (Discount.end_date == None) | (Discount.end_date >= today),
        )
        .all()
    )

    eligible: List[Tuple[Discount, Decimal]] = []

    # Map product IDs present in subscription
    product_lines: Dict[int, SubscriptionLine] = {}
    for line in subscription.lines:
        product_lines[line.product_id] = line

    for discount in active_discounts:
        # Check usage limit
        if discount.usage_limit is not None:
            usage_count = (
                db.query(func.count(DiscountUsage.usage_id))
                .filter(DiscountUsage.discount_id == discount.discount_id)
                .scalar()
                or 0
            )
            if usage_count >= discount.usage_limit:
                continue  # Usage limit exhausted

        # Subscription-wide discount
        if discount.applies_to == "subscription":
            if subtotal < Decimal(str(discount.minimum_purchase)):
                continue
            if total_quantity < discount.minimum_quantity:
                continue

            if discount.discount_type == "percentage":
                discount_amount = subtotal * (Decimal(str(discount.discount_value)) / Decimal("100.00"))
            else:
                discount_amount = min(Decimal(str(discount.discount_value)), subtotal)

            if discount_amount > Decimal("0.00"):
                eligible.append((discount, discount_amount))

        # Product-specific discount
        elif discount.applies_to == "product":
            applicable_prod_ids = [p.product_id for p in discount.applicable_products]
            matching_subtotal = Decimal("0.00")
            matching_qty = 0

            for pid in applicable_prod_ids:
                if pid in product_lines:
                    line = product_lines[pid]
                    matching_subtotal += Decimal(str(line.unit_price)) * Decimal(str(line.quantity))
                    matching_qty += line.quantity

            if matching_qty < discount.minimum_quantity:
                continue
            if matching_subtotal < Decimal(str(discount.minimum_purchase)):
                continue

            if discount.discount_type == "percentage":
                discount_amount = matching_subtotal * (Decimal(str(discount.discount_value)) / Decimal("100.00"))
            else:
                discount_amount = min(Decimal(str(discount.discount_value)), matching_subtotal)

            if discount_amount > Decimal("0.00"):
                eligible.append((discount, discount_amount))

    return eligible
