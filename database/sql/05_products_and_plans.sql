
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 2: PRODUCTS AND PLANS
-- ==========================================

-- 1. PRODUCTS
CREATE TABLE products (

    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    name VARCHAR(200) NOT NULL,

    product_type VARCHAR(50) NOT NULL,

    sales_price NUMERIC(12,2) NOT NULL
        CHECK (sales_price >= 0),

    cost_price NUMERIC(12,2) NOT NULL
        CHECK (cost_price >= 0),

    notes TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 2. PRODUCT VARIANTS
CREATE TABLE product_variants (

    variant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    product_id BIGINT NOT NULL,

    variant_name VARCHAR(100) NOT NULL,

    additional_price NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (additional_price >= 0),

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


-- 3. PLANS
CREATE TABLE plans (

    plan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    plan_name VARCHAR(150) NOT NULL,

    description TEXT,

    billing_interval VARCHAR(20) NOT NULL
        CHECK (
            billing_interval IN (
                'daily',
                'weekly',
                'monthly',
                'yearly'
            )
        ),

    interval_count INT NOT NULL DEFAULT 1
        CHECK (interval_count > 0),

    minimum_quantity INT NOT NULL DEFAULT 1
        CHECK (minimum_quantity > 0),

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
        CHECK (
            available_until IS NULL
            OR available_until >= available_from
        )
);


-- 4. PLAN PRODUCTS
CREATE TABLE plan_products (

    plan_product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    plan_id BIGINT NOT NULL,

    product_id BIGINT NOT NULL,

    variant_id BIGINT,

    quantity INT NOT NULL DEFAULT 1
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0),

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

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
