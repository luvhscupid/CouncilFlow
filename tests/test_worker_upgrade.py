"""Static checks for the Worker's execute-only duties.

These are repository checks; they do not prove native host dispatch behavior.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/council-flow"
CODEX_WORKER = ROOT / ".codex/agents/council-worker.toml"
PLUGIN = ROOT / "plugins/councilflow"
PLUGIN_WORKER = PLUGIN / "agents/council-worker.md"
# The Codex release archive ships without plugins/; plugin checks run only in a checkout.
HAS_PLUGIN = PLUGIN.is_dir()

# Rules both Worker copies must state, in the same words.
RULES = (
    "Planner's task instructions",
    "follow them exactly, in order, as written",
    "developer-side checks the instructions name",
    "recording real exit results",
    "Write code only",
    "do not plan, reorder or add steps",
    "review or judge your own work",
    "expand scope",
    "approve your own work",
    "stop and return job.report status blocked",
    "name the unchanged input candidate when nothing was edited",
    "changed files",
)


def text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def contracts():
    sys.path.insert(0, str(SKILL / "scripts"))
    try:
        import contracts as module
    finally:
        sys.path.pop(0)
    return module


class WorkerTextTests(unittest.TestCase):
    def worker_files(self):
        files = [CODEX_WORKER]
        if HAS_PLUGIN:
            files.append(PLUGIN_WORKER)
        return files

    def test_both_worker_copies_state_every_rule(self):
        for path in self.worker_files():
            body = text(path)
            for rule in RULES:
                with self.subTest(path=path.relative_to(ROOT).as_posix(), rule=rule):
                    self.assertIn(rule, body)

    @unittest.skipUnless(HAS_PLUGIN, "plugin package not present in this extraction")
    def test_plugin_worker_keeps_edit_tools(self):
        header = PLUGIN_WORKER.read_text(encoding="utf-8").split("---")[1]
        self.assertIn("tools: Read, Grep, Glob, Bash, Write, Edit", header)

    def test_roles_reference_lists_worker_rules(self):
        rows = [line for line in (SKILL / "references/roles.md").read_text(encoding="utf-8").splitlines()
                if line.startswith("| Worker |")]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        for phrase in ("Planner-authored task instructions exactly and in order", "status blocked",
                       "Planning, reordering or adding steps", "reviewing or judging its own work",
                       "self-approval", "scope expansion"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, row)


class WorkerPolicyTests(unittest.TestCase):
    def test_policy_adds_worker_rules_and_keeps_frozen_fields(self):
        c = contracts()
        policy = c.parse_policy((SKILL / "policies/roles.yaml").read_text(encoding="utf-8"))
        c.validate_policy(policy)
        worker = policy["roles"]["worker"]
        self.assertEqual(worker["abilities"], ["implement"])
        self.assertTrue(worker["application_code"])
        joined = " ".join(worker["responsibilities"])
        for phrase in ("Fresh native implementation attempt within approved scope",
                       "Follows Planner-authored task instructions exactly and in order",
                       "Performs developer checks", "does not plan, review or change scope",
                       "Reports blocked", "Cannot self-approve"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, joined)
        self.assertEqual(policy["workflow"]["order"],
                         ["owner", "planner", "manager", "worker", "tester", "reviewer", "manager", "planner", "owner"])


class WorkerBlockedReportTests(unittest.TestCase):
    def blocked_report(self):
        candidate = {"artifact_id": "input", "path": "synthetic/input.json", "sha256": "0" * 64, "kind": "synthetic"}
        return {"protocol": "council-flow", "version": "1.0", "message_id": "WR1",
                "message_type": "job.report", "plan_id": "P1", "plan_revision": 1, "task_id": "T1",
                "attempt_id": "A1", "sender": {"role": "worker", "instance_id": "worker-1"},
                "recipient": {"role": "manager", "instance_id": "manager-1"}, "in_reply_to": "W1",
                "payload": {"status": "blocked", "summary": "Instruction 2 contradicts the code; nothing edited.",
                            "acceptance_ids": ["AC1"], "candidate_ref": candidate, "input_candidate_ref": candidate,
                            "changed_files": [], "findings": ["Instruction 2 names a function that does not exist."],
                            "errors": []},
                "evidence_refs": [candidate]}

    def test_blocked_worker_report_with_no_edits_is_valid(self):
        c = contracts()
        c.validate_message(self.blocked_report(),
                           expected_sender={"role": "worker", "instance_id": "worker-1"})

    def test_blocked_worker_report_still_needs_candidate_and_changed_files(self):
        c = contracts()
        for field in ("candidate_ref", "changed_files"):
            report = self.blocked_report()
            del report["payload"][field]
            with self.subTest(field=field), self.assertRaises(c.ContractError):
                c.validate_message(report)


if __name__ == "__main__":
    unittest.main()
