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
import ledger as lg  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s5")


def L(n):
    return strict_load(os.path.join(FX, n))


BAD = {
    "invalid-missing-id.json": "missing facet 'id'",
    "invalid-missing-type.json": "missing facet 'type'",
    "invalid-missing-content.json": "missing facet 'content'",
    "invalid-missing-source-ids.json": "missing facet 'source_ids'",
    "invalid-missing-status.json": "missing facet 'status'",
    "invalid-missing-timestamp.json": "missing facet 'timestamp'",
    "invalid-missing-version-introduced.json": "missing facet 'version_introduced'",
    "invalid-missing-superseded-entry-ids.json": "missing facet 'superseded_entry_ids'",
    "invalid-missing-affected-slices.json": "missing facet 'affected_slices'",
    "invalid-unknown-type.json": "type must be",
    "invalid-bad-timestamp.json": "timestamp",
    "invalid-bool-version.json": "version_introduced must be",
    "invalid-duplicate-id.json": "duplicate id",
    "invalid-supersedes-unknown.json": "unknown or later",
    "invalid-supersedes-newer.json": "unknown or later",
    "invalid-silent-promotion.json": "without a promotion block",
    "invalid-promotion-no-approval-ref.json": "promotion.approval_ref is required",
    "invalid-promotion-authority-planner.json": "promotion.authority",
    "invalid-author-manager.json": "author_role",
    "invalid-approval-granting-key.json": "unknown field 'owner_approved'",
}
APPEND_BAD = ["append-bad-edited-content.json", "append-bad-edited-status.json",
              "append-bad-removed-entry.json", "append-bad-reordered.json"]


class T(unittest.TestCase):
    def test_valid(self):
        for n in ["valid-initial.json", "valid-v2-superseding-decision.json", "valid-assumption-promoted.json"]:
            self.assertEqual(lg.validate_ledger(L(n)), [], n)

    def test_invalid(self):
        for n, frag in BAD.items():
            with self.subTest(n):
                errs = lg.validate_ledger(L(n))
                self.assertTrue(any(frag in e for e in errs), errs)

    def test_every_invalid_fixture_listed(self):
        on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(FX, "invalid-*.json"))}
        self.assertEqual(on_disk, set(BAD))

    def test_active_entries(self):
        ids = [e["id"] for e in lg.active_entries(L("valid-v2-superseding-decision.json"))]
        self.assertNotIn("D1", ids)
        self.assertIn("D2", ids)
        self.assertEqual(len(lg.active_entries(L("valid-initial.json"))), 5)

    def test_append_only_ok(self):
        self.assertEqual(lg.check_append_only(L("valid-initial.json"), L("valid-v2-superseding-decision.json")), [])
        self.assertEqual(lg.check_append_only(L("valid-initial.json"), L("valid-initial.json")), [])

    def test_append_only_violations(self):
        for n in APPEND_BAD:
            with self.subTest(n):
                self.assertTrue(lg.check_append_only(L("valid-initial.json"), L(n)), n)
        errs = lg.check_append_only(L("valid-v2-superseding-decision.json"), L("append-bad-version-decreased.json"))
        self.assertTrue(any("must not decrease" in e for e in errs), errs)

    def test_no_mutation(self):
        a, b = L("valid-initial.json"), L("valid-v2-superseding-decision.json")
        a0, b0 = copy.deepcopy(a), copy.deepcopy(b)
        lg.validate_ledger(a); lg.validate_ledger(b); lg.active_entries(b); lg.check_append_only(a, b)
        self.assertEqual((a, b), (a0, b0))
        for n in BAD:
            x = L(n); x0 = copy.deepcopy(x); lg.validate_ledger(x); self.assertEqual(x, x0)

    def test_non_dict(self):
        self.assertTrue(lg.validate_ledger([]))
        self.assertTrue(lg.validate_ledger({"entries": "x"}))

    def test_cli(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for n, rc in [("valid-initial.json", 0), ("invalid-unknown-type.json", 2)]:
            r = subprocess.run([sys.executable, os.path.join(PKG, "ledger.py"), os.path.join(FX, n)],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, rc)
            self.assertEqual(json.loads(r.stdout)["valid"], rc == 0)


if __name__ == "__main__":
    unittest.main()
