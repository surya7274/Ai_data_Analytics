"""
analysis.py
Core Business Analytics Engine for E-commerce Sales.

Role: Senior Data Analyst / Analytics Engineer
Purpose: Execute verified, deterministic business metric calculations,
         time-series monthly trends, and statistical anomaly detection.
         Supports both PostgreSQL and in-memory SQLite (for zero-dependency local testing).
"""

import os
import csv
import sqlite3
import json
import math
from typing import Dict, List, Any, Optional
from datetime import datetime

# Optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class SalesAnalyticsEngine:
    """
    Analytical engine that processes e-commerce sales data,
    computes key performance indicators (KPIs), trends, and anomalies.
    """

    ALLOWED_INTENTS = {
        "overall_summary": "1. Overall business performance summary (Revenue, Cost, Profit, AOV, Margin)",
        "top_products": "2. Top performing products ranked by revenue and profit",
        "underperforming_products": "3. Underperforming products with low or negative profit margins",
        "category_performance": "4. Sales, profit, and volume breakdown by product category",
        "city_performance": "5. Geographic performance breakdown by customer city",
        "monthly_trend": "6. Monthly revenue and profit trends with Month-over-Month (MoM) growth %",
        "anomaly_detection": "7. Statistical anomaly detection flagging unusual revenue deviations",
        "filtered_query": "8. Filtered analytics by date range and/or category"
    }

    def __init__(self, csv_path: Optional[str] = None, db_conn=None):
        self.csv_path = csv_path
        self.conn = db_conn or sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initializes database schema and loads CSV data into SQLite."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ecommerce_sales (
                order_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                sales REAL NOT NULL,
                cost REAL NOT NULL,
                profit REAL NOT NULL,
                customer_id TEXT NOT NULL
            );
        """)
        self.conn.commit()

        if self.csv_path and os.path.exists(self.csv_path):
            self._load_csv(self.csv_path)

    def _load_csv(self, file_path: str):
        """Loads records from CSV into SQLite."""
        cursor = self.conn.cursor()
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = []
            for r in reader:
                records.append((
                    r["order_id"].strip(),
                    r["order_date"].strip(),
                    r["product_name"].strip(),
                    r["category"].strip(),
                    r["city"].strip(),
                    int(r["quantity"]),
                    float(r["sales"]),
                    float(r["cost"]),
                    float(r["profit"]),
                    r["customer_id"].strip()
                ))
            cursor.executemany("""
                INSERT OR REPLACE INTO ecommerce_sales 
                (order_id, order_date, product_name, category, city, quantity, sales, cost, profit, customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            self.conn.commit()

    def get_overall_summary(self) -> Dict[str, Any]:
        """
        Calculates high-level business KPIs:
        - Total Orders
        - Total Units Sold
        - Total Revenue
        - Total Cost
        - Total Profit
        - Overall Profit Margin (%) = (Profit / Revenue) * 100
        - Average Order Value (AOV) = Revenue / Total Orders
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(order_id) AS total_orders,
                COALESCE(SUM(quantity), 0) AS total_units_sold,
                ROUND(COALESCE(SUM(sales), 0.0), 2) AS total_revenue,
                ROUND(COALESCE(SUM(cost), 0.0), 2) AS total_cost,
                ROUND(COALESCE(SUM(profit), 0.0), 2) AS total_profit,
                ROUND((COALESCE(SUM(profit), 0.0) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS overall_profit_margin_pct,
                ROUND(AVG(sales), 2) AS average_order_value
            FROM ecommerce_sales;
        """)
        row = dict(cursor.fetchone())
        return row

    def get_top_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies top-performing products ranked by total revenue."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                product_name,
                category,
                COUNT(order_id) AS order_count,
                SUM(quantity) AS units_sold,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS profit_margin_pct
            FROM ecommerce_sales
            GROUP BY product_name, category
            ORDER BY total_revenue DESC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

    def get_underperforming_products(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies underperforming products ranked by lowest or negative total profit."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                product_name,
                category,
                SUM(quantity) AS units_sold,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS profit_margin_pct
            FROM ecommerce_sales
            GROUP BY product_name, category
            ORDER BY total_profit ASC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

    def get_category_performance(self) -> List[Dict[str, Any]]:
        """Breaks down revenue, profit, volume, and profit margin by product category."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                category,
                COUNT(order_id) AS total_orders,
                SUM(quantity) AS total_quantity,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS profit_margin_pct
            FROM ecommerce_sales
            GROUP BY category
            ORDER BY total_revenue DESC;
        """)
        return [dict(r) for r in cursor.fetchall()]

    def get_city_performance(self) -> List[Dict[str, Any]]:
        """Analyzes sales performance across cities."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                city,
                COUNT(order_id) AS total_orders,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS profit_margin_pct
            FROM ecommerce_sales
            GROUP BY city
            ORDER BY total_revenue DESC;
        """)
        return [dict(r) for r in cursor.fetchall()]

    def get_monthly_trend(self) -> List[Dict[str, Any]]:
        """
        Computes monthly revenue, profit, and Month-over-Month (MoM) growth %
        using SQL window functions (LAG).
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            WITH monthly_metrics AS (
                SELECT 
                    substr(order_date, 1, 7) AS sales_month,
                    COUNT(order_id) AS order_count,
                    ROUND(SUM(sales), 2) AS monthly_revenue,
                    ROUND(SUM(profit), 2) AS monthly_profit
                FROM ecommerce_sales
                GROUP BY substr(order_date, 1, 7)
            )
            SELECT 
                sales_month,
                order_count,
                monthly_revenue,
                monthly_profit,
                ROUND(
                    ((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY sales_month)) 
                    / NULLIF(LAG(monthly_revenue) OVER (ORDER BY sales_month), 0.0)) * 100.0, 
                    2
                ) AS mom_revenue_growth_pct
            FROM monthly_metrics
            ORDER BY sales_month ASC;
        """)
        return [dict(r) for r in cursor.fetchall()]

    def detect_anomalies(self, threshold_std: float = 0.5) -> List[Dict[str, Any]]:
        """
        Statistical anomaly detection:
        Calculates mean monthly revenue and standard deviation.
        Flags months deviating beyond threshold * std_dev as HIGH_OUTLIER or LOW_OUTLIER.
        """
        monthly = self.get_monthly_trend()
        if not monthly:
            return []

        revenues = [m["monthly_revenue"] for m in monthly]
        avg_revenue = sum(revenues) / len(revenues)
        
        # Population / sample standard deviation
        if len(revenues) > 1:
            variance = sum((x - avg_revenue) ** 2 for x in revenues) / (len(revenues) - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0

        anomalies = []
        for m in monthly:
            rev = m["monthly_revenue"]
            deviation_pct = ((rev - avg_revenue) / avg_revenue) * 100.0 if avg_revenue else 0.0
            
            flag = "NORMAL"
            if std_dev > 0:
                if rev > (avg_revenue + threshold_std * std_dev):
                    flag = "HIGH_OUTLIER"
                elif rev < (avg_revenue - threshold_std * std_dev):
                    flag = "LOW_OUTLIER"

            anomalies.append({
                "sales_month": m["sales_month"],
                "monthly_revenue": rev,
                "monthly_profit": m["monthly_profit"],
                "avg_monthly_revenue": round(avg_revenue, 2),
                "std_monthly_revenue": round(std_dev, 2),
                "deviation_from_avg_pct": round(deviation_pct, 2),
                "anomaly_flag": flag
            })
        return anomalies

    def get_filtered_analysis(self, start_date: Optional[str] = None, 
                              end_date: Optional[str] = None, 
                              category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Safe parameterized analytics query allowing date range and category filtering.
        Eliminates SQL injection through strict parameter substitution.
        """
        query = """
            SELECT 
                category,
                COUNT(order_id) AS order_count,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0.0)) * 100.0, 2) AS profit_margin_pct
            FROM ecommerce_sales
            WHERE (? IS NULL OR order_date >= ?)
              AND (? IS NULL OR order_date <= ?)
              AND (? IS NULL OR category = ?)
            GROUP BY category
            ORDER BY total_revenue DESC;
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (start_date, start_date, end_date, end_date, category, category))
        return [dict(r) for r in cursor.fetchall()]

    def run_analysis_by_intent(self, intent: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Central dispatch method mapping an allowlisted intent to verified SQL results.
        """
        params = params or {}
        if intent not in self.ALLOWED_INTENTS:
            return {
                "status": "error",
                "message": f"Unauthorized intent '{intent}'. Allowed intents: {list(self.ALLOWED_INTENTS.keys())}",
                "data": []
            }

        if intent == "overall_summary":
            data = self.get_overall_summary()
        elif intent == "top_products":
            limit = int(params.get("limit", 5))
            data = self.get_top_products(limit=limit)
        elif intent == "underperforming_products":
            limit = int(params.get("limit", 5))
            data = self.get_underperforming_products(limit=limit)
        elif intent == "category_performance":
            data = self.get_category_performance()
        elif intent == "city_performance":
            data = self.get_city_performance()
        elif intent == "monthly_trend":
            data = self.get_monthly_trend()
        elif intent == "anomaly_detection":
            threshold = float(params.get("threshold", 0.5))
            data = self.detect_anomalies(threshold_std=threshold)
        elif intent == "filtered_query":
            data = self.get_filtered_analysis(
                start_date=params.get("start_date"),
                end_date=params.get("end_date"),
                category=params.get("category")
            )
        else:
            data = []

        return {
            "status": "success",
            "intent": intent,
            "description": self.ALLOWED_INTENTS[intent],
            "data": data
        }


def format_business_report(engine: SalesAnalyticsEngine) -> str:
    """Generates an executive summary report for business stakeholders."""
    summary = engine.get_overall_summary()
    top_prods = engine.get_top_products(3)
    worst_prods = engine.get_underperforming_products(2)
    categories = engine.get_category_performance()
    cities = engine.get_city_performance()
    anomalies = engine.detect_anomalies()

    report = []
    report.append("=" * 70)
    report.append("               EXECUTIVE E-COMMERCE BUSINESS REPORT")
    report.append("=" * 70)
    report.append("1. EXECUTIVE SUMMARY (OVERALL KPIs):")
    report.append(f"   - Total Revenue           : ₹{summary['total_revenue']:,.2f}")
    report.append(f"   - Total Cost              : ₹{summary['total_cost']:,.2f}")
    report.append(f"   - Total Profit            : ₹{summary['total_profit']:,.2f}")
    report.append(f"   - Overall Profit Margin   : {summary['overall_profit_margin_pct']}%")
    report.append(f"   - Total Orders Processed  : {summary['total_orders']}")
    report.append(f"   - Average Order Value     : ₹{summary['average_order_value']:,.2f}")
    report.append("-" * 70)

    report.append("2. TOP 3 REVENUE GENERATING PRODUCTS:")
    for idx, p in enumerate(top_prods, 1):
        report.append(f"   {idx}. {p['product_name']} ({p['category']}): "
                      f"Revenue ₹{p['total_revenue']:,.2f} | Profit ₹{p['total_profit']:,.2f} "
                      f"({p['profit_margin_pct']}%)")
    report.append("-" * 70)

    report.append("3. UNDERPERFORMING PRODUCTS (ATTENTION REQUIRED):")
    for idx, p in enumerate(worst_prods, 1):
        report.append(f"   {idx}. {p['product_name']} ({p['category']}): "
                      f"Revenue ₹{p['total_revenue']:,.2f} | Profit ₹{p['total_profit']:,.2f} "
                      f"({p['profit_margin_pct']}%)")
    report.append("-" * 70)

    report.append("4. CATEGORY BREAKDOWN:")
    for c in categories:
        report.append(f"   - {c['category']:<16}: Revenue ₹{c['total_revenue']:>10,.2f} | "
                      f"Profit ₹{c['total_profit']:>9,.2f} | Margin {c['profit_margin_pct']:>5.2f}%")
    report.append("-" * 70)

    report.append("5. TOP 3 MARKETS (CITIES):")
    for c in cities[:3]:
        report.append(f"   - {c['city']:<12}: Revenue ₹{c['total_revenue']:>10,.2f} | Profit ₹{c['total_profit']:>9,.2f}")
    report.append("-" * 70)

    report.append("6. STATISTICAL ANOMALY & TREND HIGHLIGHTS:")
    for a in anomalies:
        if a["anomaly_flag"] != "NORMAL":
            report.append(f"   - [ALERT] {a['sales_month']}: Revenue ₹{a['monthly_revenue']:,.2f} "
                          f"({a['deviation_from_avg_pct']:+.1f}% vs avg) -> Flag: {a['anomaly_flag']}")
    report.append("=" * 70)
    return "\n".join(report)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base_dir, "data", "sample_sales.csv")

    engine = SalesAnalyticsEngine(csv_path=target_csv)
    print(format_business_report(engine))
