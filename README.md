# 📊 AI Data Analyst Agent Using n8n & PostgreSQL

> An end-to-end, production-grade AI Data Analyst Agent that translates natural language business questions into deterministic SQL queries, verifies accounting integrity, detects statistical anomalies, and generates actionable executive reports.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](https://www.python.org/)
[![PostgreSQL: 14+](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org/)
[![n8n: Workflow](https://img.shields.io/badge/n8n-Orchestration-EA4B71.svg)](https://n8n.io/)
[![Tests: Passing](https://img.shields.io/badge/Tests-13%20Passed-success.svg)](tests/)

---

## 📌 Table of Contents
1. [Project Overview](#-project-overview)
2. [Business Problem & Objective](#-business-problem--objective)
3. [Key Features](#-key-features)
4. [Technology Stack & Architectural Rationale](#-technology-stack--architectural-rationale)
5. [System Architecture](#-system-architecture)
6. [Defense-in-Depth Security Model](#-defense-in-depth-security-model)
7. [Dataset Description & Business Metrics](#-dataset-description--business-metrics)
8. [Quick Start & Local Setup](#-quick-start--local-setup)
9. [n8n Workflow Setup & Import](#-n8n-workflow-setup--import)
10. [Testing & Quality Verification](#-testing--quality-verification)
11. [Example Business Queries & Outputs](#-example-business-queries--outputs)
12. [Interactive Web Dashboard](#-interactive-web-dashboard)
13. [Limitations & Future Roadmap](#-limitations--future-roadmap)
14. [Repository Structure](#-repository-structure)
15. [Interview & Resume Guide](#-interview--resume-guide)

---

## 📖 Project Overview

In data-driven organizations, business stakeholders (Founders, Category Managers, Sales Heads) need real-time answers to commercial performance questions:
- *"What was our total revenue and net profit margin?"*
- *"Which products generated the highest sales?"*
- *"Which category is underperforming or losing money?"*
- *"Are there unusual spikes or anomalies in monthly sales?"*

Traditional BI tools (Tableau, PowerBI) require navigating rigid dashboards, while naive AI "Text-to-SQL" tools suffer from **hallucinations, security vulnerabilities, and mathematical inaccuracies**.

This project implements an **enterprise-grade, hybrid AI-analytics architecture**:
1. **Natural Language Understanding**: Classifies questions into an approved analytical catalog.
2. **Deterministic SQL Execution**: Runs verified, optimized SQL queries against PostgreSQL using a restricted read-only database user.
3. **Statistical Anomaly Detection**: Uses standard deviation thresholds to highlight outlier months.
4. **AI Business Synthesis**: Synthesizes verified data into executive summaries, clearly separating observed facts from strategic hypotheses.

---

## 🎯 Business Problem & Objective

### The Business Challenge
E-commerce businesses track thousands of daily sales across diverse categories and cities. Non-technical managers frequently wait days for business intelligence analysts to write SQL scripts for ad-hoc inquiries.

### The Objective
Build a lightweight, reliable, self-service AI Data Analyst that:
- Answers commercial questions instantly via webhooks or chat.
- Guarantees 100% mathematical accuracy by using actual database aggregations rather than LLM guesswork.
- Prevents database corruption or data exfiltration by enforcing an intent allowlist and read-only database roles.
- Delivers actionable recommendations (e.g., repricing loss-making products, bundling high-margin items).

---

## ✨ Key Features

1. **Deterministic Financial Metrics**: Computes Total Sales, Cost of Goods Sold (COGS), Gross Profit, Net Profit Margin (%), and Average Order Value (AOV).
2. **Product Performance Ranking**: Automatically identifies top revenue drivers (e.g., Gaming Laptops) and loss-making SKUs (e.g., Budget Smartwatches).
3. **Multi-Dimensional Breakdown**: Aggregates revenue, order volume, and profit across product categories and customer cities.
4. **Time-Series & MoM Growth**: Uses SQL window functions (`LAG()`) to calculate Month-over-Month growth rates.
5. **Statistical Anomaly Detection**: Evaluates monthly revenue variance ($\mu \pm 0.5\sigma$) to flag abnormal drops or seasonal surges.
6. **Strict Security Guardrails**: Pre-approved SQL query catalog prevents prompt injection and unauthorized database modifications.
7. **Automated Data Quality Audit**: Python validation scripts verify column types, duplicate primary keys, and the accounting identity $\text{Profit} = \text{Sales} - \text{Cost}$.
8. **Interactive Web Interface**: Clean HTML/JS dashboard with instant metric cards, query inspector, and tabular views.

---

## 🛠️ Technology Stack & Architectural Rationale

| Technology | Purpose in This Project | Why We Chose It |
| :--- | :--- | :--- |
| **n8n** | Workflow Orchestration | Visual execution flow, built-in error branching, and easy webhook integration without writing complex web server boilerplate. |
| **PostgreSQL 16** | Relational Analytical Store | ACID compliance, robust window functions (`LAG()`), and granular Role-Based Access Control (RBAC). |
| **SQL** | Aggregations & Calculations | Mathematical determinism; ensures calculations are 100% reproducible and never hallucinated. |
| **Python 3.9+** | Data Quality & Testing | Pre-ingestion CSV audits, statistical standard deviation calculations, and automated unit testing. |
| **Docker Compose** | Containerized Local Setup | Spins up PostgreSQL and n8n with one command, mounting initialization scripts automatically. |
| **HTML5 / CSS / Vanilla JS** | Web Dashboard | Zero-dependency, lightweight interface for testing questions and viewing metrics. |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([Business Stakeholder / Browser]) -->|Question: "Which products underperformed?"| Webhook[n8n Webhook Trigger]
    
    subgraph Security & Validation Layer
        Webhook --> Val[1. Input Sanitization & Token Filter]
        Val --> Classify[2. Intent Classifier & Allowlist Guardrail]
    end
    
    subgraph Data Execution Layer
        Classify -->|Approved Intent: underperforming_products| Dispatch[3. Safe SQL Query Dispatcher]
        Dispatch -->|Read-Only Parameterized Query| Postgres[(PostgreSQL 16\nUser: data_analyst_readonly)]
        Postgres -->|Verified Result Rows| Formatter[4. Results Formatter & Quality Check]
    end
    
    subgraph Intelligence & Response Layer
        Formatter --> Synthesis[5. AI Business Analyst Synthesis\nFacts vs Hypotheses]
        Synthesis --> Response[6. Structured JSON / Markdown Report]
    end
    
    Response --> User
```

---

## 🛡️ Defense-in-Depth Security Model

Allowing an LLM to generate and run arbitrary SQL directly against a production database is hazardous. This project enforces a **4-tier defense-in-depth model**:

1. **Input Sanitization**: Rejects requests containing destructive tokens (`DROP TABLE`, `DELETE FROM`, `UPDATE`, `;--`, `<script>`).
2. **Intent Allowlist**: Restricts execution to 8 pre-tested analytical intents. Unrecognized requests are rejected before querying the database.
3. **Parameterized SQL Templates**: All queries use structured parameter bindings rather than string concatenation.
4. **Database Principle of Least Privilege**: The workflow connects using a dedicated `data_analyst_readonly` role granted only `SELECT` privileges. Write operations are blocked at the database engine level.

---

## 📊 Dataset Description & Business Metrics

The project uses a representative e-commerce transactions dataset (`data/sample_sales.csv`) spanning 6 months (October 2023 to March 2024).

### Schema Columns:
- `order_id`: Unique primary key (e.g., `ORD-1001`).
- `order_date`: Transaction date (`YYYY-MM-DD`).
- `product_name`: Item name (17 distinct SKUs).
- `category`: Product category (`Electronics`, `Furniture`, `Home Appliances`, `Clothing`).
- `city`: Metro market (`Bengaluru`, `Mumbai`, `Delhi`, `Hyderabad`, `Chennai`, `Pune`).
- `quantity`: Number of units purchased ($> 0$).
- `sales`: Gross transaction revenue ($\ge 0$).
- `cost`: Total cost of goods sold ($\ge 0$).
- `profit`: Calculated gross profit ($\text{sales} - \text{cost}$).
- `customer_id`: Unique customer identifier.

### Dataset Baseline Metrics:
- **Total Revenue**: ₹17,43,334.00
- **Total Profit**: ₹4,16,734.00
- **Overall Profit Margin**: 23.90%
- **Average Order Value (AOV)**: ₹29,055.57
- **Top Product**: Gaming Laptop (₹9,10,000 revenue | 20% margin)
- **Loss-Making Product**: Budget Smartwatch (₹59,960 revenue | -₹12,040 loss | -20.08% margin)

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (Optional, for running PostgreSQL and n8n together)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/surya7274/ai-data-analyst-agent-n8n.git
cd ai-data-analyst-agent-n8n
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Run Data Validation & Analytics Engine (Standalone Python)
The Python engine has **zero mandatory external dependencies** and works out-of-the-box:

```bash
# Validate dataset integrity & accounting logic
python3 python/data_validation.py

# Generate executive analytics summary
python3 python/analysis.py
```

### 4. Start PostgreSQL and n8n via Docker Compose
```bash
docker compose up -d
```
This automatically:
- Starts PostgreSQL 16 on port `5432`.
- Seeds the database schema and 60 transactions from `database/schema.sql` and `database/sample_data.sql`.
- Starts n8n on `http://localhost:5678`.

---

## 🔄 n8n Workflow Setup & Import

1. Open your browser and navigate to `http://localhost:5678`.
2. Follow the on-screen prompt to create your local n8n admin account (first-time only).
3. In the left navigation, click **Workflows** → **Add Workflow** (or press `Ctrl/Cmd + O`).
4. Click the three dots `...` in the top right corner and select **Import from File...**.
5. Select `n8n/ai_data_analyst_workflow.json` from this repository.
6. Configure the PostgreSQL credential in n8n:
   - **Host**: `postgres` (if using Docker) or `localhost`
   - **Database**: `postgres`
   - **User**: `data_analyst_readonly`
   - **Password**: `ReadonlyAnalyst#2024`
   - **Port**: `5432`
7. Click **Save** and toggle the workflow from **Inactive** to **Active**.

---

## 🧪 Testing & Quality Verification

Run the automated test suite covering data quality, SQL ranking, MoM growth calculations, anomaly detection, security allowlisting, and n8n JSON schema integrity:

```bash
python3 -m unittest discover tests
```

### Test Results Summary:
```text
.............
----------------------------------------------------------------------
Ran 13 tests in 0.009s

OK
```
All 13 unit and integration tests validate:
- CSV schema and date formatting.
- Mathematical accounting identity ($\text{Profit} = \text{Sales} - \text{Cost}$).
- Outlier detection flagging January dip and March surge.
- Rejection of unauthorized SQL / prompt injection tokens.
- n8n node connection graph integrity.

---

## 💬 Example Business Queries & Outputs

### Query 1: *"Which product generated the highest revenue?"*
- **SQL Executed**:
  ```sql
  SELECT product_name, category, SUM(sales) AS total_revenue, 
         ROUND((SUM(profit)/SUM(sales))*100, 2) AS profit_margin_pct
  FROM ecommerce_sales GROUP BY product_name, category ORDER BY total_revenue DESC LIMIT 5;
  ```
- **Direct Answer**: *"The highest revenue generating product is Gaming Laptop (Electronics), generating ₹9,10,000 in revenue and ₹1,82,000 in profit (20.0% margin)."*
- **Actionable Recommendation**: *"Bundle ergonomic chairs or standing desks with gaming laptops to lift average order value and blended margin."*

---

### Query 2: *"Which products are underperforming or making losses?"*
- **Direct Answer**: *"Budget Smartwatch generated ₹59,960 in revenue but incurred a net loss of -₹12,040 (-20.08% margin) across 40 units sold."*
- **Analytical Insight**: *"Sold below unit cost (Unit Price ₹1,499 vs Cost ₹1,800), meaning higher sales volume directly increases cumulative business losses."*
- **Actionable Recommendation**: *"Immediately reprice Budget Smartwatch to at least ₹2,199 to cover procurement and logistics costs, or renegotiate supplier terms."*

---

### Query 3: *"Detect any unusual sales anomalies or spikes"*
- **Direct Answer**: *"Statistical anomaly detection flagged 2 outlier months: January 2024 as a LOW OUTLIER (-44.25% below 6-month mean) and March 2024 as a HIGH OUTLIER (+46.09% above mean)."*
- **Actionable Recommendation**: *"Prepare inventory buffers in February to meet the surge in March corporate fiscal-year-end demand."*

---

## 💻 Interactive Web Dashboard

Open `web/index.html` directly in any web browser:
```bash
open web/index.html
```

### Dashboard Features:
- **Natural Language Input**: Type any business question or click one of the suggested question chips.
- **Webhook Integration**: Point to your running n8n instance (`http://localhost:5678/webhook/data-analyst`).
- **Built-in Demo Mode**: If n8n is offline, the interface seamlessly falls back to the deterministic benchmark engine so you can test all 8 business scenarios instantly.
- **SQL Transparency Box**: Displays the exact SQL executed for full auditability.

```
+------------------------------------------------------------------------+
|                      AI DATA ANALYST DASHBOARD                         |
|  [ Input: "Which product generated highest revenue?" ]  [ Analyze ]   |
+------------------------------------------------------------------------+
|  💡 Executive Answer: Gaming Laptop generated ₹9,10,000 (20% margin)   |
|  📈 Key Metrics: [ Revenue: ₹9,10,000 ] [ Profit: ₹1,82,000 ]         |
|  🛡️ SQL Executed: SELECT product_name, SUM(sales)... LIMIT 5;         |
|  🎯 Recommendation: Bundle with Ergonomic Chair to increase AOV       |
+------------------------------------------------------------------------+
```

*(Screenshot placeholder: Add your dashboard screenshot here as `docs/dashboard_screenshot.png`)*

---

## ⚠️ Limitations & Future Roadmap

### Current Limitations:
- Query catalog is restricted to 8 predefined analytical intents to guarantee security and prevent SQL injection.
- Single-table schema (`ecommerce_sales`). Multi-table relational joins (e.g., separate `customers`, `returns`, and `inventory` tables) can be added.

### Future Improvements:
- **dbt Integration**: Implement data build tool (dbt) models for pre-aggregating daily and monthly metrics.
- **Slack / Teams Bot**: Connect n8n to Slack so executives can ask questions directly in channels like `#sales-leadership`.
- **Automated Anomaly Alerting**: Trigger scheduled daily n8n crons that email operations if daily sales drop $> 25\%$ below moving average.

---

## 📂 Repository Structure

```text
ai-data-analyst-agent-n8n/
├── README.md                      # Comprehensive project guide & documentation
├── .gitignore                     # Git ignore rules (secrets, venv, cache)
├── .env.example                   # Environment configuration template
├── requirements.txt               # Optional Python analytics dependencies
├── docker-compose.yml             # Containerized PostgreSQL 16 & n8n setup
├── LICENSE                        # MIT Open Source License
├── data/
│   └── sample_sales.csv           # Validated 60-row commercial sales dataset
├── database/
│   ├── schema.sql                 # PostgreSQL table definition, indexes & RBAC
│   ├── sample_data.sql            # Seed data (60 orders across 6 months)
│   └── analytics_queries.sql      # Verified analytical queries & CTEs
├── python/
│   ├── data_validation.py         # CSV schema, PK, and accounting integrity audit
│   └── analysis.py                # Zero-dependency analytics & anomaly engine
├── n8n/
│   └── ai_data_analyst_workflow.json # Importable n8n workflow definition
├── docs/
│   ├── architecture.md            # System architecture & 4-tier security model
│   ├── workflow_explanation.md    # Node-by-node walkthrough & payload schemas
│   └── interview_questions.md     # 12 Data Analyst interview Q&A for freshers
├── tests/
│   └── test_analysis.py           # 13 automated unit & integration tests
└── web/
    └── index.html                 # Clean, responsive HTML/JS executive dashboard
```

---

## 💼 Interview & Resume Guide

### Resume Bullet Points (Tailored for Data Analyst Roles):
- *Designed and deployed an AI-assisted analytics pipeline using n8n and PostgreSQL, allowing commercial stakeholders to query e-commerce metrics in natural language with 100% calculation determinism.*
- *Architected a 4-tier defense-in-depth security model with pre-approved SQL allowlists and PostgreSQL RBAC (`data_analyst_readonly`), eliminating SQL injection and LLM hallucination risks.*
- *Authored complex SQL queries utilizing window functions (`LAG()`) and CTEs to evaluate Month-over-Month (MoM) revenue trends across 17 SKUs and 6 metro markets.*
- *Implemented statistical anomaly detection using mean-variance thresholds ($\mu \pm 0.5\sigma$) to automatically flag abnormal revenue deviations (such as a 44% drop in post-holiday sales).*
- *Developed automated Python validation scripts enforcing accounting reconciliations ($\text{Profit} = \text{Sales} - \text{Cost}$) and primary key constraints prior to database ingestion.*

### For Full Interview Prep:
Read [docs/interview_questions.md](docs/interview_questions.md) for 12 detailed questions and beginner-friendly answers explaining window functions, AOV, Least Privilege security, and business recommendations.
