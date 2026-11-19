import tempfile
import unittest
import sqlite3
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "multi-agent-evolution"))

from journal import Journal, JournalError


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.journal = Journal(Path(self.temp.name) / "runs.sqlite3")
        self.run_id = self.journal.create_run("run-1", "plan-1", "a" * 64)

    def tearDown(self):
        self.temp.cleanup()

    def test_compare_and_swap_rejects_stale_revision(self):
        self.journal.transition(self.run_id, 0, "READY", {"evidence_refs": []})
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "ASSIGNED", {"evidence_refs": []})

    def test_cannot_skip_review_roles_or_accept_from_wrong_state(self):
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "ACCEPTED", {"evidence_refs": []})

    def test_event_replay_is_rejected(self):
        self.journal.transition(self.run_id, 0, "READY", {"evidence_refs": []}, event_id="event-1")
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 1, "ASSIGNED", {"evidence_refs": []}, event_id="event-1")

    def test_journal_rejects_prompt_or_arbitrary_payload_fields(self):
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "READY", {"prompt": "private text"})

    def test_schema_version_is_persisted_and_evidence_refs_are_opaque(self):
        self.journal.transition(self.run_id, 0, "READY", {"evidence_refs": ["../../outside.txt"]})
        exported = self.journal.export(self.run_id)
        self.assertIn('"schema_version": 1', exported)
        self.assertIn("../../outside.txt", exported)
        with sqlite3.connect(self.journal.path) as db:
            self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0], "1")

    def test_unsupported_database_schema_version_is_rejected(self):
        path = Path(self.temp.name) / "future.sqlite3"
        Journal(path)
        with sqlite3.connect(path) as db:
            db.execute("UPDATE metadata SET value='2' WHERE key='schema_version'")
        with self.assertRaises(JournalError):
            Journal(path)

    def test_export_is_deterministic_and_contains_references_only(self):
        self.journal.transition(self.run_id, 0, "READY", {"evidence_refs": ["evidence.json"]})
        reopened = Journal(self.journal.path)
        self.assertEqual(self.journal.export(self.run_id), reopened.export(self.run_id))

    def test_acceptance_requires_complete_role_and_evidence_references(self):
        states = ["READY", "ASSIGNED", "RUNNING", "CANDIDATE", "TESTING", "REVIEWING", "MANAGER_DECISION", "PLANNER_CHECK"]
        revision = 0
        for state in states:
            revision = self.journal.transition(self.run_id, revision, state, {"evidence_refs": ["ref"]})
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, revision, "ACCEPTED", {"evidence_refs": []})

    def test_acceptance_requires_well_formed_candidate_hash_and_accepts_complete_metadata(self):
        states = ["READY", "ASSIGNED", "RUNNING", "CANDIDATE", "TESTING", "REVIEWING", "MANAGER_DECISION", "PLANNER_CHECK"]
        revision = 0
        for state in states:
            revision = self.journal.transition(self.run_id, revision, state, {"evidence_refs": ["opaque-ref"]})
        complete = {"criteria_ids": ["C1"], "candidate_sha256": "a" * 64,
                    "tester_ref": "tester", "reviewer_ref": "reviewer", "planner_check_ref": "planner",
                    "manager_decision_ref": "manager", "evidence_refs": ["opaque-ref"]}
        malformed = dict(complete, candidate_sha256="z" * 64)
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, revision, "ACCEPTED", malformed)
        accepted_revision = self.journal.transition(self.run_id, revision, "ACCEPTED", complete)
        self.assertEqual(accepted_revision, revision + 1)
        self.assertEqual(self.journal.get_run(self.run_id)["state"], "ACCEPTED")


if __name__ == "__main__":
    unittest.main()
