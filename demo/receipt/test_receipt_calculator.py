"""Executable behavioral checks for the finished program, not the starter."""

from decimal import Decimal, Clamped, Inexact, Rounded, Subnormal, localcontext
from pathlib import Path
import subprocess
import sys
import unittest

from receipt_calculator import ProductEntry, format_rupiah, grand_total


PROGRAM = Path(__file__).with_name("receipt_calculator.py")


class ArithmeticTests(unittest.TestCase):
    def test_owner_sample(self) -> None:
        entries = [ProductEntry("rice", "2", "30000", "kg"),
                   ProductEntry("onions", "1", "43000", "kg")]
        self.assertEqual([entry.line_total for entry in entries], [Decimal("60000"), Decimal("43000")])
        self.assertEqual(grand_total(entries), Decimal("103000"))

    def test_different_receipt(self) -> None:
        entries = [ProductEntry("tea", "3", "12500", "box"),
                   ProductEntry("sugar", "1.5", "14000", "kg")]
        self.assertEqual(grand_total(entries), Decimal("58500"))

    def test_exact_fraction_and_display(self) -> None:
        self.assertEqual(ProductEntry("fraction", "0.1", "0.2").line_total, Decimal("0.02"))
        value = ProductEntry("fraction", "0.123456789012", "0.234567890123").line_total
        self.assertEqual(value, Decimal("0.028958998519905209728476"))
        self.assertEqual(format_rupiah(value), "Rp0.028958998519905209728476")
        self.assertEqual(format_rupiah(Decimal("103000.00")), "Rp103,000")

    def test_context_independence_and_large_sum(self) -> None:
        entries = [ProductEntry("large", "999999999999999999", "999999999999999999") for _ in range(11)]
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(grand_total(entries), Decimal("10999999999999999978000000000000000011"))

    def test_zero_and_generator(self) -> None:
        entries = (ProductEntry("free", value, "0") for value in ["0", "100"])
        self.assertEqual(grand_total(entries), Decimal(0))
        self.assertEqual(grand_total([]), Decimal(0))
        self.assertEqual(format_rupiah(Decimal("-0.00")), "Rp0")

    def test_restrictive_ambient_exponent_context_does_not_change_exact_arithmetic(self) -> None:
        with localcontext() as context:
            context.prec = 2
            context.Emax = 3
            context.Emin = -3
            context.clamp = 1
            for signal in (Clamped, Inexact, Rounded, Subnormal):
                context.traps[signal] = True
            before = context.copy()
            large = ProductEntry("large", "999999999999999999", "999999999999999999")
            small = ProductEntry("small", "0.000000000001", "0.000000000001")
            self.assertEqual(large.line_total, Decimal("999999999999999998000000000000000001"))
            self.assertEqual(small.line_total, Decimal("0.000000000000000000000001"))
            self.assertEqual(grand_total([large, small]),
                             Decimal("999999999999999998000000000000000001.000000000000000000000001"))
            self.assertEqual((context.prec, context.Emax, context.Emin, context.clamp),
                             (before.prec, before.Emax, before.Emin, before.clamp))
            self.assertEqual(context.traps, before.traps)
            self.assertEqual(context.flags, before.flags)

    def test_reject_invalid_numbers(self) -> None:
        for value in ["-1", "NaN", "sNaN", "Infinity", "-Infinity", "abc", "Rp100", "1,000", "1e3", "", "1000000000000000000", "0.0000000000001", 0.1, True]:
            with self.subTest(value=value, field="quantity"), self.assertRaises(ValueError):
                ProductEntry("rice", value, "1")
            with self.subTest(value=value, field="price"), self.assertRaises(ValueError):
                ProductEntry("rice", "1", value)
        for value in [Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("1E+1000000")]:
            with self.subTest(decimal=value), self.assertRaises(ValueError):
                ProductEntry("rice", "1", value)

    def test_reject_blank_and_control_labels(self) -> None:
        for name, unit in [("", "kg"), ("  ", "kg"), ("rice", "  "), ("rice\nTotal", "kg"), ("rice", "kg\t")]:
            with self.subTest(name=name, unit=unit), self.assertRaises(ValueError):
                ProductEntry(name, "1", "100", unit)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(PROGRAM), *arguments], text=True, capture_output=True, check=False)

    def test_version(self) -> None:
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1.0.0\n")

    def test_sample_cli(self) -> None:
        result = self.run_cli("--item", "rice", "2", "30000", "kg", "--item", "onions", "1", "43000", "kg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "2 kg rice × Rp30,000 = Rp60,000\n1 kg onions × Rp43,000 = Rp43,000\nTotal = Rp103,000\n")

    def test_fractional_and_zero_cli(self) -> None:
        result = self.run_cli("--item", "tiny", "0.1", "0.2", "each", "--item", "free", "2", "0", "each")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Total = Rp0.02", result.stdout)

    def test_errors_are_concise_without_traceback(self) -> None:
        arguments = [[], ["--item", "rice", "2"], ["--item", "rice", "-1", "10", "kg"],
                     ["--item", "rice", "1", "NaN", "kg"], ["--item", "rice", "1", "-Infinity", "kg"],
                     ["--item", "rice", "bad", "10", "kg"], ["--item", "rice", "1", "1,000", "kg"],
                     ["--item", "rice", "1", "10", ""]]
        for args in arguments:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_help(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for expected in ["--item", "QUANTITY", "UNIT_PRICE", "UNIT", "plain decimals", "18 integer", "12 fractional"]:
            self.assertIn(expected, result.stdout)


if __name__ == "__main__":
    unittest.main()
