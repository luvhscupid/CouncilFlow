"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import copy
import inspect
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import evidence as ev  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s6")


def F(n):
    return strict_load(os.path.join(FX, n))


LEDGER = F("ledger.json")
BAD_EV = {"invalid-evidence-new-requirement.json": "unknown field 'new_requirement'",
          "invalid-evidence-bad-sha256.json": "sha256",
          "invalid-evidence-path-traversal.json": "repo-relative",
          "invalid-evidence-absolute-path.json": "repo-relative"}
BAD_RR = {"invalid-reopen-empty-ledger-ids.json": "no ledger entry id cited",
          "invalid-reopen-nonexistent-ledger-id.json": "no cited ledger entry id exists",
          "invalid-reopen-missing-consequence.json": "missing field 'consequence'",
          "invalid-reopen-no-supporting-evidence.json": "no supporting evidence",
          "invalid-reopen-no-affected-slices.json": "no affected slices"}


class T(unittest.TestCase):
    def test_valid_evidence(self):
        for n in ("valid-evidence.json", "valid-evidence-minimal.json"):
            self.assertEqual(ev.validate_evidence(F(n)), [], n)

    def test_invalid_evidence(self):
        for n, frag in BAD_EV.items():
            errs = ev.validate_evidence(F(n))
            self.assertTrue(any(frag in e for e in errs), (n, errs))

    def test_requirement_changing_keys_rejected(self):
        for k in ("new_requirement", "ledger_change", "decision", "supersedes", "status_update"):
            e = F("valid-evidence.json")
            e[k] = "x"
            self.assertTrue(any("unknown field %r" % k in m for m in ev.validate_evidence(e)), k)
            r = F("valid-reopen.json")
            r[k] = "x"
            self.assertTrue(any("unknown field %r" % k in m for m in ev.validate_reopen_request(r)), k)

    def test_display_alias_rejected_built_at_runtime(self):
        alias = " ".join(["QA", "Engineer"])  # built here so no alias-as-role text sits in a fixture
        e = F("valid-evidence.json")
        e["source_agent"] = alias
        self.assertTrue(any("source_agent" in m for m in ev.validate_evidence(e)))
        r = F("valid-reopen.json")
        r["submitter_role"] = alias
        self.assertTrue(any("submitter_role" in m for m in ev.validate_reopen_request(r)))
        self.assertEqual(ev.classify_reopen(r, LEDGER)[0], "retained_as_evidence_only")

    def test_all_wire_roles_accepted(self):
        for role in ev.WIRE_ROLES:
            e = F("valid-evidence.json")
            e["source_agent"] = role
            self.assertEqual(ev.validate_evidence(e), [], role)
            r = F("valid-reopen.json")
            r["submitter_role"] = role
            self.assertEqual(ev.classify_reopen(r, LEDGER)[0], "valid_for_reopen", role)

    def test_bad_status_and_timestamp(self):
        e = F("valid-evidence.json")
        e["reopen_status"] = "approved"
        e["timestamp"] = "2026-11-27T11:00:00"  # no timezone
        errs = ev.validate_evidence(e)
        self.assertTrue(any("reopen_status" in m for m in errs) and any("timestamp" in m for m in errs))

    def test_valid_reopen(self):
        self.assertEqual(ev.validate_reopen_request(F("valid-reopen.json")), [])
        self.assertEqual(ev.classify_reopen(F("valid-reopen.json"), LEDGER), ("valid_for_reopen", []))

    def test_invalid_reopen_retained_as_evidence(self):
        for n, frag in BAD_RR.items():
            status, reasons = ev.classify_reopen(F(n), LEDGER)
            self.assertEqual(status, "retained_as_evidence_only", n)
            self.assertTrue(any(frag in m for m in reasons), (n, reasons))

    def test_boolean_in_numeric_field(self):
        # Records have no numeric field; the only numbers they depend on are in the supplied ledger.
        bad = copy.deepcopy(LEDGER)
        bad["ledger_version"] = True
        status, reasons = ev.classify_reopen(F("valid-reopen.json"), bad)
        self.assertEqual(status, "retained_as_evidence_only")
        self.assertTrue(any("ledger_version" in m for m in reasons), reasons)

    def test_classify_does_not_modify_ledger_or_request(self):
        led, rq = copy.deepcopy(LEDGER), F("valid-reopen.json")
        rq0 = copy.deepcopy(rq)
        for n in list(BAD_RR) + ["valid-reopen.json"]:
            ev.classify_reopen(F(n), led)
        ev.classify_reopen(rq, led)
        self.assertEqual(led, LEDGER)
        self.assertEqual(rq, rq0)

    def test_no_function_returns_or_writes_ledger(self):
        for name, fn in inspect.getmembers(ev, inspect.isfunction):
            if fn.__module__ != "evidence" or name.startswith("_"):
                continue
            self.assertNotRegex(name, r"write|save|apply|update|amend|promote|supersede", name)
        src = inspect.getsource(ev)
        self.assertNotRegex(src, r"(?<![A-Za-z_])open\(|json\.dump|return ledger")

    def test_cli(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for n, code in (("valid-evidence.json", 0), ("valid-reopen.json", 0),
                        ("invalid-evidence-new-requirement.json", 2), ("invalid-reopen-missing-consequence.json", 2)):
            p = subprocess.run([sys.executable, os.path.join(PKG, "evidence.py"), os.path.join(FX, n)],
                               capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, code, n)
            self.assertEqual(json.loads(p.stdout)["valid"], code == 0)


if __name__ == "__main__":
    unittest.main()
