
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 7: RECURRING BILLING
-- ==========================================

CREATE TABLE billing_records (

    billing_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    subscription_id BIGINT NOT NULL,

    invoice_id BIGINT UNIQUE,

    billing_period_start DATE NOT NULL,

    billing_period_end DATE NOT NULL,

    scheduled_date DATE NOT NULL,

    billing_status VARCHAR(30) NOT NULL DEFAULT 'Pending'
        CHECK (
            billing_status IN (
                'Pending',
                'Processing',
                'Completed',
                'Failed'
            )
        ),

    attempt_count INT NOT NULL DEFAULT 0
        CHECK (attempt_count >= 0),

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
        UNIQUE (
            subscription_id,
            billing_period_start,
            billing_period_end
        )
);


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;