
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 4: TAXES AND DISCOUNTS
-- ==========================================


-- 1. TAXES
CREATE TABLE taxes (

    tax_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    tax_name VARCHAR(100) NOT NULL,

    tax_rate NUMERIC(5,2) NOT NULL
        CHECK (tax_rate >= 0 AND tax_rate <= 100),

    description TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 2. DISCOUNTS
CREATE TABLE discounts (

    discount_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    discount_name VARCHAR(150) NOT NULL,

    discount_type VARCHAR(20) NOT NULL
        CHECK (discount_type IN ('fixed', 'percentage')),

    discount_value NUMERIC(12,2) NOT NULL
        CHECK (discount_value > 0),

    applies_to VARCHAR(20) NOT NULL
        CHECK (applies_to IN ('product', 'subscription')),

    minimum_purchase NUMERIC(12,2) DEFAULT 0
        CHECK (minimum_purchase >= 0),

    minimum_quantity INT DEFAULT 1
        CHECK (minimum_quantity > 0),

    start_date DATE NOT NULL,

    end_date DATE,

    usage_limit INT
        CHECK (usage_limit IS NULL OR usage_limit > 0),

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
        CHECK (
            discount_type <> 'percentage'
            OR discount_value <= 100
        )
);


-- 3. DISCOUNT PRODUCTS
CREATE TABLE discount_products (

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


-- 4. DISCOUNT USAGES
CREATE TABLE discount_usages (

    usage_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    discount_id BIGINT NOT NULL,

    subscription_id BIGINT NOT NULL,

    discount_amount NUMERIC(12,2) NOT NULL
        CHECK (discount_amount >= 0),

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


-- 5. ADD TAX REFERENCE TO SUBSCRIPTION LINES

ALTER TABLE subscription_lines
ADD COLUMN tax_id BIGINT;

ALTER TABLE subscription_lines
ADD CONSTRAINT fk_subscription_line_tax
FOREIGN KEY (tax_id)
REFERENCES taxes(tax_id)
ON DELETE RESTRICT;


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;