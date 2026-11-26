"""Regressions for the contract bugs found in the tabsplit-1 run (2026-11-25).

One test class per bug in the run record's "CouncilFlow bugs found" list; see
docs/plans/tabsplit-bug-fixes.md. Packets and plans are synthetic fixtures shaped
like the run's real packets; they prove helper behavior, not live agent activation.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as f

c = f.c
import planner_contract as pc  # noqa: E402  (test_contracts put the skill scripts on sys.path)

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/council-flow/scripts"
AC = ["AC1", "AC2"]
CRITERIA = [{"id": "AC1", "criterion": "First behavior."}, {"id": "AC2", "criterion": "Second behavior."}]


def two_task_plan(revision=1):
    return {"plan_id": "P1", "plan_revision": revision, "acceptance": copy.deepcopy(CRITERIA),
            "tasks": [{"id": "T1", "instructions": ["Build the first part."], "acceptance_ids": ["AC1"], "depends_on": []},
                      {"id": "T2", "instructions": ["Build the second part."], "acceptance_ids": ["AC2"],
                       "depends_on": ["T1"]}]}


def envelope(mid, kind, role, recipient, payload, reply=None, attempt="A1", revision=1, task="run-1"):
    m = f.message(mid, kind, role, recipient, payload, reply, attempt)
    m["plan_revision"], m["task_id"], m["evidence_refs"] = revision, task, []
    return m


def publish(mid, plan_ref, revision=1, attempt="plan-1", reply=None, acceptance=AC):
    return envelope(mid, "plan.publish", "planner", "manager",
                    {"objective": "Synthetic two-part task", "scope": ["app/**"],
                     "acceptance_ids": list(acceptance), "plan_ref": plan_ref},
                    reply, attempt, revision)


def worker_assign(mid, reply, task_payload, revision=1, attempt="A1", plan_task_id=None):
    p = {"objective": "Synthetic two-part task", "scope": ["app/**"],
         "acceptance_ids": task_payload["acceptance_ids"], "instructions": task_payload["instructions"]}
    if plan_task_id is not None:
        p["plan_task_id"] = plan_task_id
    return envelope(mid, "job.assign", "manager", "worker", p, reply, attempt, revision)


class RootCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, value, identity=None, kind="plan"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(value, indent=1).encode("utf-8")
        path.write_bytes(data)
        return {"artifact_id": identity or Path(name).stem, "path": name,
                "sha256": hashlib.sha256(data).hexdigest(), "kind": kind}

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def planner_cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "planner_contract.py"), *map(str, args)],
                              capture_output=True, text=True, timeout=60)


class Bug1TaskIdTwoMeanings(RootCase):
    """job.assign names the Planner task in payload.plan_task_id; envelope task_id stays the run's."""

    def test_second_task_of_multi_task_plan_dispatches_through_both_checks(self):
        plan = two_task_plan()
        plan_ref = self.put("plan-r1.json", plan)
        assign = worker_assign("M2", "M1", plan["tasks"][1], plan_task_id="T2")
        c.validate_sequence([publish("M1", plan_ref), assign], root=self.root)
        result = self.planner_cli("assignment", self.write("plan.json", plan),
                                  self.write("criteria.json", CRITERIA), self.write("assign.json", assign))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_plan_task_is_refused_by_both_checks(self):
        plan = two_task_plan()
        plan_ref = self.put("plan-r1.json", plan)
        assign = worker_assign("M2", "M1", plan["tasks"][1], plan_task_id="T9")
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence([publish("M1", plan_ref), assign], root=self.root)
        self.assertEqual(failure.exception.code, "unknown_plan_task")
        result = self.planner_cli("assignment", self.write("plan.json", plan),
                                  self.write("criteria.json", CRITERIA), self.write("assign.json", assign))
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown_task", result.stderr)

    def test_single_task_runs_without_plan_task_id_still_work(self):
        p = {"plan_id": "P1", "plan_revision": 1, "acceptance": [CRITERIA[0]],
             "tasks": [{"id": "T1", "instructions": ["Do it."], "acceptance_ids": ["AC1"], "depends_on": []}]}
        self.assertIsNone(pc.validate_worker_assignment(
            p, plan_id="P1", plan_revision=1, task_id="T1", acceptance_ids=["AC1"],
            instructions=["Do it."], original_acceptance=[CRITERIA[0]]))


class Bug2PlanRefMutablePath(RootCase):
    """A new revision cannot reuse an earlier revision's plan file."""

    def test_revision_reusing_plan_path_is_refused_with_clear_code(self):
        r1 = f.ref("plan-r1", "plan.json", kind="plan")
        r2 = f.ref("plan-r2", "plan.json", "1" * 64, kind="plan")
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence([publish("M1", r1), publish("M3", r2, revision=2)])
        self.assertEqual(failure.exception.code, "plan_ref_reused")

    def test_revision_reusing_plan_artifact_id_is_refused(self):
        r1 = f.ref("plan", "plan-r1.json", kind="plan")
        r2 = f.ref("plan", "plan-r2.json", "1" * 64, kind="plan")
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence([publish("M1", r1), publish("M3", r2, revision=2)])
        self.assertEqual(failure.exception.code, "plan_ref_reused")


class Bug3RevisionInOneRunFolder(RootCase):
    """The tabsplit shape: rev 1 published, dispatch rejected, rev 2 published in the same run folder."""

    def setUp(self):
        super().setUp()
        self.run = self.root / ".councilflow/runs/run-1"
        self.run.mkdir(parents=True)
        self.r1 = self.put("plan-r1.json", two_task_plan(1))
        changed = two_task_plan(2)
        changed["tasks"][1]["instructions"] = ["Build the second part, revised."]
        self.plan2 = changed
        self.r2 = self.put("plan-r2.json", changed)

    def save(self, message):
        return c.save_message((json.dumps(message) + "\n").encode("utf-8"), self.run, root=self.root)

    def test_second_revision_saves_into_same_run_folder_and_dispatches(self):
        self.save(publish("M1", self.r1))
        self.save(publish("M3", self.r2, revision=2, attempt="plan-2"))
        self.save(worker_assign("M4", "M3", self.plan2["tasks"][0], revision=2, plan_task_id="T1"))
        saved = [c.read_json(p) for p in (self.run / "messages").glob("*.json")]
        c.validate_sequence(c._run_order(saved), root=self.root)

    def test_revision_may_reply_to_earlier_revision_message(self):
        self.save(publish("M1", self.r1))
        self.save(publish("M3", self.r2, revision=2, reply="M1"))

    def test_revision_cannot_change_owner_owned_fields(self):
        first = publish("M1", self.r1)
        for field, value in (("acceptance_ids", ["AC1"]), ("scope", ["elsewhere/**"]), ("objective", "Other goal")):
            second = publish("M3", self.r2, revision=2)
            second["payload"][field] = value
            with self.subTest(field=field), self.assertRaises(c.ContractError) as failure:
                c.validate_sequence([first, second])
            self.assertEqual(failure.exception.code, "plan_revision")

    def test_revision_cannot_change_actors_or_go_backwards(self):
        first = publish("M1", self.r1)
        second = publish("M3", self.r2, revision=2)
        second["sender"]["instance_id"] = "planner-2"
        with self.assertRaises(c.ContractError):
            c.validate_sequence([first, second])
        third = publish("M5", f.ref("plan-r0", "plan-r0.json", kind="plan"), revision=1)
        third["plan_revision"] = 1
        with self.assertRaises(c.ContractError):
            c.validate_sequence([publish("M1", self.r2, revision=2), third])

    def test_new_assignment_for_superseded_revision_is_refused(self):
        plan1 = two_task_plan(1)
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence([publish("M1", self.r1), publish("M3", self.r2, revision=2),
                                 worker_assign("M4", "M1", plan1["tasks"][0], plan_task_id="T1")])
        self.assertEqual(failure.exception.code, "plan_superseded")


class Bug4AttemptInheritedFromPublish(unittest.TestCase):
    """The first Worker job.assign starts the implementation attempt."""

    def test_rejected_m006_shape_now_passes(self):
        data = f.sequence()
        data[0]["attempt_id"] = "plan-2"  # plan.publish attempt differs from Worker attempt A1
        c.validate_sequence(data)

    def test_later_links_still_keep_the_attempt(self):
        data = f.sequence()
        data[0]["attempt_id"] = "plan-2"
        data[3]["attempt_id"] = "A9"  # Tester assignment replying to Worker report
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence(data)
        self.assertEqual(failure.exception.code, "attempt")


class Bug5NativePlanningCriteria(RootCase):
    """Native planning says so instead of comparing the plan with a copy of itself."""

    def setUp(self):
        super().setUp()
        self.plan = two_task_plan()
        self.assign = worker_assign("M2", "M1", self.plan["tasks"][0], plan_task_id="T1")

    def test_planner_generated_flag_validates_and_labels_source(self):
        result = self.planner_cli("assignment", self.write("plan.json", self.plan),
                                  self.write("assign.json", self.assign), "--planner-generated-criteria")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout),
                         {"valid": True, "dispatchable": True, "criteria_source": "planner-generated"})

    def test_frozen_file_is_labelled_frozen(self):
        result = self.planner_cli("assignment", self.write("plan.json", self.plan),
                                  self.write("criteria.json", CRITERIA), self.write("assign.json", self.assign))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["criteria_source"], "frozen")

    def test_both_or_neither_criteria_source_is_refused(self):
        plan, criteria, assign = (self.write("plan.json", self.plan), self.write("criteria.json", CRITERIA),
                                  self.write("assign.json", self.assign))
        both = self.planner_cli("assignment", plan, criteria, assign, "--planner-generated-criteria")
        neither = self.planner_cli("assignment", plan, assign)
        self.assertEqual(both.returncode, 2)
        self.assertEqual(neither.returncode, 2)
        self.assertIn("criteria_source", both.stderr)
        self.assertIn("criteria_source", neither.stderr)

    def test_plan_mode_lets_planner_self_check_before_publishing(self):
        good = self.planner_cli("plan", self.write("plan.json", self.plan), "--planner-generated-criteria")
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertTrue(json.loads(good.stdout)["valid"])
        broken = copy.deepcopy(self.plan)
        broken["tasks"][1]["depends_on"] = ["T404"]
        bad = self.planner_cli("plan", self.write("broken.json", broken), self.write("criteria.json", CRITERIA))
        self.assertEqual(bad.returncode, 2)
        self.assertIn("unknown_dependency", bad.stderr)


class Bug6WorkerReportEvidence(unittest.TestCase):
    """A Worker's hashed candidate_ref is its evidence; verifiers still cite evidence files."""

    def test_worker_report_with_empty_evidence_refs_passes(self):
        report = f.report("M3", "worker", "M2")
        report["evidence_refs"] = []
        c.validate_message(report)
        data = f.sequence()
        data[2]["evidence_refs"] = []
        c.validate_sequence(data)

    def test_tester_report_with_empty_evidence_refs_is_still_refused(self):
        report = f.report("M5", "tester", "M4")
        report["evidence_refs"] = []
        with self.assertRaises(c.ContractError) as failure:
            c.validate_message(report)
        self.assertEqual(failure.exception.code, "evidence")
        self.assertIn("tester", str(failure.exception))


class Bug7NoBytecodeInSkillFolder(unittest.TestCase):
    """Running the installed helpers never writes __pycache__ into the skill folder."""

    def test_cli_runs_do_not_write_pycache(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
            packet = Path(tmp) / "M1.json"
            packet.write_text(json.dumps(f.publish()), encoding="utf-8")
            runs = [["contracts.py", "message", str(packet)],
                    ["planner_contract.py", "--help"], ["doctor.py", "--help"],
                    ["route.py", "--help"], ["dashboard.py", "--help"]]
            for args in runs:
                with self.subTest(script=args[0]):
                    result = subprocess.run([sys.executable, str(scripts / args[0]), *args[1:]],
                                            capture_output=True, text=True, cwd=tmp, env=env, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual([str(p) for p in scripts.rglob("__pycache__")], [])


if __name__ == "__main__":
    unittest.main()
