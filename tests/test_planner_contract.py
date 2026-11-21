"""Production Planner artifact and dispatch-boundary regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "councilflow_planner_contract",
    ROOT / ".agents/skills/council-flow/scripts/planner_contract.py",
)
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def plan():
    return {
        "plan_id": "P1", "plan_revision": 1,
        "acceptance": [{"id": "AC1", "criterion": "Keep the original behavior."}],
        "tasks": [{"id": "T1", "instructions": ["Inspect the existing behavior.", "Preserve it."],
                   "acceptance_ids": ["AC1"], "depends_on": []}],
    }


class PlannerContractTests(unittest.TestCase):
    def test_hosts_load_canonical_v2_instructions_and_packaged_copy_matches(self):
        canonical = (ROOT / ".agents/skills/council-flow/references/planner.md").read_bytes()
        codex = (ROOT / ".codex/agents/council-planner.toml").read_text(encoding="utf-8")
        self.assertIn("references/planner.md", codex)
        plugin = ROOT / "plugins/councilflow"
        if plugin.is_dir():
            claude = (plugin / "agents/council-planner.md").read_text(encoding="utf-8")
            self.assertIn("CF/references/planner.md", claude)
            self.assertEqual(canonical, (plugin / "skills/run/references/planner.md").read_bytes())
            self.assertEqual((ROOT / ".agents/skills/council-flow/scripts/planner_contract.py").read_bytes(),
                             (plugin / "skills/run/scripts/planner_contract.py").read_bytes())

    def test_ready_plan_covers_frozen_criteria_and_is_dispatchable(self):
        original = copy.deepcopy(plan()["acceptance"])
        self.assertIsNone(contract.validate_plan(plan(), original))

    def test_non_ready_plan_is_not_dispatchable(self):
        with self.assertRaises(contract.ContractError):
            contract.validate_plan({"plan_id": "P1", "plan_revision": 1,
                                    "acceptance": plan()["acceptance"], "tasks": []},
                                   plan()["acceptance"])

    def test_exact_selected_worker_instruction_transfer_and_identity(self):
        p = plan()
        self.assertIsNone(contract.validate_worker_assignment(
            p, plan_id="P1", plan_revision=1, task_id="T1",
            acceptance_ids=["AC1"], instructions=p["tasks"][0]["instructions"],
            original_acceptance=p["acceptance"]))
        with self.assertRaises(contract.ContractError):
            contract.validate_worker_assignment(
                p, plan_id="P2", plan_revision=1, task_id="T1", acceptance_ids=["AC1"],
                instructions=p["tasks"][0]["instructions"], original_acceptance=p["acceptance"])
        with self.assertRaises(contract.ContractError):
            contract.validate_worker_assignment(
                p, plan_id="P1", plan_revision=1, task_id="T1", acceptance_ids=["AC1"],
                instructions=["rewritten"], original_acceptance=p["acceptance"])

    def test_assignment_cli_validates_complete_dispatch_boundary(self):
        p = plan()
        envelope = {"message_type": "job.assign", "plan_id": "P1", "plan_revision": 1,
                    "task_id": "T1", "payload": {"acceptance_ids": ["AC1"],
                    "instructions": p["tasks"][0]["instructions"]}}
        script = ROOT / ".agents/skills/council-flow/scripts/planner_contract.py"
        with tempfile.TemporaryDirectory(prefix="planner-assignment-") as temp:
            paths = [Path(temp) / name for name in ("plan.json", "criteria.json", "assignment.json")]
            for path, value in zip(paths, (p, p["acceptance"], envelope)):
                path.write_text(json.dumps(value), encoding="utf-8")
            command = [sys.executable, "-I", str(script), "assignment", *(str(p) for p in paths)]
            good = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(good.returncode, 0, good.stderr)
            envelope["payload"]["instructions"] = ["rewritten"]
            paths[2].write_text(json.dumps(envelope), encoding="utf-8")
            bad = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("instruction_transfer", bad.stderr)

    def test_rejects_criteria_mutation_and_invalid_dependency_graph(self):
        p = plan()
        changed = copy.deepcopy(p["acceptance"])
        changed[0]["criterion"] += " Extra."
        with self.assertRaises(contract.ContractError):
            contract.validate_plan(p, changed)
        p["tasks"][0]["depends_on"] = ["T404"]
        with self.assertRaises(contract.ContractError):
            contract.validate_plan(p, p["acceptance"])


if __name__ == "__main__":
    unittest.main()
