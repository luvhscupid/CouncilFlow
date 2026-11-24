"""Static and helper checks for the Manager's Planner v2 and routing duties.

These are repository checks; they do not prove native host dispatch behavior.
"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/council-flow"
PLUGIN = ROOT / "plugins/councilflow"
RUN = PLUGIN / "skills/run"
# The Codex release archive ships without plugins/; plugin checks run only in a checkout.
HAS_PLUGIN = PLUGIN.is_dir()


def text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def plan():
    return {
        "plan_id": "P1", "plan_revision": 2,
        "acceptance": [{"id": "AC1", "criterion": "Keep behavior."},
                       {"id": "AC2", "criterion": "Document it."}],
        "tasks": [
            {"id": "T1", "instructions": ["Inspect.", "Preserve."], "acceptance_ids": ["AC1"], "depends_on": []},
            {"id": "T2", "instructions": ["Write docs."], "acceptance_ids": ["AC2"], "depends_on": ["T1"]},
        ],
    }


def assignment(**changes):
    message = {
        "message_type": "job.assign", "plan_id": "P1", "plan_revision": 2, "task_id": "T1",
        "payload": {"acceptance_ids": ["AC1"], "instructions": ["Inspect.", "Preserve."]},
    }
    for key, value in changes.items():
        if key in ("acceptance_ids", "instructions"):
            message["payload"][key] = value
        else:
            message[key] = value
    return message


class ManagerTextTests(unittest.TestCase):
    def test_manager_docs_require_ready_plan_check_and_exact_instructions(self):
        paths = [SKILL / "SKILL.md", SKILL / "references/workflow.md",
                 SKILL / "references/roles.md", SKILL / "references/communication.md"]
        if HAS_PLUGIN:
            paths += [RUN / "SKILL.md", RUN / "host-claude.md"]
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                body = text(path)
                self.assertIn("planner_contract.py", body)
                self.assertRegex(body.lower(), r"non-ready|needs_information")
        roles = text(SKILL / "references/roles.md")
        self.assertIn("rewriting Planner-authored task instructions", roles)
        self.assertIn("dispatching a non-ready plan", roles)

    def test_manager_supplies_planner_context(self):
        memory = text(SKILL / "references/codebase-memory.md")
        self.assertIn("supplies them to Planner before planning", memory)
        self.assertIn("Planner does not independently explore application source", memory)

    def test_routing_hint_is_advice_with_recorded_choice(self):
        paths = [SKILL / "SKILL.md", SKILL / "references/communication.md", SKILL / "references/workflow.md"]
        if HAS_PLUGIN:
            paths.append(RUN / "host-claude.md")
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                body = text(path).lower()
                self.assertIn("route.py" if path.name != "workflow.md" else "routing hint", body)
                self.assertIn("override", body)
                self.assertRegex(body, r"record")
        self.assertIn("ships none", text(SKILL / "references/communication.md"))

    def test_policy_keeps_frozen_manager_abilities_and_order(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        try:
            import contracts
        finally:
            sys.path.pop(0)
        raw = (SKILL / "policies/roles.yaml").read_text(encoding="utf-8")
        policy = contracts.parse_policy(raw)
        contracts.validate_policy(policy)
        manager = policy["roles"]["manager"]
        self.assertEqual(manager["abilities"], ["delegate", "request_rework", "evaluate_evidence"])
        self.assertFalse(manager["application_code"])
        joined = " ".join(manager["responsibilities"])
        self.assertIn("READY plan", joined)
        self.assertIn("routing hints as advice", joined)
        self.assertEqual(policy["workflow"]["order"],
                         ["owner", "planner", "manager", "worker", "tester", "reviewer", "manager", "planner", "owner"])

    @unittest.skipUnless(HAS_PLUGIN, "plugin package not present in this extraction")
    def test_adapter_maps_new_manager_helpers(self):
        adapter = text(RUN / "host-claude.md")
        self.assertIn("`CF/scripts/planner_contract.py`", adapter)
        self.assertIn("`CF/scripts/route.py`", adapter)


class ManagerDispatchCheckTests(unittest.TestCase):
    def run_check(self, script, cwd, plan_data, criteria, message):
        paths = [Path(cwd) / name for name in ("plan.json", "criteria.json", "assign.json")]
        for path, data in zip(paths, (plan_data, criteria, message)):
            path.write_text(json.dumps(data), encoding="utf-8")
        return subprocess.run([sys.executable, "-I", str(script), "assignment", *map(str, paths)],
                              cwd=cwd, capture_output=True, text=True, timeout=30)

    def test_manager_blocks_each_unsafe_dispatch(self):
        script = SKILL / "scripts/planner_contract.py"
        criteria = copy.deepcopy(plan()["acceptance"])
        dropped = plan()
        dropped["acceptance"].pop()
        dropped["tasks"].pop()
        cases = {
            "valid": (plan(), assignment(), 0),
            "reworded instruction": (plan(), assignment(instructions=["Inspect.", "Preserve it."]), 2),
            "reordered instructions": (plan(), assignment(instructions=["Preserve.", "Inspect."]), 2),
            "unknown task": (plan(), assignment(task_id="T9"), 2),
            "wrong revision": (plan(), assignment(plan_revision=1), 2),
            "dropped criterion": (dropped, assignment(), 2),
            "not an assignment": (plan(), assignment(message_type="job.report"), 2),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, (plan_data, message, code) in cases.items():
                with self.subTest(case=name):
                    result = self.run_check(script, tmp, plan_data, criteria, message)
                    self.assertEqual(result.returncode, code, result.stderr)
                    if code == 0:
                        self.assertEqual(json.loads(result.stdout), {"valid": True, "dispatchable": True})

    @unittest.skipUnless(HAS_PLUGIN, "plugin package not present in this extraction")
    def test_installed_plugin_copy_runs_check_and_route_from_another_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / "cache/councilflow"
            shutil.copytree(PLUGIN, installed)
            repo = Path(tmp) / "repo"
            repo.mkdir()
            skill = installed / "skills/run"
            result = self.run_check(skill / "scripts/planner_contract.py", repo, plan(),
                                    copy.deepcopy(plan()["acceptance"]), assignment())
            self.assertEqual(result.returncode, 0, result.stderr)
            config = repo / "routes.json"
            config.write_text(json.dumps({"version": "routing-v1", "threshold": 0.5, "margin": 0.1,
                                          "routes": [{"name": "docs", "examples": ["write docs"], "metadata": {}}]}))
            routed = subprocess.run([sys.executable, "-I", str(skill / "scripts/route.py"), "--config", str(config)],
                                    cwd=repo, input="write docs", capture_output=True, text=True, timeout=30)
            self.assertEqual(routed.returncode, 0, routed.stderr)
            self.assertEqual(json.loads(routed.stdout)["route"], "docs")
            self.assertFalse((repo / ".councilflow").exists())


class ManagerRoutingRecordTests(unittest.TestCase):
    def test_every_manager_choice_produces_a_sealed_record(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        try:
            from routing.contract import DecisionStatus, RouteDecision, hash_input, hash_route_config, validate_route_config
            from routing.decision import build_decision_record, override_route, validate_decision_record
        finally:
            sys.path.pop(0)
        config = validate_route_config({"version": "routing-v1", "threshold": 0.5, "margin": 0.1,
                                        "routes": [{"name": "docs", "examples": ["docs"], "metadata": {}}]})
        decision = RouteDecision(status=DecisionStatus.MATCHED, route="docs", confidence=0.9,
                                 threshold=0.5, margin=0.1, router_version="routing-v1",
                                 route_config_sha256=hash_route_config(config), input_sha256=hash_input("task"),
                                 encoder_id="lexical-v1", reason_codes=("threshold_met",))
        for action in ("accepted", "ignored", "blocked"):
            with self.subTest(action=action):
                record = build_decision_record(decision, manager_action=action)
                validate_decision_record(record)
                self.assertEqual(record["manager_action"], action)
        overridden = override_route(build_decision_record(decision, manager_action="ignored"), "Owner scope differs")
        validate_decision_record(overridden)
        self.assertEqual(overridden["manager_action"], "overridden")


if __name__ == "__main__":
    unittest.main()
