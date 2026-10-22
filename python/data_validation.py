"""
data_validation.py
Data Quality & Business Rule Validation for E-commerce Sales Dataset.

Role: Analytics Engineer / Senior Data Analyst
Purpose: Ensure raw business data meets schema constraints, referential integrity,
         and accounting logic before being ingested into PostgreSQL.
"""

import sys
import os
import csv
from datetime import datetime

# Attempt to import pandas if installed, else fallback to standard library
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "product_name",
    "category",
    "city",
    "quantity",
    "sales",
    "cost",
    "profit",
    "customer_id"
]


def validate_csv(file_path):
    """
    Validates CSV data against strict schema, data type, and business logic rules.
    Returns a dict with validation status, metrics, and error logs.
    """
    if not os.path.exists(file_path):
        return {
            "is_valid": False,
            "errors": [f"File not found: {file_path}"],
            "metrics": {}
        }

    errors = []
    warnings = []
    seen_order_ids = set()
    
    total_rows = 0
    total_sales = 0.0
    total_cost = 0.0
    total_profit = 0.0
    distinct_categories = set()
    distinct_cities = set()
    distinct_products = set()
    distinct_customers = set()
    min_date = None
    max_date = None

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # 1. Header validation
        if not reader.fieldnames:
            return {"is_valid": False, "errors": ["CSV file is completely empty."], "metrics": {}}
        
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_cols:
            return {"is_valid": False, "errors": [f"Missing required columns: {missing_cols}"], "metrics": {}}
        
        # 2. Row by row validation
        for row_idx, row in enumerate(reader, start=2): # 1-indexed, header is line 1
            total_rows += 1
            order_id = row.get("order_id", "").strip()
            order_date_str = row.get("order_date", "").strip()
            product = row.get("product_name", "").strip()
            category = row.get("category", "").strip()
            city = row.get("city", "").strip()
            customer_id = row.get("customer_id", "").strip()
            
            # Check empty fields
            for col in REQUIRED_COLUMNS:
                if not row.get(col, "").strip():
                    errors.append(f"Row {row_idx}: Column '{col}' is null or empty.")

            # Duplicate Primary Key check
            if order_id:
                if order_id in seen_order_ids:
                    errors.append(f"Row {row_idx}: Duplicate order_id '{order_id}'.")
                seen_order_ids.add(order_id)

            # Date format check (YYYY-MM-DD)
            try:
                order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
                if min_date is None or order_date < min_date:
                    min_date = order_date
                if max_date is None or order_date > max_date:
                    max_date = order_date
            except ValueError:
                errors.append(f"Row {row_idx}: Invalid date format '{order_date_str}'. Expected YYYY-MM-DD.")

            # Quantity check
            try:
                qty = int(row.get("quantity", "0"))
                if qty <= 0:
                    errors.append(f"Row {row_idx}: Quantity must be > 0 (got {qty}).")
            except ValueError:
                errors.append(f"Row {row_idx}: Quantity '{row.get('quantity')}' is not a valid integer.")
                qty = 0

            # Financial figures check
            try:
                sales = float(row.get("sales", "0.0"))
                cost = float(row.get("cost", "0.0"))
                profit = float(row.get("profit", "0.0"))

                if sales < 0:
                    errors.append(f"Row {row_idx}: Sales cannot be negative (got {sales}).")
                if cost < 0:
                    errors.append(f"Row {row_idx}: Cost cannot be negative (got {cost}).")

                # Accounting identity check: profit == sales - cost (with tolerance for float rounding)
                expected_profit = round(sales - cost, 2)
                if abs(profit - expected_profit) > 0.02:
                    errors.append(
                        f"Row {row_idx}: Accounting mismatch! Sales ({sales}) - Cost ({cost}) = "
                        f"{expected_profit}, but recorded Profit is {profit}."
                    )

                total_sales += sales
                total_cost += cost
                total_profit += profit

            except ValueError:
                errors.append(f"Row {row_idx}: Non-numeric value found in financial fields.")

            if product:
                distinct_products.add(product)
            if category:
                distinct_categories.add(category)
            if city:
                distinct_cities.add(city)
            if customer_id:
                distinct_customers.add(customer_id)

    overall_margin_pct = (total_profit / total_sales * 100) if total_sales > 0 else 0.0
    aov = (total_sales / total_rows) if total_rows > 0 else 0.0

    metrics = {
        "total_records": total_rows,
        "date_range": f"{min_date} to {max_date}",
        "distinct_products": len(distinct_products),
        "distinct_categories": len(distinct_categories),
        "distinct_cities": len(distinct_cities),
        "distinct_customers": len(distinct_customers),
        "total_sales": round(total_sales, 2),
        "total_cost": round(total_cost, 2),
        "total_profit": round(total_profit, 2),
        "overall_profit_margin_pct": round(overall_margin_pct, 2),
        "average_order_value": round(aov, 2),
        "pandas_accelerated": PANDAS_AVAILABLE
    }

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics
    }


def print_audit_report(result):
    """Prints a structured Data Quality Audit report to stdout."""
    print("=" * 60)
    print("       DATA QUALITY AUDIT & BUSINESS RULE REPORT")
    print("=" * 60)
    if result["is_valid"]:
        print(" STATUS: [PASSED] - Dataset is clean and ready for DB ingestion.")
    else:
        print(f" STATUS: [FAILED] - Found {len(result['errors'])} validation errors.")
    print("-" * 60)
    print("Dataset Profile:")
    for key, val in result["metrics"].items():
        print(f"  - {key.replace('_', ' ').title():<28}: {val}")
    print("-" * 60)
    
    if result["errors"]:
        print("Validation Errors:")
        for err in result["errors"][:10]:
            print(f"  [X] {err}")
        if len(result["errors"]) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors.")
        print("-" * 60)
    print("=" * 60)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_csv = os.path.join(base_dir, "data", "sample_sales.csv")
    
    print(f"Validating: {target_csv}")
    report = validate_csv(target_csv)
    print_audit_report(report)
    
    sys.exit(0 if report["is_valid"] else 1)
