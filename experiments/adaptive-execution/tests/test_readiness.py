"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import readiness as rd  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s8")


def L(n):
    return strict_load(os.path.join(FX, n))


def bundle_errs(n):
    b = L(n)
    return rd.validate_readiness_ext(b["readiness"], b["ledger"], b["mode"])


class Count(unittest.TestCase):
    def test_counts(self):
        for n in (0, 4, 5, 6):
            self.assertEqual(rd.active_unconfirmed_count(L("ledger-n%d.json" % n)), n)

    def test_supersession(self):
        # A1->confirmed, A2->rejected stop consuming; D3->D6 provisional counts once.
        self.assertEqual(rd.active_unconfirmed_count(L("ledger-superseded.json")), 1)


class Budget(unittest.TestCase):
    def ev(self, ledger, slices, lim):
        return rd.evaluate_slices(L(ledger), L(slices), {"unconfirmed_decision_limit": lim})

    def test_limit5_exhausted(self):
        self.assertEqual(self.ev("ledger-n5.json", "slices-limit5-used5.json", 5),
                         {"a": "PAUSED_BUDGET", "b": "PAUSED_BUDGET", "c": "CONTINUE",
                          "d": "BLOCKED", "e": "PAUSED_BUDGET"})

    def test_limit_boundary(self):
        self.assertEqual(self.ev("ledger-n4.json", "slices-limit4-used4.json", 5),
                         {"a": "CONTINUE", "b": "PAUSED_BUDGET"})

    def test_limit0(self):
        self.assertEqual(self.ev("ledger-n0.json", "slices-limit0-used0.json", 0),
                         {"a": "PAUSED_BUDGET", "b": "CONTINUE", "d": "BLOCKED"})

    def test_blocking_with_budget_free(self):
        self.assertEqual(self.ev("ledger-n0.json", "slices-limit0-used0.json", 5)["d"], "BLOCKED")

    def test_bad_limits(self):
        for bad in (-1, True, "5", None, 1.0):
            with self.assertRaises(ValueError):
                self.ev("ledger-n0.json", "slices-limit0-used0.json", bad)
        self.assertEqual(rd.validate_budget_config({"unconfirmed_decision_limit": 0}), [])


class Discovery(unittest.TestCase):
    def test_cap(self):
        ev = L("events.json")
        self.assertEqual(rd.discovery_cycles_used(ev, "a"), 2)
        self.assertEqual(rd.discovery_cycles_used(ev, "b"), 1)
        self.assertEqual(rd.request_discovery(ev, "a"), {"slice_id": "a", "action": "escalate_scope_question"})
        self.assertEqual(rd.request_discovery(ev, "b")["action"], "run_discovery_cycle")
        self.assertEqual(rd.request_discovery(ev, "z")["action"], "run_discovery_cycle")


class Readiness(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(bundle_errs("valid-pwa.json"), [])

    def test_invalid(self):
        want = {
            "invalid-pwa-no-assumption-ids.json": "assumption_ids",
            "invalid-pwa-empty-assumption-ids.json": "assumption_ids",
            "invalid-pwa-unknown-id.json": "not an active",
            "invalid-pwa-rejected-assumption.json": "provisional",
            "invalid-pwa-superseded-assumption.json": "not an active",
            "invalid-pwa-blocking-decision.json": "blocking_decision",
            "invalid-pwa-default-mode.json": "default",
            "invalid-needs-information-adaptive.json": "state must be one of",
        }
        for n, frag in want.items():
            errs = bundle_errs(n)
            self.assertTrue(any(frag in e for e in errs), (n, errs))

    def test_default_mode_unchanged(self):
        b = L("valid-pwa.json")
        r = dict(b["readiness"], state="NEEDS_INFORMATION")
        r.pop("assumption_ids")
        r.pop("blocking_decision")
        self.assertEqual(rd.validate_readiness_ext(r, b["ledger"], "default"), [])

    def test_cli(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for n, code in (("valid-pwa.json", 0), ("invalid-pwa-unknown-id.json", 2)):
            p = subprocess.run([sys.executable, os.path.join(PKG, "readiness.py"), os.path.join(FX, n)],
                               capture_output=True, text=True, env=env)
            self.assertEqual(p.returncode, code)
            self.assertEqual(json.loads(p.stdout)["valid"], code == 0)


class Classes(unittest.TestCase):
    def test_table(self):
        self.assertEqual(rd.CLASSES["cheap_reversible"][1:], ("planner_provisional_default", "proceed"))
        self.assertEqual(rd.CLASSES["costly_reversible"][1:], ("owner_approval", "pause_affected_slice"))
        for c in ("irreversible_or_external", "security_data_financial_legal", "owner_controlled"):
            self.assertEqual(rd.CLASSES[c][1:], ("owner_approval", "block"))

    def test_downgrade(self):
        self.assertTrue(rd.check_classification("costly_reversible", "cheap_reversible"))
        for c in ("irreversible_or_external", "security_data_financial_legal", "owner_controlled"):
            self.assertTrue(rd.check_classification(c, "cheap_reversible"))
            self.assertTrue(rd.check_classification(c, "costly_reversible"))
            self.assertEqual(rd.check_classification(c, c), [])
        self.assertEqual(rd.check_classification("cheap_reversible", "owner_controlled"), [])
        self.assertTrue(rd.check_classification("cheap_reversible", "bogus"))


if __name__ == "__main__":
    unittest.main()
