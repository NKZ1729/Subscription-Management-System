
-- ==========================================
-- STAGE 8: FOREIGN KEY AUDIT
-- ==========================================

SELECT
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS relationship
FROM pg_constraint
WHERE contype = 'f'
AND connamespace = 'public'::regnamespace
ORDER BY table_name, constraint_name;



SELECT
    tc.table_name,
    kcu.column_name AS primary_key_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
    AND tc.table_name = kcu.table_name
WHERE tc.constraint_type = 'PRIMARY KEY'
AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.ordinal_position;



-- CHECK CONSTRAINT AUDIT

SELECT
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS condition
FROM pg_constraint
WHERE contype = 'c'
AND connamespace = 'public'::regnamespace
ORDER BY table_name, constraint_name;



-- ==========================================
-- STAGE 8: DATABASE STRUCTURE SUMMARY
-- ==========================================

SELECT
    'Tables' AS component,
    COUNT(*) AS total
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'

UNION ALL

SELECT
    'Primary Keys',
    COUNT(*)
FROM pg_constraint
WHERE contype = 'p'
AND connamespace = 'public'::regnamespace

UNION ALL

SELECT
    'Foreign Keys',
    COUNT(*)
FROM pg_constraint
WHERE contype = 'f'
AND connamespace = 'public'::regnamespace

UNION ALL

SELECT
    'Check Constraints',
    COUNT(*)
FROM pg_constraint
WHERE contype = 'c'
AND connamespace = 'public'::regnamespace;

-- ==========================================
-- STAGE 9: INDEX AUDIT
-- ==========================================

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;