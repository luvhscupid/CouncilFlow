"""Predeclared stable test-result output; only raw CRLF-to-LF hashing is external."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "reports/councilflow-final-release-audit/worker/final/candidate-manifest.json"
EXPECTED = "9e5ae1a046221deb96a345815ef9ac72746f023ccd01bdaf34984ea224c4a113"
SUITES = ["tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification"]


def check_candidate():
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == EXPECTED
    manifest = json.loads(MANIFEST.read_bytes())
    for item in manifest["files"]:
        data = (ROOT / item["path"]).read_bytes()
        assert len(data) == item["size"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    assert hashlib.sha256((ROOT / manifest["archive"]["path"]).read_bytes()).hexdigest() == manifest["archive"]["sha256"]


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append([test.id(), "passed"])

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append([test.id(), "skipped"])

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append([test.id(), "failed"])

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append([test.id(), "error"])


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        suite = sys.argv[2]
        assert suite in SUITES
        output = io.StringIO()
        tests = unittest.defaultTestLoader.discover(str(ROOT / suite))
        result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(tests)
        sys.stderr.write(output.getvalue())
        print(json.dumps({"suite": suite, "run": result.testsRun,
                          "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
                          "failed": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                          "records": sorted(result.records)}, sort_keys=True, separators=(",", ":")))
        return 0 if result.wasSuccessful() else 1
    assert len(sys.argv) == 1
    check_candidate()
    results = []
    code = 0
    for suite in SUITES:
        process = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--child", suite],
                                 cwd=ROOT, capture_output=True)
        sys.stderr.buffer.write(process.stderr)
        code = max(code, process.returncode)
        results.append(json.loads(process.stdout))
    check_candidate()
    print(json.dumps({"candidate_manifest_sha256": EXPECTED, "suites": results},
                     sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
