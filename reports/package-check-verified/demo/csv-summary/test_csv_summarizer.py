"""Behavioral tests for the local, read-only CSV summarizer."""

import csv
from decimal import localcontext
import errno
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from csv_summarizer import SummaryError, summarize


PROGRAM = Path(__file__).with_name("csv_summarizer.py")


class CSVSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.area = tempfile.TemporaryDirectory(prefix="test-csv-", dir=PROGRAM.parent)
        self.addCleanup(self.area.cleanup)
        self.source = Path(self.area.name) / "input.csv"

    def write(self, text: str | bytes) -> None:
        self.source.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        before = self.source.read_bytes() if self.source.is_file() else None
        result = subprocess.run([sys.executable, str(PROGRAM), *arguments], capture_output=True, text=True)
        if before is not None:
            self.assertEqual(self.source.read_bytes(), before)
        return result

    def invalid(self, content: str | bytes, *expected: str, columns: tuple[str, ...] = ("amount",)) -> None:
        self.write(content)
        args = [str(self.source)]
        for name in columns:
            args.extend(["--column", name])
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(str(self.source), result.stderr)
        for text in expected:
            self.assertIn(text, result.stderr)

    def test_sample_and_reversed_order(self) -> None:
        sample = PROGRAM.with_name("sample.csv")
        before = sample.read_bytes()
        result = self.run_cli(str(sample), "--column", "amount", "--column", "quantity")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Rows: 3\nTotal amount: 30\nTotal quantity: 6\n")
        self.assertEqual(sample.read_bytes(), before)
        result = self.run_cli(str(sample), "--column", "quantity", "--column", "amount")
        self.assertEqual(result.stdout, "Rows: 3\nTotal quantity: 6\nTotal amount: 30\n")

    def test_different_signed_fractional_data(self) -> None:
        self.write("description,amount,units\na, +.25 ,2\nb,1.,-1\nc,-.125,0\n,0.000000000001,3\n")
        result = summarize(self.source, ["units", "amount"])
        self.assertEqual(result.rows, 4)
        self.assertEqual(result.totals, (("units", "4"), ("amount", "1.125000000001")))

    def test_exact_accumulation_beyond_input_limits_and_low_context(self) -> None:
        self.write("amount\n999999999999999999.999999999999\n999999999999999999.999999999999\n.000000000001\n")
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(summarize(self.source, ["amount"]).totals,
                             (("amount", "1999999999999999999.999999999999"),))

    def test_zero_and_canonical_format(self) -> None:
        self.write("amount\n-0.00\n+0\n-1.5000\n+1.5\n")
        self.assertEqual(summarize(self.source, ["amount"]).totals, (("amount", "0"),))

    def test_numeric_rejections(self) -> None:
        values = ["", " ", "NaN", "sNaN", "Infinity", "-Infinity", "1e3", "1_000", "1,000",
                  "Rp1", "one", "+", ".", "--1", "١", "1000000000000000000",
                  "0000000000000000000", "0.0000000000001", "1.0000000000000"]
        for value in values:
            with self.subTest(value=value):
                self.write("description,amount\nvalid,2\n")
                with self.source.open("a", newline="", encoding="utf-8") as stream:
                    csv.writer(stream).writerow(["bad", value])
                result = self.run_cli(str(self.source), "--column", "amount")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                for text in [str(self.source), "record 3", "column 'amount'"]:
                    self.assertIn(text, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_normalized_headers_and_header_only(self) -> None:
        self.write(" description , amount \n")
        result = self.run_cli(str(self.source), "--column", "amount")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Rows: 0\nTotal amount: 0\n")

    def test_bad_headers_and_selections(self) -> None:
        for content, expected in [("", "missing CSV header"), (b"\xef\xbb\xbf", "missing CSV header"),
                                  ("\n", "missing CSV header"), ("description, \n", "blank"),
                                  ("amount, amount \n", "duplicate normalized"),
                                  ('"amo\nunt"\n1\n', "control character"),
                                  ("\tamount\n1\n", "control character")]:
            with self.subTest(content=content):
                self.invalid(content, expected)
        self.invalid("amount\n1\n", "not in the header", columns=("Amount",))
        self.invalid("amount\n1\n", "duplicate requested", columns=("amount", "amount"))
        self.invalid("amount\n1\n", "not in the header", columns=("",))

    def test_ragged_and_blank_records(self) -> None:
        for data, count in [("description,amount\na\n", "found 1"),
                            ("description,amount\na,1,extra\n", "found 3"),
                            ("description,amount\n\n", "found 0")]:
            with self.subTest(data=data):
                self.invalid(data, "record 2", "expected 2 fields", count)

    def test_malformed_quotes(self) -> None:
        for data in ['description,amount\n"unfinished,2\n', 'description,amount\n"closed"junk,2\n']:
            with self.subTest(data=data):
                self.invalid(data, "CSV parsing error", "physical line")

    def test_bom_unicode_crlf_quoted_commas_quotes_and_multiline(self) -> None:
        self.write('\ufeffdescription,amount\r\n"café, tea",1.25\r\n"she said ""hi""",2\r\n"two\r\nlines",-.25\r\n')
        result = self.run_cli(str(self.source), "--column", "amount")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Rows: 3\nTotal amount: 3\n")

    def test_multiline_descriptors_do_not_change_logical_error_record(self) -> None:
        self.invalid('description,amount\n"two\nlines",1\nbad,oops\n', "record 3", "column 'amount'")

    def test_invalid_utf8(self) -> None:
        self.invalid(b"description,amount\n\xff,2\n", "invalid UTF-8")

    def test_read_errors_and_no_selection_api(self) -> None:
        for target in [self.source, Path(self.area.name)]:
            with self.subTest(target=target):
                result = self.run_cli(str(target), "--column", "amount")
                self.assertEqual(result.returncode, 2)
                self.assertIn(str(target), result.stderr)
                self.assertIn("cannot read input", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")
        with patch.object(Path, "open", side_effect=PermissionError(errno.EACCES, "Permission denied")):
            with self.assertRaisesRegex(SummaryError, "Permission denied"):
                summarize(self.source, ["amount"])
        with self.assertRaisesRegex(SummaryError, "at least one"):
            summarize(self.source, [])

    def test_help_and_required_arguments(self) -> None:
        help_result = self.run_cli("--help")
        self.assertEqual(help_result.returncode, 0)
        for text in ["--column", "INPUT", "UTF-8", "18 integer", "12 fractional", "offline"]:
            self.assertIn(text, help_result.stdout)
        for args in [(), (str(self.source),), ("--column", "amount")]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("required", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_api_read_only_on_success_and_failure(self) -> None:
        for content in ["amount\n1.25\n", "amount\nnot-a-number\n"]:
            self.write(content)
            before = self.source.read_bytes()
            try:
                summarize(self.source, ["amount"])
            except SummaryError:
                pass
            self.assertEqual(self.source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
