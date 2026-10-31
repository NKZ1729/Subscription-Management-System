from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_staff_or_admin
from app.models.billing import BillingRecord
from app.models.user import User
from app.schemas.billing import (
    BillingRecordResponse,
    BillingRunRequest,
    BillingRunResponse,
)
from app.services.billing_service import run_billing_day

router = APIRouter(prefix="/billing", tags=["Recurring Billing Engine"])


@router.post("/run", response_model=BillingRunResponse)
def trigger_billing_run(
    request: Optional[BillingRunRequest] = None,
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Trigger the automated Recurring Billing run ("Billing Day").
    Processes all active subscriptions with next_billing_date <= run_date.
    Prevents double billing via idempotency checks in billing_records.
    """
    run_date = request.run_date if request else date.today()
    dry_run = request.dry_run if request else False

    subs_proc, invs_gen, tot_billed, errs, records = run_billing_day(
        db=db,
        run_date=run_date,
        dry_run=dry_run,
    )

    return BillingRunResponse(
        run_date=run_date or date.today(),
        subscriptions_processed=subs_proc,
        invoices_generated=invs_gen,
        total_billed_amount=f"{tot_billed:.2f}",
        errors_count=errs,
        details=[BillingRecordResponse.model_validate(r) for r in records],
    )


@router.get("/records", response_model=List[BillingRecordResponse])
def list_billing_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    subscription_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_staff: User = Depends(require_staff_or_admin),
):
    """
    Staff & Admin: Audit trail of all recurring billing cycles executed.
    """
    query = db.query(BillingRecord)
    if subscription_id:
        query = query.filter(BillingRecord.subscription_id == subscription_id)
    if status_filter:
        query = query.filter(BillingRecord.billing_status == status_filter)

    return query.order_by(BillingRecord.scheduled_date.desc()).offset(skip).limit(limit).all()
