-- ====================================================================
-- BRIGHTLOOP SOFTWARE - SUBSCRIPTION MANAGEMENT SYSTEM
-- COMPLETE CONSOLIDATED POSTGRESQL DATABASE SCHEMA
-- ====================================================================

-- STAGE 1: USERS AND CUSTOMER MANAGEMENT

CREATE TABLE IF NOT EXISTS roles (
    role_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR(30) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id BIGINT NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id)
        REFERENCES roles(role_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    billing_address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_users (
    customer_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    is_primary_contact BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (customer_id, user_id),

    CONSTRAINT fk_customer_users_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_customer_users_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_password_reset_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Default Roles Seed
INSERT INTO roles (role_name, description)
VALUES
    ('Admin', 'Full system access'),
    ('Staff', 'Limited operational access'),
    ('Customer', 'Access to personal subscriptions and invoices')
ON CONFLICT (role_name) DO NOTHING;


-- STAGE 2: PRODUCTS AND PLANS

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    product_type VARCHAR(50) NOT NULL,
    sales_price NUMERIC(12,2) NOT NULL CHECK (sales_price >= 0),
    cost_price NUMERIC(12,2) NOT NULL CHECK (cost_price >= 0),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_variants (
    variant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL,
    variant_name VARCHAR(100) NOT NULL,
    additional_price NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (additional_price >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_variant_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_product_variant
        UNIQUE (product_id, variant_name),

    CONSTRAINT unique_product_variant_reference
        UNIQUE (product_id, variant_id)
);

CREATE TABLE IF NOT EXISTS plans (
    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_name VARCHAR(150) NOT NULL,
    description TEXT,
    billing_interval VARCHAR(20) NOT NULL CHECK (
        billing_interval IN ('daily', 'weekly', 'monthly', 'yearly')
    ),
    interval_count INT NOT NULL DEFAULT 1 CHECK (interval_count > 0),
    minimum_quantity INT NOT NULL DEFAULT 1 CHECK (minimum_quantity > 0),
    available_from DATE NOT NULL,
    available_until DATE,
    auto_close BOOLEAN NOT NULL DEFAULT FALSE,
    allow_early_close BOOLEAN NOT NULL DEFAULT TRUE,
    allow_pause BOOLEAN NOT NULL DEFAULT TRUE,
    allow_renewal BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_plan_dates
        CHECK (available_until IS NULL OR available_until >= available_from)
);

CREATE TABLE IF NOT EXISTS plan_products (
    plan_product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    variant_id BIGINT,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_plan_product_plan
        FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_plan_product_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_plan_product_variant
        FOREIGN KEY (product_id, variant_id)
        REFERENCES product_variants(product_id, variant_id)
        ON DELETE RESTRICT
);


-- STAGE 3: TAXES AND DISCOUNTS

CREATE TABLE IF NOT EXISTS taxes (
    tax_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tax_name VARCHAR(100) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL CHECK (tax_rate >= 0 AND tax_rate <= 100),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discounts (
    discount_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    discount_name VARCHAR(150) NOT NULL,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('fixed', 'percentage')),
    discount_value NUMERIC(12,2) NOT NULL CHECK (discount_value > 0),
    applies_to VARCHAR(20) NOT NULL CHECK (applies_to IN ('product', 'subscription')),
    minimum_purchase NUMERIC(12,2) DEFAULT 0 CHECK (minimum_purchase >= 0),
    minimum_quantity INT DEFAULT 1 CHECK (minimum_quantity > 0),
    start_date DATE NOT NULL,
    end_date DATE,
    usage_limit INT CHECK (usage_limit IS NULL OR usage_limit > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_discount_creator
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_discount_dates
        CHECK (end_date IS NULL OR end_date >= start_date),

    CONSTRAINT valid_percentage_discount
        CHECK (discount_type <> 'percentage' OR discount_value <= 100)
);

CREATE TABLE IF NOT EXISTS discount_products (
    discount_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    PRIMARY KEY (discount_id, product_id),

    CONSTRAINT fk_discount_products_discount
        FOREIGN KEY (discount_id)
        REFERENCES discounts(discount_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_discount_products_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
);


-- STAGE 4: QUOTATIONS AND SUBSCRIPTIONS

CREATE TABLE IF NOT EXISTS quotation_templates (
    template_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    template_name VARCHAR(150) NOT NULL,
    plan_id BIGINT NOT NULL,
    validity_days INT NOT NULL DEFAULT 30 CHECK (validity_days > 0),
    created_by BIGINT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_template_plan
        FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_template_creator
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS quotation_template_lines (
    template_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    template_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    variant_id BIGINT,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),

    CONSTRAINT fk_template_line_template
        FOREIGN KEY (template_id)
        REFERENCES quotation_templates(template_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_template_line_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_template_line_variant
        FOREIGN KEY (product_id, variant_id)
        REFERENCES product_variants(product_id, variant_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL,
    plan_id BIGINT NOT NULL,
    template_id BIGINT,
    start_date DATE,
    expiry_date DATE,
    quotation_valid_until DATE,
    next_billing_date DATE,
    payment_terms VARCHAR(150),
    status VARCHAR(30) NOT NULL DEFAULT 'Draft' CHECK (
        status IN ('Draft', 'Quotation', 'Confirmed', 'Active', 'Paused', 'Closed')
    ),
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_subscription_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_subscription_plan
        FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_subscription_template
        FOREIGN KEY (template_id)
        REFERENCES quotation_templates(template_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_subscription_creator
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_subscription_dates
        CHECK (expiry_date IS NULL OR start_date IS NULL OR expiry_date >= start_date),

    CONSTRAINT valid_quotation_dates
        CHECK (quotation_valid_until IS NULL OR start_date IS NULL OR quotation_valid_until >= start_date)
);

CREATE TABLE IF NOT EXISTS subscription_lines (
    subscription_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    variant_id BIGINT,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    tax_id BIGINT,

    CONSTRAINT fk_subscription_line_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_subscription_line_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_subscription_line_variant
        FOREIGN KEY (product_id, variant_id)
        REFERENCES product_variants(product_id, variant_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_subscription_line_tax
        FOREIGN KEY (tax_id)
        REFERENCES taxes(tax_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS discount_usages (
    usage_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    discount_id BIGINT NOT NULL,
    subscription_id BIGINT NOT NULL,
    discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_discount_usage_discount
        FOREIGN KEY (discount_id)
        REFERENCES discounts(discount_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_discount_usage_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id)
        ON DELETE RESTRICT
);


-- STAGE 5: INVOICE MANAGEMENT

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    subscription_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    billing_period_start DATE,
    billing_period_end DATE,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    discount_total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    status VARCHAR(30) NOT NULL DEFAULT 'Draft' CHECK (
        status IN ('Draft', 'Confirmed', 'Partially Paid', 'Paid', 'Cancelled')
    ),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_invoice_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_invoice_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_invoice_dates
        CHECK (due_date >= issue_date),

    CONSTRAINT valid_billing_period
        CHECK (billing_period_end IS NULL OR billing_period_start IS NULL OR billing_period_end >= billing_period_start),

    CONSTRAINT valid_invoice_totals
        CHECK (total_amount = subtotal - discount_total + tax_total)
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    invoice_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    description TEXT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    tax_name VARCHAR(100),
    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (tax_rate >= 0 AND tax_rate <= 100),
    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    line_total NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),

    CONSTRAINT fk_invoice_line_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_invoice_line_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_line_discount
        CHECK (discount_amount <= subtotal),

    CONSTRAINT valid_line_total
        CHECK (line_total = subtotal - discount_amount + tax_amount)
);

CREATE TABLE IF NOT EXISTS invoice_discounts (
    invoice_discount_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id BIGINT NOT NULL,
    discount_id BIGINT NOT NULL,
    discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_invoice_discount_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_invoice_discount_rule
        FOREIGN KEY (discount_id)
        REFERENCES discounts(discount_id)
        ON DELETE RESTRICT
);


-- STAGE 6: PAYMENT MANAGEMENT

CREATE TABLE IF NOT EXISTS payments (
    payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_method VARCHAR(50) NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    payment_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reference_number VARCHAR(150),
    note TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Completed' CHECK (
        status IN ('Pending', 'Completed', 'Failed', 'Refunded')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id BIGINT NOT NULL,
    invoice_id BIGINT NOT NULL,
    allocated_amount NUMERIC(12,2) NOT NULL CHECK (allocated_amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_allocation_payment
        FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_allocation_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
        ON DELETE RESTRICT,

    CONSTRAINT unique_payment_invoice
        UNIQUE (payment_id, invoice_id)
);


-- STAGE 7: RECURRING BILLING

CREATE TABLE IF NOT EXISTS billing_records (
    billing_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subscription_id BIGINT NOT NULL,
    invoice_id BIGINT UNIQUE,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    scheduled_date DATE NOT NULL,
    billing_status VARCHAR(30) NOT NULL DEFAULT 'Pending' CHECK (
        billing_status IN ('Pending', 'Processing', 'Completed', 'Failed')
    ),
    attempt_count INT NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_billing_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_billing_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
        ON DELETE RESTRICT,

    CONSTRAINT valid_billing_dates
        CHECK (billing_period_end >= billing_period_start),

    CONSTRAINT unique_subscription_billing_period
        UNIQUE (subscription_id, billing_period_start, billing_period_end)
);
