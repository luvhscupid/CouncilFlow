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

    def test_existing_worker_and_tester_handoffs_stay_valid(self):
        """Worker and Tester legs of the chain are unchanged by the fix."""
        data = fixtures.sequence()[:5]  # plan, worker assign/report, tester assign/report
        c.validate_sequence(data)


if __name__ == "__main__":
    unittest.main()
