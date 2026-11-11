"""Independent contract checks using rational arithmetic and real CLI subprocesses."""

import csv
from decimal import localcontext
from fractions import Fraction
import io
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "demo/csv-summary/csv_summarizer.py"
sys.path.insert(0, str(PROGRAM.parent))
from csv_summarizer import summarize


class IndependentCSVChecks(unittest.TestCase):
    def setUp(self):
        self.area = tempfile.TemporaryDirectory(prefix="independent-", dir=Path(__file__).parent)
        self.addCleanup(self.area.cleanup)
        self.source = Path(self.area.name) / "fixture.csv"

    def write(self, data):
        self.source.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))

    def run_cli(self, columns=("amount",), target=None):
        target = self.source if target is None else target
        before = target.read_bytes() if target.is_file() else None
        command = [sys.executable, str(PROGRAM), str(target)]
        for name in columns:
            command.extend(["--column", name])
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if before is not None:
            self.assertEqual(target.read_bytes(), before, "Input bytes changed")
        return result

    def assert_invalid(self, data, *context, columns=("amount",)):
        self.write(data)
        result = self.run_cli(columns)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "", "Invalid input produced a partial summary")
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(str(self.source), result.stderr)
        for snippet in context:
            self.assertIn(snippet, result.stderr)

    def test_independent_rational_totals_at_bounds_and_many_records(self):
        rng = random.Random(7281)
        rows = [
            ("maximum", "999999999999999999.999999999999", "1"),
            ("maximum again", "999999999999999999.999999999999", "1"),
            ("tiny", "+.000000000001", "-.000000000001"),
            ("cancellation", "-999999999999999999.999999999999", "-2"),
            ("zero", "-0.000000000000", "+0"),
            ("fraction", ".25", "1."),
        ]
        for n in range(137):
            sign = "-" if rng.randrange(2) else "+"
            amount = f"{sign}{rng.randrange(10**17)}.{rng.randrange(10**12):012d}"
            quantity = f"{rng.randrange(10**12)}.{rng.randrange(10**8):08d}"
            rows.append((f"product {n}", amount, quantity))
        content = io.StringIO(newline="")
        writer = csv.writer(content, lineterminator="\n")
        writer.writerow(["description", "amount", "quantity"])
        writer.writerows(rows)
        self.write(content.getvalue())
        before = self.source.read_bytes()
        with localcontext() as context:
            context.prec = 1
            result = summarize(self.source, ["quantity", "amount"])
        self.assertEqual(result.rows, len(rows))
        self.assertEqual([name for name, _ in result.totals], ["quantity", "amount"])
        expected = {
            "amount": sum((Fraction(row[1]) for row in rows), Fraction(0)),
            "quantity": sum((Fraction(row[2]) for row in rows), Fraction(0)),
        }
        for name, total in result.totals:
            self.assertEqual(Fraction(total), expected[name])
            self.assertNotIn("e", total.lower())
            if "." in total:
                self.assertFalse(total.endswith("0"))
            self.assertNotEqual(total, "-0")
        self.assertEqual(self.source.read_bytes(), before)
        live = self.run_cli(("quantity", "amount"))
        self.assertEqual(live.returncode, 0, live.stderr)
        lines = live.stdout.splitlines()
        self.assertEqual(lines[0], f"Rows: {len(rows)}")
        self.assertEqual(Fraction(lines[1].removeprefix("Total quantity: ")), expected["quantity"])
        self.assertEqual(Fraction(lines[2].removeprefix("Total amount: ")), expected["amount"])

    def test_utf8_bom_crlf_multiline_quotes_and_requested_order(self):
        content = io.StringIO(newline="")
        writer = csv.writer(content, lineterminator="\r\n")
        writer.writerow([" description ", " amount ", "quantity"])
        writer.writerows([
            ["kopi, café", " +1.25 ", "2"],
            ['she said "tea"\r\nnext line', "-.125", "-1"],
            ["", ".000000000001", "-0.0000"],
        ])
        self.write(b"\xef\xbb\xbf" + content.getvalue().encode("utf-8"))
        live = self.run_cli(("quantity", "amount"))
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(live.stdout, "Rows: 3\nTotal quantity: 1\nTotal amount: 1.125000000001\n")

    def test_headers_selections_and_header_only_records(self):
        cases = [
            ("", "header"),
            (b"\xef\xbb\xbf", "header"),
            ("\n", "header"),
            ("note,   \n", "blank"),
            ("amount, amount \n", "duplicate"),
            ('"amount\n"\n1\n', "control"),
            ("\tamount\n1\n", "control"),
            ("amount\x00\n1\n", "control"),
        ]
        for data, expected in cases:
            with self.subTest(data=data):
                self.assert_invalid(data, expected)
        for selection, expected in [(("missing",), "not in the header"), (("Amount",), "not in the header"), (("amount", "amount"), "duplicate requested")]:
            with self.subTest(selection=selection):
                self.assert_invalid("note,amount,quantity\n", expected, columns=selection)
        self.write(" note , amount ,quantity\r\n")
        live = self.run_cli(("quantity", "amount"))
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(live.stdout, "Rows: 0\nTotal quantity: 0\nTotal amount: 0\n")

    def test_late_bad_numeric_cells_never_emit_partial_summary(self):
        invalid = ["", " ", "NaN", "sNaN", "Inf", "-Infinity", "+NaN", "1e0", "1_2", "1,000", "Rp1", "1/2", ".", "+", "--1", "١", "０", "1234567890123456789", "0000000000000000000", "0.0000000000001", "1.0000000000000"]
        for value in invalid:
            with self.subTest(value=value):
                content = io.StringIO(newline="")
                writer = csv.writer(content, lineterminator="\n")
                writer.writerow(["note", "amount"])
                writer.writerow(["valid", "1.25"])
                writer.writerow(["invalid", value])
                self.assert_invalid(content.getvalue(), "record 3", "column 'amount'")

    def test_shape_quotes_and_logical_record_error_context(self):
        for bad in ["too short\n", "extra,1,2\n", "\n"]:
            with self.subTest(bad=bad):
                self.assert_invalid('note,amount\n"first\nrecord",2\n' + bad, "record 3", "expected 2 fields")
        self.assert_invalid('note,amount\n"first\nrecord",2\nbad,wrong\n', "record 3", "column 'amount'")
        for bad in ['"unfinished,2\n', '"closed"junk,2\n']:
            with self.subTest(quoting=bad):
                self.assert_invalid("note,amount\nvalid,1\n" + bad, "CSV parsing error", "physical line")

    def test_encoding_file_errors_help_and_required_arguments(self):
        self.assert_invalid(b"note,amount\ngood,1\n\xff,2\n", "UTF-8")
        for target in [Path(self.area.name), Path(self.area.name) / "missing.csv"]:
            with self.subTest(target=target):
                result = self.run_cli(target=target)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(str(target), result.stderr)
                self.assertNotIn("Traceback", result.stderr)
        result = subprocess.run([sys.executable, str(PROGRAM), "--help"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        for text in ["INPUT", "--column", "UTF-8", "18 integer", "12 fractional", "offline"]:
            self.assertIn(text, result.stdout)
        for tail in [[], [str(self.source)], ["--column", "amount"]]:
            with self.subTest(arguments=tail):
                result = subprocess.run([sys.executable, str(PROGRAM), *tail], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn("required", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
