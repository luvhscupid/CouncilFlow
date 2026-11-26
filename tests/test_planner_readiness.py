"""Planner readiness answers, model hints and the adaptive policy block."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/council-flow/scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pc = load("councilflow_pc_readiness", "planner_contract.py")
ps = load("councilflow_ps_readiness", "project_state.py")
contracts = load("councilflow_contracts_readiness", "contracts.py")
TS = "2026-11-26T10:00:00Z"


def answer(**changes):
    base = {"schema": "councilflow-readiness", "version": "1.0", "status": "READY",
            "slice_id": "S1", "ledger_version": None, "discovery_cycle": 1,
            "assumption_ids": [], "questions": [], "reason": "All conditions met."}
    base.update(changes)
    return base


def question(**changes):
    base = {"question_id": "Q1", "text": "Which database?", "blocking": True,
            "decision_class": "costly_reversible", "affected_slices": ["S1"],
            "permitted_default": None, "reason": "Schema choice is costly to revisit."}
    base.update(changes)
    return base


def plan():
    return {"plan_id": "P1", "plan_revision": 1,
            "acceptance": [{"id": "AC1", "criterion": "Keep the original behavior."}],
            "tasks": [{"id": "T1", "instructions": ["Inspect.", "Preserve."],
                       "acceptance_ids": ["AC1"], "depends_on": []}]}


def error_code(case, func, *args, **kwargs):
    with case.assertRaises(pc.ContractError) as ctx:
        func(*args, **kwargs)
    return ctx.exception.code


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"

    def build_project(self, budget=5, assumptions=("A1",)):
        (self.tmp / "owner.txt").write_text("Owner text\n", encoding="utf-8")
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": "Original."}]), encoding="utf-8")
        for args in (["init", "--project", self.project, "--budget", str(budget)],
                     ["source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                      "--received-at", TS],
                     ["bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                      "--source-id", "S0001", "--created-at", TS]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ps.main([str(a) for a in args]), 0)
        if assumptions:
            path = self.project / "ledger/L0001.json"
            import hashlib
            raw = path.read_bytes()
            data = json.loads(raw)
            data["ledger_version"] = 2
            data["previous_sha256"] = hashlib.sha256(raw).hexdigest()
            for aid in assumptions:
                data["entries"].append({
                    "id": aid, "type": "Assumption", "content": "Default name", "source_ids": ["S0001"],
                    "evidence_ids": [], "status": "unconfirmed", "created_at": TS,
                    "version_introduced": 2, "supersedes": [], "affected_slices": []})
            (self.project / "ledger/L0002.json").write_text(json.dumps(data), encoding="utf-8")
        errors, _ = ps.validate(self.project)
        self.assertEqual(list(errors), [])

    def proceed(self, **changes):
        return answer(status="PROCEED_WITH_ASSUMPTIONS", ledger_version=2, assumption_ids=["A1"],
                      questions=[question(blocking=False, decision_class="cheap_reversible",
                                          permitted_default="name it widget")], **changes)

    def test_ready_is_valid_and_dispatchable(self):
        result = pc.validate_readiness(answer())
        self.assertEqual(result, {"valid": True, "status": "READY", "dispatchable": True,
                                  "escalate_to_owner": False, "budget": None, "reasons": []})

    def test_proceed_without_project_is_not_dispatchable(self):
        result = pc.validate_readiness(self.proceed())
        self.assertFalse(result["dispatchable"])
        self.assertEqual(result["reasons"], ["budget_unchecked"])

    def test_proceed_with_project_is_dispatchable(self):
        self.build_project()
        result = pc.validate_readiness(self.proceed(), self.project)
        self.assertTrue(result["dispatchable"])
        self.assertEqual(result["budget"], {"limit": 5, "used": 1, "exceeded": False})

    def test_budget_exhausted_is_not_dispatchable(self):
        self.build_project(budget=0)
        result = pc.validate_readiness(self.proceed(), self.project)
        self.assertFalse(result["dispatchable"])
        self.assertEqual(result["reasons"], ["budget_exhausted"])

    def test_unknown_or_confirmed_assumption_fails(self):
        self.build_project()
        bad = self.proceed()
        bad["assumption_ids"] = ["A9"]
        self.assertEqual(error_code(self, pc.validate_readiness, bad, self.project), "assumption_ref")
        bad = self.proceed()
        bad["assumption_ids"] = ["AC1"]  # a Requirement, not an Assumption
        self.assertEqual(error_code(self, pc.validate_readiness, bad, self.project), "assumption_ref")
        path = self.project / "ledger/L0002.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entries"][-1]["status"] = "confirmed"
        path.write_text(json.dumps(data), encoding="utf-8")
        code = error_code(self, pc.validate_readiness, self.proceed(), self.project)
        self.assertIn(code, {"assumption_ref", "project_invalid"})

    def test_missing_ledger_version_fails(self):
        self.build_project()
        bad = self.proceed()
        bad["ledger_version"] = 7
        self.assertEqual(error_code(self, pc.validate_readiness, bad, self.project), "assumption_ref")

    def test_invalid_project_fails(self):
        self.build_project()
        (self.project / "sources/S0001.txt").write_bytes(b"changed")
        self.assertEqual(error_code(self, pc.validate_readiness, self.proceed(), self.project),
                         "project_invalid")

    def test_class_downgrade_fails(self):
        for changes in ({"blocking": False}, {"permitted_default": "just do it", "blocking": True}):
            bad = answer(status="BLOCKED", questions=[question(decision_class="owner_objective", **changes)])
            self.assertEqual(error_code(self, pc.validate_readiness, bad), "class_downgrade")

    def test_ready_with_blocking_question_fails(self):
        self.assertEqual(error_code(self, pc.validate_readiness, answer(questions=[question()])),
                         "readiness_state")
        self.assertEqual(error_code(self, pc.validate_readiness, answer(assumption_ids=["A1"])),
                         "readiness_state")

    def test_blocked_needs_blocking_question(self):
        self.assertEqual(error_code(self, pc.validate_readiness, answer(status="BLOCKED")), "readiness_state")

    def test_blocked_cycle_two_escalates(self):
        blocked = answer(status="BLOCKED", questions=[question()], discovery_cycle=2)
        result = pc.validate_readiness(blocked)
        self.assertEqual((result["dispatchable"], result["escalate_to_owner"]), (False, True))
        blocked["discovery_cycle"] = 1
        self.assertFalse(pc.validate_readiness(blocked)["escalate_to_owner"])

    def test_duplicate_question_ids_and_extra_keys_fail(self):
        dup = answer(status="BLOCKED", questions=[question(), question()])
        self.assertEqual(error_code(self, pc.validate_readiness, dup), "duplicate_question")
        extra = answer()
        extra["note"] = "x"
        self.assertEqual(error_code(self, pc.validate_readiness, extra), "fields")

    def test_cli_exit_codes(self):
        path = self.tmp / "answer.json"
        path.write_text(json.dumps(answer()), encoding="utf-8")
        cmd = [sys.executable, str(SCRIPTS / "planner_contract.py"), "readiness", str(path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["status"], "READY")
        path.write_text(json.dumps(answer(status="BLOCKED")), encoding="utf-8")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(json.loads(proc.stderr)["valid"])


class ModelHintTests(unittest.TestCase):
    HINT = {"model": "haiku", "reasoning": "medium", "reason": "Small mechanical task."}

    def hinted(self, hint):
        value = plan()
        value["tasks"][0]["model_hint"] = hint
        return value

    def test_valid_hint_passes_plan_and_assignment(self):
        value = self.hinted(dict(self.HINT))
        criteria = value["acceptance"]
        self.assertIsNone(pc.validate_plan(value, criteria))
        self.assertIsNone(pc.validate_worker_assignment(
            value, plan_id="P1", plan_revision=1, task_id="T1", acceptance_ids=["AC1"],
            instructions=["Inspect.", "Preserve."], original_acceptance=criteria))

    def test_bad_hints_fail(self):
        criteria = plan()["acceptance"]
        bad = [dict(self.HINT, reasoning="extreme"), dict(self.HINT, model=" x"), dict(self.HINT, model=""),
               dict(self.HINT, model="m" * 129), dict(self.HINT, reason=" "), {"model": "x"},
               dict(self.HINT, extra=1), "haiku", None]
        for hint in bad:
            self.assertEqual(error_code(self, pc.validate_plan, self.hinted(hint), criteria), "model_hint")

    def test_other_extra_task_keys_still_fail_and_no_hint_is_unchanged(self):
        value = plan()
        self.assertIsNone(pc.validate_plan(value, copy.deepcopy(value["acceptance"])))
        value["tasks"][0]["other"] = 1
        self.assertEqual(error_code(self, pc.validate_plan, value, value["acceptance"]), "fields")


class AdaptivePolicyTests(unittest.TestCase):
    def policy(self):
        text = (ROOT / ".agents/skills/council-flow/policies/roles.yaml").read_text(encoding="utf-8")
        return contracts.parse_policy(text)

    def test_policy_with_adaptive_block_validates(self):
        policy = self.policy()
        self.assertIsNotNone(policy)
        self.assertEqual(policy["adaptive"]["default_unconfirmed_budget"], 5)
        contracts.validate_policy(policy)

    def test_changed_adaptive_value_fails(self):
        policy = self.policy()
        policy["adaptive"]["default_unconfirmed_budget"] = 6
        with self.assertRaises(contracts.ContractError) as ctx:
            contracts.validate_policy(policy)
        self.assertEqual(ctx.exception.code, "policy_semantics")

    def test_policy_without_adaptive_block_still_validates(self):
        policy = self.policy()
        del policy["adaptive"]
        contracts.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
