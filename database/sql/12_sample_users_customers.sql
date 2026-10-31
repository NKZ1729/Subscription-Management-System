
-- ==========================================
-- STAGE 10: SAMPLE DATA
-- STEP 1: USERS AND CUSTOMERS
-- ==========================================

BEGIN;

-- Enable password hashing support
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- 1. INSERT SAMPLE USERS

INSERT INTO users (
    role_id,
    email,
    password_hash,
    full_name
)
SELECT
    r.role_id,
    sample.email,
    crypt(sample.demo_password, gen_salt('bf', 12)),
    sample.full_name
FROM (
    VALUES
        (
            'Admin',
            'admin@brightloop.test',
            'AdminDemo#2026',
            'Brightloop Administrator'
        ),
        (
            'Staff',
            'staff@brightloop.test',
            'StaffDemo#2026',
            'Sales Staff'
        ),
        (
            'Customer',
            'alex@abctech.test',
            'CustomerDemo#2026',
            'Alex Morgan'
        )
) AS sample(role_name, email, demo_password, full_name)
JOIN roles r
    ON r.role_name = sample.role_name
ON CONFLICT (email) DO NOTHING;


-- 2. INSERT SAMPLE CUSTOMER

INSERT INTO customers (
    company_name,
    contact_email,
    phone,
    billing_address
)
SELECT
    'ABC Technologies',
    'alex@abctech.test',
    '+91 9876543210',
    'Kochi, Kerala, India'
WHERE NOT EXISTS (
    SELECT 1
    FROM customers
    WHERE contact_email = 'alex@abctech.test'
);


-- 3. CONNECT CUSTOMER WITH CUSTOMER USER

INSERT INTO customer_users (
    customer_id,
    user_id,
    is_primary_contact
)
SELECT
    c.customer_id,
    u.user_id,
    TRUE
FROM customers c
JOIN users u
    ON u.email = 'alex@abctech.test'
WHERE c.contact_email = 'alex@abctech.test'
ON CONFLICT (customer_id, user_id) DO NOTHING;


COMMIT;


SELECT
    u.user_id,
    u.full_name,
    u.email,
    r.role_name
FROM users u
JOIN roles r
    ON u.role_id = r.role_id
ORDER BY u.user_id;

SELECT * FROM customers;

SELECT
    c.company_name,
    u.full_name,
    u.email,
    cu.is_primary_contact
FROM customer_users cu
JOIN customers c
    ON cu.customer_id = c.customer_id
JOIN users u
    ON cu.user_id = u.user_id;