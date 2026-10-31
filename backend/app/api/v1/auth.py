import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_admin
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.models.user import Role, User, Customer, CustomerUser, PasswordResetToken
from app.schemas.auth import (
    Token,
    LoginRequest,
    CustomerRegisterRequest,
    StaffCreateRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT bearer token.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive. Please contact support.",
        )

    role_name = user.role.role_name if user.role else "Customer"
    access_token = create_access_token(
        subject=user.user_id,
        extra_claims={"role": role_name, "email": user.email},
    )

    return Token(
        access_token=access_token,
        role=role_name,
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
    )


@router.post("/register-customer", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_customer(request: CustomerRegisterRequest, db: Session = Depends(get_db)):
    """
    Customer self-registration:
    - Enforces unique email
    - Enforces strong password (>8 chars, upper, lower, special char)
    - Automatically provisions Customer record & assigns 'Customer' role
    """
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    customer_role = db.query(Role).filter(Role.role_name == "Customer").first()
    if not customer_role:
        # Fallback if roles not yet seeded
        customer_role = Role(role_name="Customer", description="Access to personal subscriptions and invoices")
        db.add(customer_role)
        db.flush()

    # 1. Create User
    new_user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        role_id=customer_role.role_id,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # 2. Create Customer
    new_customer = Customer(
        company_name=request.company_name,
        contact_email=request.email,
        phone=request.phone,
        billing_address=request.billing_address,
        is_active=True,
    )
    db.add(new_customer)
    db.flush()

    # 3. Associate Customer with User
    cust_user = CustomerUser(
        customer_id=new_customer.customer_id,
        user_id=new_user.user_id,
        is_primary_contact=True,
    )
    db.add(cust_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        subject=new_user.user_id,
        extra_claims={"role": "Customer", "email": new_user.email},
    )

    return Token(
        access_token=access_token,
        role="Customer",
        user_id=new_user.user_id,
        full_name=new_user.full_name,
        email=new_user.email,
    )


@router.post("/create-staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    request: StaffCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Admin-only: Provision a new internal staff member.
    """
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    role = db.query(Role).filter(Role.role_id == request.role_id).first()
    if not role or role.role_name not in ["Admin", "Staff"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role specified. Must be Staff or Admin.",
        )

    new_staff = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        role_id=role.role_id,
        is_active=True,
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff


@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset flow: generates a secure reset token sent to registered email.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Prevent email enumeration by returning a generic success message
        return {"message": "If the account exists, a reset link has been dispatched to your email."}

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_record = PasswordResetToken(
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_record)
    db.commit()

    # For hackathon/demo verification, we also return the token in response
    return {
        "message": "If the account exists, a reset link has been dispatched to your email.",
        "reset_token": raw_token,
    }


@router.post("/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Verify reset token and update password.
    """
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    reset_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    now = datetime.now(timezone.utc)
    if not reset_record or reset_record.used_at is not None or reset_record.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = db.query(User).filter(User.user_id == reset_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user not found.",
        )

    user.password_hash = get_password_hash(request.new_password)
    reset_record.used_at = now
    db.commit()

    return {"message": "Password has been successfully updated. You may now log in."}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile information of currently logged in user.
    """
    return current_user
