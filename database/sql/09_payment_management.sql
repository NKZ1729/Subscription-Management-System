
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 6: PAYMENT MANAGEMENT
-- ==========================================


-- 1. PAYMENTS
CREATE TABLE payments (

    payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    payment_method VARCHAR(50) NOT NULL,

    amount NUMERIC(12,2) NOT NULL
        CHECK (amount > 0),

    payment_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    reference_number VARCHAR(150),

    note TEXT,

    status VARCHAR(30) NOT NULL DEFAULT 'Completed'
        CHECK (
            status IN (
                'Pending',
                'Completed',
                'Failed',
                'Refunded'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 2. PAYMENT ALLOCATIONS
CREATE TABLE payment_allocations (

    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    payment_id BIGINT NOT NULL,

    invoice_id BIGINT NOT NULL,

    allocated_amount NUMERIC(12,2) NOT NULL
        CHECK (allocated_amount > 0),

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


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;