"""
test_analysis.py
Unit & Integration Tests for Sales Analytics and Data Quality.

Role: Analytics Engineer / Quality Assurance
Purpose: Validate mathematical correctness, schema enforcement,
         statistical anomaly detection, and SQL security allowlisting.
"""

import unittest
import os
import tempfile
import csv
import json
from python.data_validation import validate_csv
from python.analysis import SalesAnalyticsEngine


class TestDataValidation(unittest.TestCase):
    """Tests the data validation and accounting integrity layer."""

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.valid_csv = os.path.join(base_dir, "data", "sample_sales.csv")

    def test_production_csv_validity(self):
        """Ensures that the real sample_sales.csv passes all validation checks."""
        result = validate_csv(self.valid_csv)
        self.assertTrue(result["is_valid"], f"Validation failed with errors: {result['errors']}")
        self.assertEqual(result["metrics"]["total_records"], 60)
        self.assertEqual(result["metrics"]["total_sales"], 1743334.00)
        self.assertEqual(result["metrics"]["total_cost"], 1326600.00)
        self.assertEqual(result["metrics"]["total_profit"], 416734.00)
        self.assertAlmostEqual(result["metrics"]["overall_profit_margin_pct"], 23.90, places=1)

    def test_corrupted_accounting_mismatch(self):
        """Catches accounting discrepancy where profit != sales - cost."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["order_id", "order_date", "product_name", "category", "city",
                             "quantity", "sales", "cost", "profit", "customer_id"])
            # In this row: sales 100, cost 70, expected profit 30, but recorded 999.00
            writer.writerow(["ORD-9999", "2024-01-01", "Test Item", "Electronics", "Bengaluru",
                             "1", "100.00", "70.00", "999.00", "CUST-999"])
            tmp_path = tmp.name

        try:
            result = validate_csv(tmp_path)
            self.assertFalse(result["is_valid"])
            self.assertTrue(any("Accounting mismatch" in err for err in result["errors"]))
        finally:
            os.remove(tmp_path)

    def test_invalid_date_format(self):
        """Catches malformed date strings not matching YYYY-MM-DD."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["order_id", "order_date", "product_name", "category", "city",
                             "quantity", "sales", "cost", "profit", "customer_id"])
            writer.writerow(["ORD-9999", "01/15/2024", "Test Item", "Electronics", "Bengaluru",
                             "1", "100.00", "70.00", "30.00", "CUST-999"])
            tmp_path = tmp.name

        try:
            result = validate_csv(tmp_path)
            self.assertFalse(result["is_valid"])
            self.assertTrue(any("Invalid date format" in err for err in result["errors"]))
        finally:
            os.remove(tmp_path)

    def test_duplicate_primary_key(self):
        """Rejects datasets containing duplicate order_id values."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["order_id", "order_date", "product_name", "category", "city",
                             "quantity", "sales", "cost", "profit", "customer_id"])
            writer.writerow(["ORD-1001", "2024-01-01", "Item A", "Electronics", "Mumbai", "1", "100.00", "60.00", "40.00", "CUST-1"])
            writer.writerow(["ORD-1001", "2024-01-02", "Item B", "Furniture", "Delhi", "2", "200.00", "120.00", "80.00", "CUST-2"])
            tmp_path = tmp.name

        try:
            result = validate_csv(tmp_path)
            self.assertFalse(result["is_valid"])
            self.assertTrue(any("Duplicate order_id" in err for err in result["errors"]))
        finally:
            os.remove(tmp_path)


class TestAnalyticsEngine(unittest.TestCase):
    """Tests analytical queries, business metric formulas, and security allowlist."""

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.valid_csv = os.path.join(base_dir, "data", "sample_sales.csv")
        cls.engine = SalesAnalyticsEngine(csv_path=cls.valid_csv)

    def test_overall_summary_metrics(self):
        """Verifies overall revenue, cost, profit, AOV, and margin calculations."""
        summary = self.engine.get_overall_summary()
        self.assertEqual(summary["total_orders"], 60)
        self.assertEqual(summary["total_units_sold"], 185)
        self.assertEqual(summary["total_revenue"], 1743334.00)
        self.assertEqual(summary["total_cost"], 1326600.00)
        self.assertEqual(summary["total_profit"], 416734.00)
        self.assertAlmostEqual(summary["overall_profit_margin_pct"], 23.90, places=1)
        self.assertAlmostEqual(summary["average_order_value"], 29055.57, places=2)

    def test_top_products_ranking(self):
        """Ensures highest revenue product is Gaming Laptop."""
        top_prods = self.engine.get_top_products(limit=3)
        self.assertEqual(len(top_prods), 3)
        self.assertEqual(top_prods[0]["product_name"], "Gaming Laptop")
        self.assertEqual(top_prods[0]["total_revenue"], 910000.00)
        self.assertEqual(top_prods[0]["total_profit"], 182000.00)

    def test_underperforming_products_detection(self):
        """Identifies Budget Smartwatch as the loss-making product."""
        worst_prods = self.engine.get_underperforming_products(limit=1)
        self.assertEqual(len(worst_prods), 1)
        self.assertEqual(worst_prods[0]["product_name"], "Budget Smartwatch")
        self.assertLess(worst_prods[0]["total_profit"], 0.0, "Expected negative profit for Budget Smartwatch")
        self.assertEqual(worst_prods[0]["total_profit"], -12040.00)

    def test_category_performance_aggregation(self):
        """Verifies category breakdown totals sum to overall totals."""
        cat_data = self.engine.get_category_performance()
        total_cat_revenue = sum(c["total_revenue"] for c in cat_data)
        total_cat_profit = sum(c["total_profit"] for c in cat_data)
        self.assertAlmostEqual(total_cat_revenue, 1743334.00, places=2)
        self.assertAlmostEqual(total_cat_profit, 416734.00, places=2)

    def test_monthly_trend_and_mom_growth(self):
        """Verifies monthly aggregation and LAG-based Month-over-Month calculation."""
        trends = self.engine.get_monthly_trend()
        self.assertEqual(len(trends), 6) # Oct 2023 to Mar 2024
        self.assertIsNone(trends[0]["mom_revenue_growth_pct"]) # First month has no previous month
        # Second month (Nov 2023) growth
        self.assertIsNotNone(trends[1]["mom_revenue_growth_pct"])

    def test_anomaly_detection_outliers(self):
        """Validates statistical anomaly detection correctly identifies Jan dip and Mar peak."""
        anomalies = self.engine.detect_anomalies(threshold_std=0.5)
        flags = {a["sales_month"]: a["anomaly_flag"] for a in anomalies}
        self.assertEqual(flags.get("2024-01"), "LOW_OUTLIER")
        self.assertEqual(flags.get("2024-03"), "HIGH_OUTLIER")

    def test_safe_intent_allowlist_enforcement(self):
        """Blocks arbitrary or unauthorized analysis intents."""
        res_valid = self.engine.run_analysis_by_intent("overall_summary")
        self.assertEqual(res_valid["status"], "success")

        res_invalid = self.engine.run_analysis_by_intent("DROP TABLE ecommerce_sales; --")
        self.assertEqual(res_invalid["status"], "error")
        self.assertIn("Unauthorized intent", res_invalid["message"])


class TestN8nWorkflow(unittest.TestCase):
    """Tests the integrity and validity of the n8n workflow JSON."""

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.workflow_file = os.path.join(base_dir, "n8n", "ai_data_analyst_workflow.json")

    def test_workflow_json_validity(self):
        """Verifies the n8n workflow file exists and parses as valid JSON."""
        self.assertTrue(os.path.exists(self.workflow_file))
        with open(self.workflow_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("nodes", data)
        self.assertIn("connections", data)
        self.assertGreaterEqual(len(data["nodes"]), 6)

    def test_workflow_connections_integrity(self):
        """Ensures every connected node actually exists in the workflow nodes list."""
        with open(self.workflow_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        node_names = {node["name"] for node in data["nodes"]}
        for source_node, connection_info in data["connections"].items():
            self.assertIn(source_node, node_names, f"Source node '{source_node}' in connections not found in nodes.")
            for channel in connection_info.get("main", []):
                for target in channel:
                    self.assertIn(target["node"], node_names, f"Target node '{target['node']}' not found in nodes.")


if __name__ == "__main__":
    unittest.main()

