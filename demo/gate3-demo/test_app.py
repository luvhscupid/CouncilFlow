"""Maintained deterministic column-sum checks imported from Gate 3 Run 01."""
from pathlib import Path
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal

APP = Path(os.environ.get("COUNCILFLOW_GATE3_APP", str(Path(__file__).with_name("app.py")))).resolve()
INPUTS = Path(__file__).with_name("inputs")

class ColumnSumTests(unittest.TestCase):
    def cli(self, filename, column):
        return subprocess.run([sys.executable, "-B", str(APP), str(INPUTS / filename), column], capture_output=True, text=True)

    def test_ac1_function(self):
        self.assertEqual(runpy.run_path(str(APP))["sum_column"](INPUTS / "amount.csv", "amount"), 5)

    def test_ac1_cli(self):
        result = self.cli("amount.csv", "amount")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "5")

    def assert_error(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_ac2_missing_column(self):
        result = self.cli("amount.csv", "absent")
        self.assert_error(result)
        self.assertIn("absent", result.stderr)
        self.assertIn("missing", result.stderr.lower())

    def test_ac2_nonnumeric(self):
        result = self.cli("nonnumeric.csv", "amount")
        self.assert_error(result)
        self.assertIn("amount", result.stderr)
        self.assertIn("numeric", result.stderr.lower())

    def test_fractional_and_negative_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            path.write_text("amount\n0.1\n0.2\n-1\n", encoding="utf-8")
            self.assertEqual(runpy.run_path(str(APP))["sum_column"](path, "amount"), Decimal("-0.7"))

    def test_nonfinite_values_are_errors(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "values.csv"
                path.write_text(f"amount\n{value}\n", encoding="utf-8")
                result = subprocess.run([sys.executable, "-B", str(APP), str(path), "amount"], capture_output=True, text=True)
                self.assert_error(result)
                self.assertIn("finite numeric", result.stderr)

    def test_missing_file(self):
        self.assert_error(self.cli("does-not-exist.csv", "amount"))

if __name__ == "__main__":
    unittest.main()
