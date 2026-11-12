"""Independent Tester checks using Fraction as a separate arithmetic oracle."""
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "demo/receipt"))
from receipt_calculator import ProductEntry, grand_total, format_rupiah

PROGRAM = ROOT / "demo/receipt/receipt_calculator.py"


class IndependentReceiptChecks(unittest.TestCase):
    def test_exact_boundary_products_and_sums_using_rational_oracle(self):
        values = [
            ("999999999999999999.999999999999", "999999999999999999.999999999999"),
            ("0.000000000001", "0.000000000001"),
            ("0.1", "0.2"),
            ("1.123456789012", "345678901234567890.000000000001"),
        ]
        with localcontext() as ctx:
            ctx.prec = 2
            entries = [ProductEntry("independent", q, p) for q, p in values]
            for entry, (q, p) in zip(entries, values):
                self.assertIsInstance(entry.quantity, Decimal)
                self.assertIsInstance(entry.unit_price, Decimal)
                self.assertIsInstance(entry.line_total, Decimal)
                self.assertEqual(Fraction(entry.line_total), Fraction(q) * Fraction(p))
            self.assertEqual(Fraction(grand_total(iter(entries))), sum((Fraction(q) * Fraction(p) for q, p in values), Fraction(0)))
        self.assertEqual(format_rupiah(entries[1].line_total), "Rp0.000000000000000000000001")

    def test_deterministic_independent_receipt_oracle(self):
        rng = random.Random(431)
        values = [(f"{rng.randrange(100000)}.{rng.randrange(1000000):06}",
                   f"{rng.randrange(1000000)}.{rng.randrange(1000000):06}") for _ in range(73)]
        entries = [ProductEntry(f"product-{n}", q, p, "each") for n, (q, p) in enumerate(values)]
        for entry, (q, p) in zip(entries, values):
            self.assertEqual(Fraction(entry.line_total), Fraction(q) * Fraction(p))
        self.assertEqual(Fraction(grand_total(entries)), sum((Fraction(q) * Fraction(p) for q, p in values), Fraction(0)))

    def test_rejected_out_of_bounds_and_unsafe_api_values(self):
        for value in ["1000000000000000000", "0.0000000000001", "NaN", "sNaN", "Infinity", "-Infinity", "-0.01", "1,000", "Rp20", "1e2", "oops", "", True, 0.1, Decimal("NaN")]:
            for field in ["quantity", "price"]:
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    ProductEntry("x", value if field == "quantity" else "1", value if field == "price" else "1")
        self.assertEqual(grand_total([ProductEntry("zero", "0", "2"), ProductEntry("free", "8", "0")]), Decimal(0))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(PROGRAM), *args], capture_output=True, text=True, check=False)

    def test_actual_sample_alternate_and_fractional_receipts(self):
        cases = [
            (["--item", "rice", "2", "30000", "kg", "--item", "onions", "1", "43000", "kg"], "2 kg rice × Rp30,000 = Rp60,000\n1 kg onions × Rp43,000 = Rp43,000\nTotal = Rp103,000\n"),
            (["--item", "paper clips", "7", "1200.75", "box", "--item", "notebook", "2.5", "13000.125", "each"], "7 box paper clips × Rp1,200.75 = Rp8,405.25\n2.5 each notebook × Rp13,000.125 = Rp32,500.3125\nTotal = Rp40,905.5625\n"),
            (["--item", "tiny", "0.000000000001", "0.000000000001", "each"], "0.000000000001 each tiny × Rp0.000000000001 = Rp0.000000000000000000000001\nTotal = Rp0.000000000000000000000001\n"),
        ]
        for args, expected in cases:
            result = self.cli(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, expected)

    def test_user_errors_and_help(self):
        invalid = [[], ["--item", "rice", "1"], ["--item", "", "1", "2", "each"], ["--item", "rice", "1", "2", " "]]
        for value in ["-1", "NaN", "Infinity", "-Infinity", "bad", "1,000", "Rp100", "0.0000000000001"]:
            invalid.extend([["--item", "rice", value, "2", "kg"], ["--item", "rice", "2", value, "kg"]])
        for args in invalid:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")
        help_result = self.cli("--help")
        self.assertEqual(help_result.returncode, 0)
        for required in ["--item", "NAME", "QUANTITY", "UNIT_PRICE", "UNIT", "plain decimals", "18 integer", "12 fractional"]:
            self.assertIn(required, help_result.stdout)


if __name__ == "__main__":
    unittest.main()
