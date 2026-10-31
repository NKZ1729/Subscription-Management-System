
-- Check whether invoice customers match
-- their associated subscription customers.

SELECT
    i.invoice_id,
    i.invoice_number,
    i.customer_id AS invoice_customer,
    s.customer_id AS subscription_customer
FROM invoices i
JOIN subscriptions s
    ON i.subscription_id = s.subscription_id
WHERE i.customer_id <> s.customer_id;
