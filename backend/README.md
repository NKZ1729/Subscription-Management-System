# Brightloop Subscription Management System - Backend API

Unified backend platform running the full lifecycle of a subscription business, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

---

## Features Implemented in Scaffold

- **Architecture**: Modular FastAPI structure (`app/core`, `app/models`, `app/schemas`, `app/api/v1`).
- **Database Schema**: Full SQLAlchemy models matching all SQL stages:
  - Users, Roles, Customers, CustomerUsers, PasswordResetTokens
  - Products, Variants, Plans, PlanProducts
  - Quotation Templates, Subscriptions, Subscription Lines
  - Taxes, Discounts, Usages
  - Invoices, Invoice Lines, Invoice Discounts
  - Payments, Allocations
  - Recurring Billing Records
- **Authentication & RBAC**:
  - JWT Bearer Authentication (`/api/v1/auth/login`).
  - Customer Self-Registration (`/api/v1/auth/register-customer`) with strict password validation:
    - Minimum length > 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 special character
  - Admin-only Staff Provisioning (`/api/v1/auth/create-staff`).
  - Password Reset Request & Confirmation (`/api/v1/auth/forgot-password` and `/api/v1/auth/reset-password`).
  - Role-based dependencies (`require_admin`, `require_staff_or_admin`, `require_customer`).
- **Interactive Documentation**: Auto-generated OpenAPI docs at `/docs` (Swagger UI) and `/redoc`.

---

## Setup & Running Locally

### 1. Create and Activate Virtual Environment

```bash
cd Subscription-Management-System/backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Activate (Linux / macOS)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure your database connection string:

```bash
cp .env.example .env
```

Default PostgreSQL URL:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/subscription_management
```

*(For quick local development without a running PostgreSQL instance, SQLite can also be used: `DATABASE_URL=sqlite:///./subscription.db`)*

### 4. Initialize Database & Seed Superuser

```bash
python -m app.core.init_db
```

Default Admin Credentials seeded:
- **Email**: `admin@brightloop.com`
- **Password**: `AdminPassword@123`

### 5. Run API Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

