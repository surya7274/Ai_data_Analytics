-- ============================================================================
-- File: analytics_queries.sql
-- Project: AI Data Analyst Agent Using n8n
-- Purpose: Predefined, safe analytical queries executed by n8n workflow.
-- Security: These queries are mapped to an allowlist. The LLM never writes raw SQL.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. OVERALL BUSINESS SUMMARY
-- Purpose: Answers questions like "What was our total revenue / total profit / AOV?"
-- ----------------------------------------------------------------------------
-- Key Metrics:
-- - Total Sales: SUM(sales)
-- - Total Cost: SUM(cost)
-- - Total Profit: SUM(profit)
-- - Total Orders: COUNT(order_id)
-- - Average Order Value (AOV): SUM(sales) / COUNT(order_id)
-- - Profit Margin %: (SUM(profit) / SUM(sales)) * 100
SELECT 
    COUNT(order_id)                                  AS total_orders,
    SUM(quantity)                                    AS total_units_sold,
    ROUND(SUM(sales), 2)                             AS total_revenue,
    ROUND(SUM(cost), 2)                              AS total_cost,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS overall_profit_margin_pct,
    ROUND(AVG(sales), 2)                             AS average_order_value
FROM ecommerce_sales;


-- ----------------------------------------------------------------------------
-- 2. TOP PERFORMING PRODUCTS BY REVENUE & PROFIT
-- Purpose: Answers "Which products generated the highest revenue / profit?"
-- ----------------------------------------------------------------------------
SELECT 
    product_name,
    category,
    COUNT(order_id)                                  AS order_count,
    SUM(quantity)                                    AS units_sold,
    ROUND(SUM(sales), 2)                             AS total_revenue,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS profit_margin_pct
FROM ecommerce_sales
GROUP BY product_name, category
ORDER BY total_revenue DESC
LIMIT 5;


-- ----------------------------------------------------------------------------
-- 3. UNDERPERFORMING PRODUCTS (Negative or Lowest Profit)
-- Purpose: Answers "Which products have low or negative profit margins?"
-- ----------------------------------------------------------------------------
SELECT 
    product_name,
    category,
    SUM(quantity)                                    AS units_sold,
    ROUND(SUM(sales), 2)                             AS total_revenue,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS profit_margin_pct
FROM ecommerce_sales
GROUP BY product_name, category
ORDER BY total_profit ASC
LIMIT 5;


-- ----------------------------------------------------------------------------
-- 4. REVENUE & PROFIT BY CATEGORY
-- Purpose: Answers "Which category is performing the best / worst?"
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(order_id)                                  AS total_orders,
    SUM(quantity)                                    AS total_quantity,
    ROUND(SUM(sales), 2)                             AS total_revenue,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS profit_margin_pct
FROM ecommerce_sales
GROUP BY category
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- 5. GEOGRAPHIC ANALYSIS: REVENUE BY CITY
-- Purpose: Answers "Which city has the highest sales?"
-- ----------------------------------------------------------------------------
SELECT 
    city,
    COUNT(order_id)                                  AS total_orders,
    ROUND(SUM(sales), 2)                             AS total_revenue,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS profit_margin_pct
FROM ecommerce_sales
GROUP BY city
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- 6. MONTHLY REVENUE & PROFIT TRENDS WITH MOM (MONTH-OVER-MONTH) GROWTH
-- Purpose: Answers "What is our monthly revenue trend? Are sales growing?"
-- Uses: LAG() Window Function to compare current month with previous month
-- ----------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        TO_CHAR(order_date, 'YYYY-MM')               AS sales_month,
        COUNT(order_id)                              AS order_count,
        ROUND(SUM(sales), 2)                         AS monthly_revenue,
        ROUND(SUM(profit), 2)                        AS monthly_profit
    FROM ecommerce_sales
    GROUP BY TO_CHAR(order_date, 'YYYY-MM')
)
SELECT 
    sales_month,
    order_count,
    monthly_revenue,
    monthly_profit,
    ROUND(
        ((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY sales_month)) 
        / NULLIF(LAG(monthly_revenue) OVER (ORDER BY sales_month), 0)) * 100, 
        2
    ) AS mom_revenue_growth_pct
FROM monthly_metrics
ORDER BY sales_month ASC;


-- ----------------------------------------------------------------------------
-- 7. STATISTICAL ANOMALY DETECTION (Monthly Deviation from Mean)
-- Purpose: Answers "Are there any anomalies or unusual changes in sales?"
-- Identifies months where revenue deviated significantly (> 15%) from monthly average
-- ----------------------------------------------------------------------------
WITH monthly_agg AS (
    SELECT 
        TO_CHAR(order_date, 'YYYY-MM') AS sales_month,
        ROUND(SUM(sales), 2)          AS monthly_revenue,
        ROUND(SUM(profit), 2)         AS monthly_profit
    FROM ecommerce_sales
    GROUP BY TO_CHAR(order_date, 'YYYY-MM')
),
baseline AS (
    SELECT 
        ROUND(AVG(monthly_revenue), 2) AS avg_monthly_revenue,
        ROUND(STDDEV(monthly_revenue), 2) AS std_monthly_revenue
    FROM monthly_agg
)
SELECT 
    m.sales_month,
    m.monthly_revenue,
    m.monthly_profit,
    b.avg_monthly_revenue,
    ROUND(((m.monthly_revenue - b.avg_monthly_revenue) / b.avg_monthly_revenue) * 100, 2) AS deviation_from_avg_pct,
    CASE 
        WHEN m.monthly_revenue > (b.avg_monthly_revenue + 0.5 * b.std_monthly_revenue) THEN 'HIGH_OUTLIER'
        WHEN m.monthly_revenue < (b.avg_monthly_revenue - 0.5 * b.std_monthly_revenue) THEN 'LOW_OUTLIER'
        ELSE 'NORMAL'
    END AS anomaly_flag
FROM monthly_agg m
CROSS JOIN baseline b
ORDER BY m.sales_month;


-- ----------------------------------------------------------------------------
-- 8. PARAMETERIZED FILTERED QUERY (Date Range & Category)
-- Purpose: Safe query template used by n8n when user supplies date or category filters
-- Variables: $1 = start_date, $2 = end_date, $3 = category (or wildcard/all)
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(order_id)      AS order_count,
    ROUND(SUM(sales), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit
FROM ecommerce_sales
WHERE ($1::DATE IS NULL OR order_date >= $1::DATE)
  AND ($2::DATE IS NULL OR order_date <= $2::DATE)
  AND ($3::TEXT IS NULL OR category = $3::TEXT)
GROUP BY category
ORDER BY total_revenue DESC;
