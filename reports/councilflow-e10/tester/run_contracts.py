"""Deterministic summary runner for the focused contract suite."""
import io
import json
import unittest


suite = unittest.defaultTestLoader.discover("tests", pattern="test_contracts.py")
result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=2).run(suite)
print(json.dumps({"tests_run": result.testsRun,
                  "failures": len(result.failures),
                  "errors": len(result.errors),
                  "skipped": len(result.skipped)}, sort_keys=True))
raise SystemExit(0 if result.wasSuccessful() else 1)
