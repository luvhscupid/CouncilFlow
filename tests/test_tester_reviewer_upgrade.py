"""Static checks for the Tester's test-only and the Reviewer's compare-only duties.

These are repository checks; they do not prove native host dispatch behavior.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/council-flow"
PLUGIN = ROOT / "plugins/councilflow"
# The Codex release archive ships without plugins/; plugin checks run only in a checkout.
HAS_PLUGIN = PLUGIN.is_dir()

# Rules both copies of each role must state, in the same words.
TESTER_RULES = (
    "Manager-approved verification strategy",
    "follow them exactly, in order, as written",
    "run every check they name against the exact candidate",
    "recording real exit results",
    "Test only",
    "do not plan, reorder or drop checks, change criteria or scope, review code quality, or repair the product",
    "stop and return job.report status blocked with the reason as a finding",
    "mark each check you could not run blocked or unverified, never passed",
    "reported failed with its evidence",
    "Worker-authored tests alone do not prove correctness",
    "executable path",
)
REVIEWER_RULES = (
    "Manager-assigned review instructions",
    "follow them exactly, in order, as written",
    "Compare only",
    "do not plan, repair, retest in place of the Tester, or approve",
    "stop and return job.report status blocked with the reason as a finding",
    "never guess the missing input",
    "Record every discrepancy",
    "pass only with a MATCH rerun and no discrepancies",
    "never substitute a shell alias",
    "NOT_COMPARABLE",
)
WORKFLOW_ORDER = ["owner", "planner", "manager", "worker", "tester", "reviewer", "manager", "planner", "owner"]


def text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def contracts():
    sys.path.insert(0, str(SKILL / "scripts"))
    try:
        import contracts as module
    finally:
        sys.path.pop(0)
    return module


def role_files(role):
    files = [ROOT / f".codex/agents/council-{role}.toml"]
    if HAS_PLUGIN:
        files.append(PLUGIN / f"agents/council-{role}.md")
    return files


class TesterReviewerTextTests(unittest.TestCase):
    def test_both_copies_state_every_rule(self):
        for role, rules in (("tester", TESTER_RULES), ("reviewer", REVIEWER_RULES)):
            for path in role_files(role):
                body = text(path)
                for rule in rules:
                    with self.subTest(path=path.relative_to(ROOT).as_posix(), rule=rule):
                        self.assertIn(rule, body)

    @unittest.skipUnless(HAS_PLUGIN, "plugin package not present in this extraction")
    def test_plugin_copies_keep_tools_without_edit(self):
        for role in ("tester", "reviewer"):
            header = (PLUGIN / f"agents/council-{role}.md").read_text(encoding="utf-8").split("---")[1]
            with self.subTest(role=role):
                self.assertIn("tools: Read, Grep, Glob, Bash, Write", header)
                self.assertNotIn("Edit", header)

    def test_roles_reference_lists_rules(self):
        lines = (SKILL / "references/roles.md").read_text(encoding="utf-8").splitlines()
        expected = {
            "| Tester |": ("verification instructions and oracle exactly and in order", "status blocked",
                           "Product repairs", "planning", "changing criteria or scope", "reviewing code quality",
                           "self-approval of its oracle", "reporting an unrun check as passed"),
            "| Reviewer |": ("review instructions exactly and in order", "status blocked",
                             "Implementation", "planning", "retesting in place of Tester", "approving",
                             "criteria changes", "replacing Tester"),
        }
        for prefix, phrases in expected.items():
            rows = [line for line in lines if line.startswith(prefix)]
            self.assertEqual(len(rows), 1)
            for phrase in phrases:
                with self.subTest(row=prefix, phrase=phrase):
                    self.assertIn(phrase, rows[0])


class TesterReviewerPolicyTests(unittest.TestCase):
    def test_policy_adds_rules_and_keeps_frozen_fields(self):
        c = contracts()
        policy = c.parse_policy((SKILL / "policies/roles.yaml").read_text(encoding="utf-8"))
        c.validate_policy(policy)
        tester, reviewer = policy["roles"]["tester"], policy["roles"]["reviewer"]
        self.assertEqual(tester["abilities"], ["technical_test"])
        self.assertEqual(reviewer["abilities"], ["compare_evidence", "independent_rerun"])
        self.assertFalse(tester["application_code"])
        self.assertFalse(reviewer["application_code"])
        for role, phrases in (
            (tester, ("Independent technical verification of exact candidate",
                      "Follows the assigned verification instructions and oracle exactly and in order",
                      "Tests only", "Does not repair product", "Reports blocked instead of guessing",
                      "Does not approve its own oracle")),
            (reviewer, ("Independently compares frozen plan and acceptance",
                        "Follows the assigned review instructions exactly and in order",
                        "Reruns one Tester-declared deterministic command", "Compares only",
                        "Reports blocked instead of guessing", "Does not implement, alter criteria, or replace Tester")),
        ):
            joined = " ".join(role["responsibilities"])
            for phrase in phrases:
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, joined)
        self.assertEqual(policy["workflow"]["order"], WORKFLOW_ORDER)
        self.assertFalse(policy["evidence"]["tester_self_approves_oracle"])
        self.assertTrue(policy["context"]["independent_tester"])
        self.assertTrue(policy["context"]["independent_reviewer"])


def ref(artifact_id, kind="synthetic"):
    return {"artifact_id": artifact_id, "path": f"synthetic/{artifact_id}.json", "sha256": "0" * 64, "kind": kind}


def envelope(role, payload):
    return {"protocol": "council-flow", "version": "1.0", "message_id": f"{role[0].upper()}R1",
            "message_type": "job.report", "plan_id": "P1", "plan_revision": 1, "task_id": "T1",
            "attempt_id": "A1", "sender": {"role": role, "instance_id": f"{role}-1"},
            "recipient": {"role": "manager", "instance_id": "manager-1"}, "in_reply_to": "J1",
            "payload": payload, "evidence_refs": [ref("evidence")]}


class BlockedReportTests(unittest.TestCase):
    def make_tester_report(self, status, check_status):
        return envelope("tester", {
            "status": status, "summary": "Oracle hash does not match the assignment; no check was run.",
            "acceptance_ids": ["AC1"], "candidate_ref": ref("candidate"), "oracle_ref": ref("oracle"),
            "checks": [{"name": "AC1 original oracle", "status": check_status, "evidence_ref": ref("evidence")}],
            "deterministic_commands": [], "findings": ["oracle_ref hash differs from the assigned strategy."],
            "errors": []})

    def make_reviewer_report(self, status, discrepancies):
        return envelope("reviewer", {
            "status": status, "summary": "Tester report is missing from the assignment; nothing compared.",
            "acceptance_ids": ["AC1"], "candidate_ref": ref("candidate"),
            "comparison": {"plan_ref": ref("plan"), "tester_report_ref": ref("TR1", "message"),
                           "candidate_ref": ref("candidate"), "findings": ["Tester report not supplied."],
                           "discrepancies": discrepancies, "independent_rerun": {"status": "NOT_COMPARABLE"}},
            "findings": ["Blocked: assigned Tester report is missing."], "errors": []})

    def test_blocked_tester_report_with_unrun_checks_is_valid(self):
        c = contracts()
        for check_status in ("blocked", "unverified"):
            with self.subTest(check_status=check_status):
                c.validate_message(self.make_tester_report("blocked", check_status),
                                   expected_sender={"role": "tester", "instance_id": "tester-1"})

    def test_tester_cannot_pass_with_an_unrun_check(self):
        c = contracts()
        for check_status in ("blocked", "unverified", "failed"):
            with self.subTest(check_status=check_status), self.assertRaises(c.ContractError):
                c.validate_message(self.make_tester_report("passed", check_status))

    def test_blocked_reviewer_report_is_valid(self):
        c = contracts()
        c.validate_message(self.make_reviewer_report("blocked", ["Tester report missing."]),
                           expected_sender={"role": "reviewer", "instance_id": "reviewer-1"})

    def test_reviewer_cannot_pass_without_match_or_with_discrepancies(self):
        c = contracts()
        for discrepancies in ([], ["Candidate hash differs from plan."]):
            with self.subTest(discrepancies=discrepancies), self.assertRaises(c.ContractError):
                c.validate_message(self.make_reviewer_report("passed", discrepancies))


if __name__ == "__main__":
    unittest.main()
