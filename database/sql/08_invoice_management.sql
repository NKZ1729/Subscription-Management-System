
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 5: INVOICE MANAGEMENT
-- ==========================================


-- 1. INVOICES
CREATE TABLE invoices (

    invoice_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    invoice_number VARCHAR(50) NOT NULL UNIQUE,

    subscription_id BIGINT NOT NULL,

    customer_id BIGINT NOT NULL,

    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,

    due_date DATE NOT NULL,

    billing_period_start DATE,

    billing_period_end DATE,

    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (subtotal >= 0),

    discount_total NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (discount_total >= 0),

    tax_total NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (tax_total >= 0),

    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (total_amount >= 0),

    status VARCHAR(30) NOT NULL DEFAULT 'Draft'
        CHECK (
            status IN (
                'Draft',
                'Confirmed',
                'Partially Paid',
                'Paid',
                'Cancelled'
            )
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
        CHECK (
            billing_period_end IS NULL
            OR billing_period_start IS NULL
            OR billing_period_end >= billing_period_start
        ),

    CONSTRAINT valid_invoice_totals
        CHECK (
            total_amount = subtotal - discount_total + tax_total
        )
);


-- 2. INVOICE LINES
CREATE TABLE invoice_lines (

    invoice_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    invoice_id BIGINT NOT NULL,

    product_id BIGINT NOT NULL,

    description TEXT,

    quantity INT NOT NULL
        CHECK (quantity > 0),

    unit_price NUMERIC(12,2) NOT NULL
        CHECK (unit_price >= 0),

    subtotal NUMERIC(12,2) NOT NULL
        CHECK (subtotal >= 0),

    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (discount_amount >= 0),

    tax_name VARCHAR(100),

    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (tax_rate >= 0 AND tax_rate <= 100),

    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (tax_amount >= 0),

    line_total NUMERIC(12,2) NOT NULL
        CHECK (line_total >= 0),

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
        CHECK (
            line_total = subtotal - discount_amount + tax_amount
        )
);


-- 3. INVOICE DISCOUNTS
CREATE TABLE invoice_discounts (

    invoice_discount_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    invoice_id BIGINT NOT NULL,

    discount_id BIGINT NOT NULL,

    discount_amount NUMERIC(12,2) NOT NULL
        CHECK (discount_amount >= 0),

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

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;