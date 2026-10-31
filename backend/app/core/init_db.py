from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import Role, User
# Import all models to ensure metadata is populated
import app.models  # noqa: F401


def init_db(db: Session) -> None:
    # 1. Create tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # 2. Seed Default Roles
    roles = [
        ("Admin", "Full system access"),
        ("Staff", "Limited operational access"),
        ("Customer", "Access to personal subscriptions and invoices"),
    ]

    role_map = {}
    for role_name, description in roles:
        role = db.query(Role).filter(Role.role_name == role_name).first()
        if not role:
            role = Role(role_name=role_name, description=description)
            db.add(role)
            db.flush()
        role_map[role_name] = role

    # 3. Seed Default Superuser / Admin
    admin_user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
    if not admin_user:
        admin_role = role_map.get("Admin")
        admin_user = User(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name=settings.FIRST_SUPERUSER_NAME,
            role_id=admin_role.role_id,
            is_active=True,
        )
        db.add(admin_user)

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized and seeded successfully.")
    finally:
        db.close()
