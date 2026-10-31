
-- ==========================================
-- STAGE 10: EXISTING DATA AUDIT
-- ==========================================

SELECT 'roles' AS table_name, COUNT(*) AS records FROM roles
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'product_variants', COUNT(*) FROM product_variants
UNION ALL
SELECT 'plans', COUNT(*) FROM plans
UNION ALL
SELECT 'plan_products', COUNT(*) FROM plan_products
UNION ALL
SELECT 'quotation_templates', COUNT(*) FROM quotation_templates
UNION ALL
SELECT 'quotation_template_lines', COUNT(*) FROM quotation_template_lines
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'subscription_lines', COUNT(*) FROM subscription_lines
UNION ALL
SELECT 'taxes', COUNT(*) FROM taxes
UNION ALL
SELECT 'discounts', COUNT(*) FROM discounts
UNION ALL
SELECT 'discount_products', COUNT(*) FROM discount_products
UNION ALL
SELECT 'discount_usages', COUNT(*) FROM discount_usages
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'invoice_lines', COUNT(*) FROM invoice_lines
UNION ALL
SELECT 'invoice_discounts', COUNT(*) FROM invoice_discounts
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'payment_allocations', COUNT(*) FROM payment_allocations
UNION ALL
SELECT 'billing_records', COUNT(*) FROM billing_records
UNION ALL
SELECT 'password_reset_tokens', COUNT(*) FROM password_reset_tokens
UNION ALL
SELECT 'customer_users', COUNT(*) FROM customer_users
ORDER BY table_name;
