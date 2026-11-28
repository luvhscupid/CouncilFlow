"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import ast
import json
import os
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
import adaptive_mode as am  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s4")


def L(n):
    return strict_load(os.path.join(FX, n))


def cli(n):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, os.path.join(PKG, "adaptive_mode.py"), os.path.join(FX, n)],
                          capture_output=True, text=True, env=env)


PLAN_BAD = {
    "invalid-plan-author-planner.json": "author_role",
    "invalid-plan-unknown-mode.json": "mode must be",
    "invalid-plan-cycle.json": "cycle",
    "invalid-plan-unknown-dependency.json": "unknown slice",
    "invalid-plan-duplicate-slice.json": "duplicate slice_id",
    "invalid-plan-missing-pinned.json": "pinned_ledger_version",
    "invalid-plan-revision-bool.json": "plan_revision",
    "invalid-plan-default-with-slices.json": "default",
}


class AdaptiveModeTests(unittest.TestCase):
    def test_valid(self):
        for n in ("valid-plan.json", "valid-plan-default.json"):
            self.assertEqual(am.validate_slice_plan(L(n)), [], n)
        for n in ("valid-readiness.json", "valid-readiness-blocked.json"):
            self.assertEqual(am.validate_readiness(L(n)), [], n)

    def test_invalid_plans(self):
        for n, frag in PLAN_BAD.items():
            errs = am.validate_slice_plan(L(n))
            self.assertTrue(any(frag in e for e in errs), (n, errs))

    def test_alias_as_role_rejected(self):
        # built at run time so no alias literal is stored in the repo
        alias = next(iter(strict_load(os.path.join(PKG, "role_aliases.json"))["aliases"]))
        plan = L("valid-plan.json")
        plan["slices"][0]["assignment"]["role"] = alias
        errs = am.validate_slice_plan(plan)
        self.assertEqual(len([e for e in errs if "assignment.role" in e]), 1, errs)

    def test_readiness_author_manager(self):
        errs = am.validate_readiness(L("invalid-readiness-author-manager.json"))
        self.assertTrue(any("author_role" in e for e in errs))

    def test_no_proceed_with_assumptions_yet(self):
        r = dict(L("valid-readiness.json"), state="PROCEED_WITH_ASSUMPTIONS")
        self.assertTrue(am.validate_readiness(r))

    def test_coherence(self):
        plan = L("valid-plan.json")
        self.assertEqual(am.check_coherence(plan, [L("valid-readiness.json")]), [])
        e1 = am.check_coherence(plan, [L("invalid-readiness-unknown-slice.json")])
        self.assertTrue(any("unknown slice" in e for e in e1), e1)
        e2 = am.check_coherence(plan, [L("invalid-readiness-ledger-mismatch.json")])
        self.assertTrue(any("differs from pinned" in e for e in e2), e2)

    def test_graph_direct(self):
        self.assertEqual(am.validate_slice_graph(L("valid-plan.json")), [])
        self.assertTrue(am.validate_slice_graph(L("invalid-plan-cycle.json")))

    def test_cli(self):
        r = cli("valid-plan.json")
        self.assertEqual((r.returncode, json.loads(r.stdout)["valid"]), (0, True))
        r = cli("invalid-plan-cycle.json")
        self.assertEqual((r.returncode, json.loads(r.stdout)["valid"]), (2, False))
        self.assertEqual(cli("valid-readiness.json").returncode, 0)
        self.assertEqual(cli("invalid-readiness-author-manager.json").returncode, 2)

    def test_source_constraints(self):
        src_path = os.path.join(PKG, "adaptive_mode.py")
        src = open(src_path, encoding="utf-8").read()
        self.assertNotIn("message_type", src)
        for node in ast.walk(ast.parse(src)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for n in names:
                self.assertFalse(n.split(".")[0] == "plugins", n)
        self.assertNotIn("plugins", src)


if __name__ == "__main__":
    unittest.main()
