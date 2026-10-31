
-- ==========================================
-- SUBSCRIPTION MANAGEMENT SYSTEM
-- STAGE 9: INDEXING AND OPTIMIZATION
-- ==========================================


-- 1. USER AND CUSTOMER MANAGEMENT

CREATE INDEX IF NOT EXISTS idx_users_role_id
ON users(role_id);

CREATE INDEX IF NOT EXISTS idx_customer_users_user_id
ON customer_users(user_id);

CREATE INDEX IF NOT EXISTS idx_password_reset_user_id
ON password_reset_tokens(user_id);


-- 2. PRODUCTS AND PLANS

CREATE INDEX IF NOT EXISTS idx_plan_products_plan_id
ON plan_products(plan_id);

CREATE INDEX IF NOT EXISTS idx_plan_products_product_variant
ON plan_products(product_id, variant_id);


-- 3. QUOTATIONS

CREATE INDEX IF NOT EXISTS idx_quotation_templates_plan_id
ON quotation_templates(plan_id);

CREATE INDEX IF NOT EXISTS idx_quotation_templates_created_by
ON quotation_templates(created_by);

CREATE INDEX IF NOT EXISTS idx_quotation_template_lines_template_id
ON quotation_template_lines(template_id);

CREATE INDEX IF NOT EXISTS idx_quotation_template_lines_product_variant
ON quotation_template_lines(product_id, variant_id);


-- 4. SUBSCRIPTIONS

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id
ON subscriptions(customer_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id
ON subscriptions(plan_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_template_id
ON subscriptions(template_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_created_by
ON subscriptions(created_by);

-- Find active subscriptions due for billing
CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing
ON subscriptions(next_billing_date)
WHERE status = 'Active';


-- 5. SUBSCRIPTION LINES

CREATE INDEX IF NOT EXISTS idx_subscription_lines_subscription_id
ON subscription_lines(subscription_id);

CREATE INDEX IF NOT EXISTS idx_subscription_lines_product_variant
ON subscription_lines(product_id, variant_id);

CREATE INDEX IF NOT EXISTS idx_subscription_lines_tax_id
ON subscription_lines(tax_id);


-- 6. DISCOUNTS

CREATE INDEX IF NOT EXISTS idx_discounts_created_by
ON discounts(created_by);

CREATE INDEX IF NOT EXISTS idx_discount_products_product_id
ON discount_products(product_id);

CREATE INDEX IF NOT EXISTS idx_discount_usages_discount_id
ON discount_usages(discount_id);

CREATE INDEX IF NOT EXISTS idx_discount_usages_subscription_id
ON discount_usages(subscription_id);


-- 7. INVOICES

CREATE INDEX IF NOT EXISTS idx_invoices_customer_id
ON invoices(customer_id);

-- Also supports subscription-to-customer consistency checks
CREATE INDEX IF NOT EXISTS idx_invoices_subscription_customer
ON invoices(subscription_id, customer_id);

-- Find overdue invoices efficiently
CREATE INDEX IF NOT EXISTS idx_invoices_overdue
ON invoices(due_date)
WHERE status IN ('Confirmed', 'Partially Paid');


-- 8. INVOICE LINES

CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice_id
ON invoice_lines(invoice_id);

CREATE INDEX IF NOT EXISTS idx_invoice_lines_product_id
ON invoice_lines(product_id);


-- 9. INVOICE DISCOUNTS

CREATE INDEX IF NOT EXISTS idx_invoice_discounts_invoice_id
ON invoice_discounts(invoice_id);

CREATE INDEX IF NOT EXISTS idx_invoice_discounts_discount_id
ON invoice_discounts(discount_id);


-- 10. PAYMENTS

CREATE INDEX IF NOT EXISTS idx_payment_allocations_invoice_id
ON payment_allocations(invoice_id);

CREATE INDEX IF NOT EXISTS idx_payments_completed_date
ON payments(payment_date)
WHERE status = 'Completed';


-- 11. RECURRING BILLING

-- Find pending and failed billing records
CREATE INDEX IF NOT EXISTS idx_billing_records_scheduled_date
ON billing_records(scheduled_date)
WHERE billing_status IN ('Pending', 'Failed');
