"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import copy
import glob
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import qa_trace as qa  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s9")


def F(n):
    return strict_load(os.path.join(FX, n))


MISSING = ["test_id", "tested_behavior", "ledger_ids", "slice_id", "pinned_ledger_version", "result",
           "evidence", "timestamp"]
BAD = {
    "invalid-result-green.json": "result must be one of",
    "invalid-empty-ledger-ids.json": "ledger_ids must be a nonempty",
    "invalid-ledger-id-unknown.json": "not in ledger",
    "invalid-pinned-above-ledger.json": "exceeds ledger_version",
    "invalid-duplicate-test-id.json": "duplicate test_id",
    "invalid-check-link-unknown-test.json": "unknown test_id",
    "invalid-bool-version.json": "pinned_ledger_version must be",
}


class T(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(qa.validate_qa_sidecar(F("valid-sidecar.json")), [])
        self.assertEqual(qa.validate_qa_sidecar(F("valid-sidecar.json"), F("ledger-v1.json")), [])
        self.assertEqual(qa.validate_qa_sidecar(F("valid-sidecar-null-candidate.json")), [])

    def test_missing_each_field(self):
        for f in MISSING:
            with self.subTest(f):
                errs = qa.validate_qa_sidecar(F("invalid-missing-%s.json" % f.replace("_", "-")), F("ledger-v1.json"))
                self.assertTrue(any("missing field %r" % f in e for e in errs), errs)

    def test_invalid(self):
        for n, msg in BAD.items():
            with self.subTest(n):
                errs = qa.validate_qa_sidecar(F(n), F("ledger-v1.json"))
                self.assertTrue(any(msg in e for e in errs), errs)

    def test_ledger_checks_need_ledger(self):
        self.assertEqual(qa.validate_qa_sidecar(F("invalid-ledger-id-unknown.json")), [])

    def test_every_invalid_fixture_covered(self):
        names = {os.path.basename(p) for p in glob.glob(os.path.join(FX, "invalid-*.json"))}
        self.assertEqual(names, set(BAD) | {"invalid-missing-%s.json" % f.replace("_", "-") for f in MISSING})

    def stale(self, ledger):
        st = qa.stale_results(F(ledger), F("valid-sidecar.json")["records"])
        return st, qa.retest_scope(st)

    def test_unchanged(self):
        self.assertEqual(self.stale("ledger-v1.json"), ([], []))

    def test_requirement_superseded(self):
        st, scope = self.stale("ledger-v2.json")
        self.assertEqual(st, [{"test_id": "T-A", "stale": True, "reasons": ["superseded:R1"]}])
        self.assertEqual(scope, ["T-A"])

    def test_goal_superseded(self):
        st, scope = self.stale("ledger-v3.json")
        self.assertEqual(st, [{"test_id": "T-C", "stale": True, "reasons": ["goal_changed", "superseded:G1"]}])
        self.assertEqual(scope, ["T-C"])

    def test_goal_change_hits_other_record_of_affected_slice(self):
        recs = copy.deepcopy(F("valid-sidecar.json")["records"])
        recs[1]["slice_id"] = "S1"  # T-B covers only R2 but sits in the Goal's slice S1
        st = qa.stale_results(F("ledger-v3.json"), recs)
        self.assertEqual([s["test_id"] for s in st], ["T-B", "T-C"])
        self.assertEqual(st[0]["reasons"], ["goal_changed"])

    def test_pin_at_or_above_supersession_keeps_result(self):
        recs = copy.deepcopy(F("valid-sidecar.json")["records"])
        recs[0]["pinned_ledger_version"] = 2
        self.assertEqual(qa.stale_results(F("ledger-v2.json"), recs), [])

    def test_inputs_not_mutated(self):
        led, recs = F("ledger-v3.json"), F("valid-sidecar.json")["records"]
        l0, r0 = copy.deepcopy(led), copy.deepcopy(recs)
        qa.stale_results(led, recs)
        qa.validate_qa_sidecar(F("valid-sidecar.json"), led)
        self.assertEqual((led, recs), (l0, r0))

    def test_cli(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, os.path.join(PKG, "qa_trace.py"), "stale",
                            os.path.join(FX, "ledger-v2.json"), os.path.join(FX, "valid-sidecar.json")],
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout)["retest_scope"], ["T-A"])
        p = subprocess.run([sys.executable, os.path.join(PKG, "qa_trace.py"),
                            os.path.join(FX, "invalid-result-green.json")], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 2)
        self.assertFalse(json.loads(p.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
