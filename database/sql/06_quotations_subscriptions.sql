
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 3: QUOTATIONS AND SUBSCRIPTIONS
-- ==========================================

-- 1. QUOTATION TEMPLATES
CREATE TABLE quotation_templates (

    template_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    template_name VARCHAR(150) NOT NULL,

    plan_id BIGINT NOT NULL,

    validity_days INT NOT NULL DEFAULT 30
        CHECK (validity_days > 0),

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


-- 2. QUOTATION TEMPLATE LINES
CREATE TABLE quotation_template_lines (

    template_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    template_id BIGINT NOT NULL,

    product_id BIGINT NOT NULL,

    variant_id BIGINT,

    quantity INT NOT NULL DEFAULT 1
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0),

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



-- 3. SUBSCRIPTIONS
CREATE TABLE subscriptions (

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

    status VARCHAR(30) NOT NULL DEFAULT 'Draft'
        CHECK (
            status IN (
                'Draft',
                'Quotation',
                'Confirmed',
                'Active',
                'Paused',
                'Closed'
            )
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
        CHECK (
            expiry_date IS NULL
            OR start_date IS NULL
            OR expiry_date >= start_date
        ),

    CONSTRAINT valid_quotation_dates
        CHECK (
            quotation_valid_until IS NULL
            OR start_date IS NULL
            OR quotation_valid_until >= start_date
        )
);


-- 4. SUBSCRIPTION LINES
CREATE TABLE subscription_lines (

    subscription_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    subscription_id BIGINT NOT NULL,

    product_id BIGINT NOT NULL,

    variant_id BIGINT,

    quantity INT NOT NULL DEFAULT 1
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0),

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
        ON DELETE RESTRICT
);


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;