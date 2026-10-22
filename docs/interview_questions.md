# Data Analyst Interview Preparation Guide

This guide is designed for **BBA graduates and freshers targeting Data Analyst, Business Analyst, and BI Analyst roles in India**. It explains the core concepts of this project in simple English and provides answers to 12 likely interview questions.

---

## 1. The 60-Second Elevator Pitch

> *"In this project, I built an end-to-end AI Data Analyst Agent that translates natural language business questions into verified SQL queries and executive insights using n8n and PostgreSQL.
>
> Many early AI projects fail because LLMs hallucinate calculations. In my system, the LLM is never allowed to invent numbers or execute raw SQL. Instead, n8n classifies user questions into an allowlist of pre-approved business metrics—such as total revenue, top products, monthly trends, and profit margins. Safe SQL queries are executed against a PostgreSQL database with a read-only user role. The verified query output is then synthesized into an executive summary with key KPIs, analytical observations, and actionable business recommendations.
>
> I also built Python data validation scripts to verify accounting rules and detect statistical anomalies using standard deviation thresholds."*

---

## 2. Top 12 Interview Questions & Answers

### Q1: Why did you use n8n instead of writing everything in custom Python code?
**Simple Answer**:  
n8n is an open-source workflow automation platform. In modern business teams, data analysts need to connect databases, webhook triggers, chat platforms (like Slack or Teams), and AI models rapidly. Using n8n gave me:
1. **Visual Data Lineage**: I can inspect the exact payload moving from node to node in real time.
2. **Error Handling**: Built-in branching nodes make it easy to catch errors (e.g., bad inputs, database timeouts) and return clear status codes.
3. **Enterprise Integration**: It can be deployed in a Docker container alongside PostgreSQL and easily integrated with corporate webhooks without writing boilerplate web server code.

---

### Q2: Why did you perform metric calculations in PostgreSQL instead of letting the LLM calculate them?
**Simple Answer**:  
LLMs are probabilistic language models, not calculators. If you ask an LLM to sum 60 transactions, it will often hallucinate plausible-looking numbers that are mathematically incorrect.  
SQL is deterministic: `SUM(sales)` will return the exact, reproducible total every single time. As a Data Analyst, my responsibility is to ensure 100% data integrity. Therefore, SQL does the math, and the LLM merely translates those verified facts into plain-English business language.

---

### Q3: Why didn't you let the LLM generate raw SQL queries dynamically (Text-to-SQL)?
**Simple Answer**:  
Direct Text-to-SQL creates severe security and reliability risks:
1. **SQL Injection**: A malicious prompt could trick the LLM into generating `DROP TABLE` or exfiltrating customer data.
2. **Hallucinated Schemas**: LLMs often invent column names that do not exist or choose the wrong table joins.
3. **Performance Issues**: An unconstrained LLM might generate unindexed full-table scans that overwhelm the database.

By using an **Allowlist Architecture**, user queries are classified into approved business intents (e.g., `top_products`, `monthly_trend`), and mapped to pre-tested, parameterized SQL queries.

---

### Q4: How did you calculate Month-over-Month (MoM) revenue growth in SQL?
**Simple Answer**:  
I used SQL Common Table Expressions (CTEs) and the `LAG()` window function:
```sql
WITH monthly_metrics AS (
    SELECT 
        TO_CHAR(order_date, 'YYYY-MM') AS sales_month,
        ROUND(SUM(sales), 2)          AS monthly_revenue
    FROM ecommerce_sales
    GROUP BY TO_CHAR(order_date, 'YYYY-MM')
)
SELECT 
    sales_month,
    monthly_revenue,
    ROUND(
        ((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY sales_month)) 
        / NULLIF(LAG(monthly_revenue) OVER (ORDER BY sales_month), 0)) * 100, 
        2
    ) AS mom_revenue_growth_pct
FROM monthly_metrics;
```
`LAG(monthly_revenue) OVER (ORDER BY sales_month)` accesses the revenue from the preceding row without needing an expensive self-join. `NULLIF(..., 0)` prevents division-by-zero errors.

---

### Q5: What is Average Order Value (AOV), and why is it important in e-commerce?
**Simple Answer**:  
$\text{Average Order Value (AOV)} = \frac{\text{Total Revenue}}{\text{Total Number of Orders}}$.  
In our dataset, the total revenue is ₹17,43,334 across 60 orders, resulting in an AOV of ₹29,055.57.  
AOV is a critical business metric because increasing AOV allows a business to grow top-line revenue without necessarily spending more money on customer acquisition. For example, bundling an ergonomic chair with a standing desk raises the basket size per transaction.

---

### Q6: What did your analysis reveal about underperforming products?
**Simple Answer**:  
The analysis identified that the **Budget Smartwatch** generated ₹59,960 in revenue but incurred a net loss of -₹12,040 (-20.08% margin).  
Looking into unit economics, each smartwatch was sold for ₹1,499 while the unit procurement cost was ₹1,800. Every unit sold actually lost the company ₹301.  
**My Recommendation**:
1. Immediately reprice the item to at least ₹2,199 to cover unit cost and restore a positive gross margin.
2. If the item was deliberately priced as a "loss leader" to attract traffic, analyze customer retention data to see if those buyers subsequently purchase high-margin items like laptops.

---

### Q7: Explain the statistical anomaly detection logic you used.
**Simple Answer**:  
Instead of using a complex machine learning black box, I used standard descriptive statistics:
1. Calculated the **mean monthly revenue** ($\mu = ₹2,90,555.67$) across the 6-month period.
2. Calculated the **standard deviation** ($\sigma$) to measure natural business variance.
3. Established threshold bands: $\mu \pm (0.5 \times \sigma)$.
4. Flagged any month exceeding the upper band as `HIGH_OUTLIER` and any month falling below the lower band as `LOW_OUTLIER`.

**Findings**:
- **January 2024** was flagged as a `LOW_OUTLIER` (₹1,61,982, down -44.25% from mean) due to a post-holiday slump and drop in gaming laptop orders.
- **March 2024** was flagged as a `HIGH_OUTLIER` (₹4,24,461, up +46.09% above mean) driven by fiscal year-end procurement.

---

### Q8: How do you distinguish an observed fact from a business hypothesis?
**Simple Answer**:  
- **Observed Fact**: A statement directly supported by the data. E.g., *"Electronics accounted for 64.9% of total revenue, but Clothing had the highest profit margin at 48.37%."*
- **Hypothesis / Explanation**: A plausible business reason that requires further validation. E.g., *"The surge in March orders could be due to corporate budget exhaustion before the fiscal year ends."*

As a data analyst, I present facts first, clearly label hypotheses as potential causes, and recommend concrete next steps to verify them.

---

### Q9: Why did you create a dedicated read-only role (`data_analyst_readonly`) in PostgreSQL?
**Simple Answer**:  
This follows the principle of **Least Privilege (PoLP)** and Defense-in-Depth.  
Even though our application sanitizes queries and validates intents, human error or software bugs could theoretically pass an unwanted command. By configuring n8n with database credentials restricted to `SELECT` permissions on `ecommerce_sales`, PostgreSQL will natively reject any `INSERT`, `UPDATE`, `DELETE`, or `DROP` statements at the database engine level.

---

### Q10: How did your Python data validation script ensure data quality before ingestion?
**Simple Answer**:  
Before loading raw data into PostgreSQL, `data_validation.py` enforces five crucial checks:
1. **Schema Check**: All 10 required columns exist.
2. **Primary Key Integrity**: No duplicate `order_id` values.
3. **Data Type & Range Validation**: `quantity > 0`, `sales >= 0`, `cost >= 0`, and valid `YYYY-MM-DD` date formats.
4. **Accounting Reconciliation**: Verifies that $\text{Profit} = \text{Sales} - \text{Cost}$ within a 2-cent rounding tolerance.
5. **Categorical Profiling**: Counts distinct cities, categories, and customers to identify outliers or misspellings.

---

### Q11: If this system had to process 10 million transactions instead of 60, what would change?
**Simple Answer**:  
1. **Database Indexing**: Compound indexes on `(order_date, category)` and partitioning the table by month or year.
2. **Aggregated Summary Tables / Materialized Views**: Instead of querying raw rows for monthly trends, pre-calculate daily and monthly aggregates using scheduled cron jobs or dbt.
3. **Caching**: Store frequently requested metrics (like yesterday's total sales) in Redis so repeated questions don't hit the database.
4. **Read Replicas**: Route analytical queries from n8n to a read replica to avoid placing load on the primary transactional database (OLTP).

---

### Q12: Which category in the dataset had the best performance, and what strategic advice would you give?
**Simple Answer**:  
Performance depends on whether we optimize for revenue volume or profit margin:
- **Electronics** had the highest revenue (₹11,31,914) but a moderate margin of 20.10%.
- **Clothing** had the lowest revenue (₹80,957) but the highest profit margin of **48.37%** (nearly double the company average of 23.90%).

**Strategic Recommendation**:  
Allocate more marketing budget and homepage promotional banners to the Clothing category. Because Clothing has a 48.37% margin, increasing its share of total sales will lift the company's overall blended profit margin without requiring higher fixed overheads.
