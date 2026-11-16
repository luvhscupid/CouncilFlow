"""Regression: every Worker, Tester and Reviewer report needs a prior Manager job.assign.

Uses the real contract validator (validate_sequence and the plugin's contracts.py
CLI), not documentation string checks. Actors and hashes are synthetic fixtures:
this proves the causal-link rules only, not native subagent identity or activation.
"""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fixtures

c = fixtures.c
ROOT = Path(__file__).resolve().parents[1]
PLUGIN_CONTRACTS = ROOT / "plugins/councilflow/skills/run/scripts/contracts.py"


def by_id(messages, mid):
    return next(m for m in messages if m["message_id"] == mid)


class DispatchLifecycleTests(unittest.TestCase):
    def assertRejected(self, messages, field=None):
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence(messages)
        if field is not None:
            self.assertEqual(failure.exception.field, field)
        return failure.exception

    def test_correctly_linked_worker_tester_reviewer_sequence_passes(self):
        """Worker, Tester and Reviewer each reply to a prior Manager assignment."""
        data = fixtures.sequence()
        c.validate_sequence(data)
        # Each report replies to the assignment immediately before it.
        self.assertEqual(by_id(data, "M3")["in_reply_to"], "M2")
        self.assertEqual(by_id(data, "M5")["in_reply_to"], "M4")
        self.assertEqual(by_id(data, "M7")["in_reply_to"], "M6")
        self.assertEqual(by_id(data, "M6")["message_type"], "job.assign")
        self.assertEqual(by_id(data, "M6")["recipient"]["role"], "reviewer")

    def test_reviewer_report_without_matching_assignment_is_rejected(self):
        """The observed defect: Reviewer report M5-equivalent replies to the Tester
        report, with no Manager job.assign for the Reviewer in between."""
        data = fixtures.sequence()
        del data[5]  # remove the Reviewer job.assign (M6)
        self.assertRejected(data, field="in_reply_to")

    def test_reviewer_report_replying_to_tester_report_is_rejected_cli(self):
        """Same defect through the plugin's own CLI, as the Manager would run it."""
        import tempfile
        data = fixtures.sequence()
        del data[5]
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, message in enumerate(data):
                path = Path(tmp) / f"M{index}.json"
                path.write_text(json.dumps(message), encoding="utf-8")
                paths.append(str(path))
            proc = subprocess.run(
                [sys.executable, "-I", str(PLUGIN_CONTRACTS), "sequence", *paths],
                capture_output=True, text=True, timeout=60,
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('"valid": false', proc.stderr)
        self.assertIn("in_reply_to", proc.stderr)

    def test_wrong_in_reply_to_is_rejected(self):
        data = fixtures.sequence()
        # The Reviewer report points at the Tester report, not its assignment.
        by_id(data, "M7")["in_reply_to"] = "M5"
        self.assertRejected(data)

    def test_reviewer_report_must_not_reply_to_a_non_assignment(self):
        """A report replying to a non-assignment (e.g. the Worker report M3) is rejected."""
        data = fixtures.sequence()
        by_id(data, "M7")["in_reply_to"] = "M3"
        self.assertRejected(data, field="in_reply_to")

    def test_stale_candidate_identity_is_rejected(self):
        """Reviewer assignment carries a candidate different from the Tester's."""
        data = fixtures.sequence()
        stale = fixtures.ref("stale-candidate", "synthetic/old.json", "f" * 64, "candidate")
        by_id(data, "M6")["payload"]["candidate_ref"] = stale
        self.assertRejected(data)

    def test_missing_required_reviewer_evidence_is_rejected(self):
        """A Reviewer report that drops its independent-rerun evidence fails."""
        data = fixtures.sequence()
        reviewer = copy.deepcopy(by_id(data, "M7"))
        reviewer["payload"].pop("comparison", None)
        data[6] = reviewer
        self.assertRejected(data)

    def test_reviewer_chain_without_worker_report_is_rejected(self):
        """The Reviewer must bind the Worker's actual candidate report. Removing the
        Worker job.report (M3) that the Tester and Reviewer depend on must fail."""
        data = [m for m in fixtures.sequence() if m["message_id"] != "M3"]
        # M4 still replies to the missing M3, so the first failing causal check may vary.
        self.assertRejected(data)

    def test_tester_assignment_without_worker_report_is_rejected(self):
        """Tester dispatch needs a persisted, candidate-bound Worker report first."""
        data = [m for m in fixtures.sequence() if m["message_id"] != "M3"]
        self.assertRejected(data)

    def test_worker_report_with_null_candidate_ref_is_rejected(self):
        """A chat-style Worker report with candidate_ref null cannot anchor a candidate."""
        data = fixtures.sequence()
        by_id(data, "M3")["payload"]["candidate_ref"] = None
        self.assertRejected(data)

    def test_worker_report_must_reply_to_its_actual_assignment(self):
        """The Worker report must reply to the Worker job.assign (M2), not another message."""
        data = fixtures.sequence()
        by_id(data, "M3")["in_reply_to"] = "M1"
        self.assertRejected(data)

    def test_reviewer_tester_report_ref_must_use_tester_message_id(self):
        """The Reviewer must cite the Tester message by its message_id, not a label."""
        data = fixtures.sequence()
        reviewer = by_id(data, "M7")
        reviewer["payload"]["comparison"]["tester_report_ref"]["artifact_id"] = "calc-001-tester-report"
        self.assertRejected(data, field="payload.comparison.tester_report_ref")

    @unittest.expectedFailure
    def test_reviewer_may_cite_corrective_tester_when_earlier_superseded_report_exists(self):
        """KNOWN VALIDATOR DEFECT (expected failure until the shared contract is fixed).

        After a Tester report M5 is superseded by a corrective Tester report M5b on the
        same candidate, the Reviewer must be able to cite M5b. contracts.py selects the
        first candidate-matched Tester in the whole context (M5), so a Reviewer that
        correctly cites M5b is rejected. Fixing this changes the shared canonical
        validator, which also serves Codex, so it needs explicit approval first.
        """
        data = fixtures.sequence()
        corrective_assign = copy.deepcopy(by_id(data, "M4"))
        corrective_assign["message_id"] = "M4b"
        corrective_assign["in_reply_to"] = "M3"
        corrective_report = copy.deepcopy(by_id(data, "M5"))
        corrective_report["message_id"] = "M5b"
        corrective_report["in_reply_to"] = "M4b"
        reviewer_assign = copy.deepcopy(by_id(data, "M6"))
        reviewer_assign["in_reply_to"] = "M5b"
        reviewer_report = by_id(data, "M7")
        reviewer_report["in_reply_to"] = "M6"
        reviewer_report["payload"]["comparison"]["tester_report_ref"]["artifact_id"] = "M5b"
        # Real history keeps the superseded M5: M4b replies to M3, M5b replies to M4b.
        chain = [m for m in data if m["message_id"] in {"M1", "M2", "M3", "M4", "M5"}]
        chain += [corrective_assign, corrective_report, reviewer_assign, reviewer_report]
        c.validate_sequence(chain)

    def test_existing_worker_and_tester_handoffs_stay_valid(self):
        """Worker and Tester legs of the chain are unchanged by the fix."""
        data = fixtures.sequence()[:5]  # plan, worker assign/report, tester assign/report
        c.validate_sequence(data)


if __name__ == "__main__":
    unittest.main()
