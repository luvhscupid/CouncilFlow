"""Fresh executable acceptance tests; initially one mandatory test genuinely fails."""
from pathlib import Path
import subprocess
import sys
import unittest

PROGRAM = Path(__file__).with_name("sum_values.py")


class SumValuesTests(unittest.TestCase):
    def run_program(self, *args):
        return subprocess.run([sys.executable, str(PROGRAM), *args], text=True,
                              capture_output=True, check=False)

    def test_multiple_signed_values(self):
        result = self.run_program("2", "3", "-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "4\n")

    def test_single_and_zero(self):
        for value in ("-3", "0", "+12"):
            with self.subTest(value=value):
                result = self.run_program(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, str(int(value)) + "\n")

    def test_invalid_values_are_clear_without_traceback(self):
        for value in ("x", "1.2", "NaN", "１２"):
            with self.subTest(value=value):
                result = self.run_program(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_missing_values_and_help(self):
        result = self.run_program()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        help_result = self.run_program("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("signed ASCII integers", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
