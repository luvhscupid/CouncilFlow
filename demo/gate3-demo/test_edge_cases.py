"""Additional maintained error regressions, separate from historical Gate 3 checks."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

APP = Path(__file__).with_name("app.py")


class ErrorRegressions(unittest.TestCase):
    def test_blank_missing_and_invalid_utf8_values_fail_cleanly(self):
        for raw in (b"amount\n\"\"\n", b"other,amount\nx\n", b"amount\n\xff\n"):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.csv"
                path.write_bytes(raw)
                result = subprocess.run([sys.executable, str(APP), str(path), "amount"], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(result.stdout, b"")

    def test_bom_decimal_cli_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fraction.csv"
            path.write_text("\ufeffamount\n0.1\n0.2\n-0.05\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(APP), str(path), "amount"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.replace(b"\r\n", b"\n"), b"0.25\n")


if __name__ == "__main__":
    unittest.main()
