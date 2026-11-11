"""Baseline: imports successfully but one meaningful behavioral test fails."""

from decimal import Decimal
import unittest

from receipt_calculator import ProductEntry, format_rupiah, grand_total


class StarterReceiptTests(unittest.TestCase):
    def test_single_unit_format(self) -> None:
        entry = ProductEntry("onions", "1", "43000", "kg")
        self.assertEqual(format_rupiah(entry.line_total), "Rp43,000")

    def test_multiple_product_quantities(self) -> None:
        entries = [ProductEntry("rice", "2", "30000", "kg"),
                   ProductEntry("onions", "1", "43000", "kg")]
        self.assertEqual(grand_total(entries), Decimal("103000"))


if __name__ == "__main__":
    unittest.main()
