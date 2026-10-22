-- ============================================================================
-- File: schema.sql
-- Project: AI Data Analyst Agent Using n8n
-- Database: PostgreSQL 14+ / Compatible with standard SQL
-- ============================================================================

-- Drop table if already exists (safe for clean environment initialization)
DROP TABLE IF EXISTS ecommerce_sales;

-- 1. Main Business Transactions Table
CREATE TABLE ecommerce_sales (
    order_id        VARCHAR(50)     PRIMARY KEY,
    order_date      DATE            NOT NULL,
    product_name    VARCHAR(100)    NOT NULL,
    category        VARCHAR(50)     NOT NULL,
    city            VARCHAR(50)     NOT NULL,
    quantity        INTEGER         NOT NULL CHECK (quantity > 0),
    sales           NUMERIC(12, 2)  NOT NULL CHECK (sales >= 0),
    cost            NUMERIC(12, 2)  NOT NULL CHECK (cost >= 0),
    profit          NUMERIC(12, 2)  NOT NULL,
    customer_id     VARCHAR(50)     NOT NULL
);

-- 2. Performance Indexes (speeds up aggregations and filters in n8n queries)
CREATE INDEX IF NOT EXISTS idx_sales_order_date ON ecommerce_sales (order_date);
CREATE INDEX IF NOT EXISTS idx_sales_category   ON ecommerce_sales (category);
CREATE INDEX IF NOT EXISTS idx_sales_city       ON ecommerce_sales (city);
CREATE INDEX IF NOT EXISTS idx_sales_product    ON ecommerce_sales (product_name);

-- 3. Security: Read-Only Role Definition (Defense in Depth)
-- In production, the n8n database credential MUST use a read-only role.
-- This ensures that even if an unexpected SQL command is issued, PostgreSQL blocks modifications.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'data_analyst_readonly') THEN
        CREATE ROLE data_analyst_readonly WITH LOGIN PASSWORD 'ReadonlyAnalyst#2024';
    END IF;
END
$$;

-- Grant read-only permissions
GRANT CONNECT ON DATABASE postgres TO data_analyst_readonly;
GRANT USAGE ON SCHEMA public TO data_analyst_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO data_analyst_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO data_analyst_readonly;
