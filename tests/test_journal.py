import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "multi-agent-evolution"))

from journal import Journal, JournalError


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "runs.sqlite3"
        self.journal = Journal(self.path)
        self.run_id = self.journal.create_run("run-1", "plan-1", "a" * 64)

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, **overrides):
        run = self.journal.get_run(self.run_id)
        events = json.loads(self.journal.export(self.run_id))["events"]
        payload = {
            "attempt_id": run.get("attempt_id", "attempt-1"),
            "attempt_revision": run.get("attempt_revision", 0),
            "parent_event_id": events[-1]["event_id"] if events else None,
            "actor_claim": {"role": "Manager", "identity": "claimed-id", "session_ref": "claimed-session"},
            "criteria_ref": "criteria/C1",
            "candidate_artifact": None,
            "terminal_reason": None,
            "approval_ref": None,
            "evidence_refs": ["opaque-ref"],
        }
        payload.update(overrides)
        return payload

    def advance_to_planner_check(self, candidate_artifact=None):
        states = ["READY", "ASSIGNED", "RUNNING", "CANDIDATE", "TESTING", "REVIEWING", "MANAGER_DECISION", "PLANNER_CHECK"]
        revision = 0
        for state in states:
            payload = self.payload(candidate_artifact=candidate_artifact if state == "CANDIDATE" else None)
            revision = self.journal.transition(self.run_id, revision, state, payload)
        return revision

    def accept(self, candidate_artifact):
        revision = self.advance_to_planner_check(candidate_artifact)
        payload = self.payload(
            criteria_ids=["C1"], candidate_sha256=candidate_artifact["sha256"],
            tester_ref="tester", reviewer_ref="reviewer", planner_check_ref="planner",
            manager_decision_ref="manager", candidate_artifact=candidate_artifact,
            approval_ref="approval-claim",
        )
        return self.journal.transition(self.run_id, revision, "ACCEPTED", payload)

    def test_compare_and_swap_rejects_stale_revision(self):
        self.journal.transition(self.run_id, 0, "READY", self.payload())
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "ASSIGNED", self.payload())
        other_connection = Journal(self.path)
        with self.assertRaises(JournalError):
            other_connection.transition(self.run_id, 0, "ASSIGNED", self.payload())

    def test_boolean_revisions_and_unhashable_states_are_rejected(self):
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, True, "READY", self.payload())
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, False, "READY", self.payload())
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, [], self.payload())

    def test_cannot_skip_review_roles_or_accept_without_acceptance_metadata(self):
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "ACCEPTED", self.payload())
        revision = self.advance_to_planner_check()
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, revision, "ACCEPTED", self.payload())

    def test_event_replay_parent_mismatch_and_revision_gap_are_rejected(self):
        first = self.payload()
        self.journal.transition(self.run_id, 0, "READY", first, event_id="event-1")
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 1, "ASSIGNED", self.payload(parent_event_id=None), event_id="event-1")
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 1, "ASSIGNED", self.payload(parent_event_id="wrong-parent"))
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 2, "ASSIGNED", self.payload())

    def test_attempt_identity_increments_only_after_rework(self):
        revision = 0
        for state in ["READY", "ASSIGNED", "RUNNING", "CANDIDATE", "TESTING"]:
            revision = self.journal.transition(self.run_id, revision, state, self.payload())
        revision = self.journal.transition(self.run_id, revision, "REWORK_REQUIRED", self.payload())
        before = self.journal.get_run(self.run_id)
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, revision, "READY", self.payload())
        payload = self.payload(attempt_id="attempt-2", attempt_revision=1)
        revision = self.journal.transition(self.run_id, revision, "READY", payload)
        after = self.journal.get_run(self.run_id)
        self.assertEqual(after["attempt_id"], "attempt-2")
        self.assertEqual(after["attempt_revision"], before["attempt_revision"] + 1)
        self.assertEqual(revision, 7)

    def test_payload_types_are_strict_and_references_remain_opaque(self):
        bad = self.payload(attempt_revision=True)
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "READY", bad)
        bad = self.payload(actor_claim=[])
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "READY", bad)
        self.journal.transition(self.run_id, 0, "READY", self.payload(evidence_refs=["../../outside.txt"]))
        self.assertIn("../../outside.txt", self.journal.export(self.run_id))

    def test_schema_v2_is_persisted_and_exports_are_stable(self):
        self.journal.transition(self.run_id, 0, "READY", self.payload())
        reopened = Journal(self.path)
        self.assertEqual(self.journal.export(self.run_id), reopened.export(self.run_id))
        self.assertEqual(json.loads(reopened.export(self.run_id))["schema_version"], 2)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0], "2")

    def test_v1_is_preserved_and_available_only_for_readonly_export(self):
        path = self.root / "legacy-v1.sqlite3"
        with sqlite3.connect(path) as db:
            db.executescript("""
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE runs (run_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, plan_sha256 TEXT NOT NULL, state TEXT NOT NULL, revision INTEGER NOT NULL);
                CREATE TABLE events (event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, revision INTEGER NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL);
                INSERT INTO metadata VALUES ('schema_version', '1');
                INSERT INTO runs VALUES ('legacy-run', 'plan', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'READY', 1);
                INSERT INTO events VALUES ('legacy-event', 'legacy-run', 1, 'READY', '{"evidence_refs":["opaque"]}');
            """)
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(JournalError):
            Journal(path)
        readonly = Journal.open_readonly(path)
        self.assertEqual(json.loads(readonly.export("legacy-run"))["schema_version"], 1)
        with self.assertRaises(JournalError):
            readonly.transition("legacy-run", 1, "ASSIGNED", {})
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_candidate_artifact_bytes_are_verified_and_actor_claims_stay_unverified(self):
        candidate = self.root / "candidate.bin"
        candidate.write_bytes(b"verified local candidate")
        artifact = {"path": "candidate.bin", "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()}
        self.accept(artifact)
        report = self.journal.verify_run(self.run_id, self.root)
        self.assertEqual(report["integrity_status"], "PASS")
        self.assertTrue(any(c["name"] == "actor_claim" and c["status"] == "UNVERIFIED" for c in report["checks"]))
        self.assertTrue(any(c["name"] == "approval_claim" and c["status"] == "UNVERIFIED" for c in report["checks"]))

    def test_missing_mismatched_symlink_and_fifo_artifacts_fail_closed(self):
        self.assertEqual(self.journal.verify_run(self.run_id, self.root)["integrity_status"], "BLOCKED")
        regular = self.root / "candidate.bin"
        regular.write_bytes(b"candidate")
        descriptor = {"path": "candidate.bin", "sha256": "0" * 64}
        revision = self.journal.transition(self.run_id, 0, "READY", self.payload(candidate_artifact=descriptor))
        report = self.journal.verify_run(self.run_id, self.root)
        self.assertEqual(report["integrity_status"], "FAIL")
        self.assertIn("DIGEST_MISMATCH", self.journal.reconcile(self.run_id, self.root)["reason_codes"])

        for unsafe in ("../outside", "/absolute/file", "C:/outside/file"):
            with self.subTest(path=unsafe), self.assertRaises(JournalError):
                self.journal.transition(self.run_id, revision, "ASSIGNED", self.payload(candidate_artifact={"path": unsafe, "sha256": "0" * 64}))

        def verify_unsafe_path(name):
            db_path = self.root / f"{name}.sqlite3"
            local = Journal(db_path)
            local_run = local.create_run(name, "plan", "b" * 64)
            payload = {
                "attempt_id": local.get_run(local_run).get("attempt_id", "attempt-1"),
                "attempt_revision": 0, "parent_event_id": None,
                "actor_claim": {"role": "Manager", "identity": "id", "session_ref": "session"},
                "criteria_ref": "criteria", "candidate_artifact": {"path": name, "sha256": "0" * 64},
                "terminal_reason": None, "approval_ref": None,
            }
            local.transition(local_run, 0, "READY", payload)
            return local.verify_run(local_run, self.root)["integrity_status"]

        if hasattr(os, "symlink"):
            (self.root / "link.bin").symlink_to(regular)
            self.assertEqual(verify_unsafe_path("link.bin"), "BLOCKED")
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.root / "pipe.bin")
            self.assertEqual(verify_unsafe_path("pipe.bin"), "BLOCKED")

    def test_nonacceptance_terminals_require_a_reason(self):
        for field, state in (("BLOCKED", "BLOCKED"), ("CANCELLED", "CANCELLED"), ("REJECTED", "REJECTED")):
            with self.subTest(state=state):
                journal = Journal(self.root / f"{field}.sqlite3")
                run_id = journal.create_run(field, "plan", "c" * 64)
                with self.assertRaises(JournalError):
                    journal.transition(run_id, 0, state, {
                        "attempt_id": journal.get_run(run_id)["attempt_id"], "attempt_revision": 0,
                        "parent_event_id": None, "actor_claim": {"role": "Manager", "identity": "id", "session_ref": "session"},
                        "criteria_ref": "criteria", "candidate_artifact": None,
                        "terminal_reason": None, "approval_ref": None,
                    })

    def test_event_chain_corruption_is_reported_and_reconciliation_does_not_repair(self):
        self.journal.transition(self.run_id, 0, "READY", self.payload())
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET payload=? WHERE run_id=?", (json.dumps(self.payload(parent_event_id="forged-parent")), self.run_id))
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        report = self.journal.verify_run(self.run_id, self.root)
        result = self.journal.reconcile(self.run_id, self.root)
        self.assertEqual(report["integrity_status"], "FAIL")
        self.assertEqual(result["recovery_status"], "RECOVERY_REQUIRED")
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)

    def test_reconcile_is_readonly_and_never_promotes_claims_to_authority(self):
        candidate = self.root / "candidate.bin"
        candidate.write_bytes(b"candidate")
        artifact = {"path": "candidate.bin", "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest()}
        self.accept(artifact)
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        result = self.journal.reconcile(self.run_id, self.root)
        self.assertEqual(result["recovery_status"], "COMPLETE_RECORD")
        self.assertIn("UNVERIFIED_ACTOR", result["reason_codes"])
        self.assertIn("UNVERIFIED_APPROVAL", result["reason_codes"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), before)

    def test_sqlite_failure_rolls_back_event_and_run_state(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'injected'); END")
        with self.assertRaises(JournalError):
            self.journal.transition(self.run_id, 0, "READY", self.payload())
        self.assertEqual(self.journal.get_run(self.run_id)["revision"], 0)
        self.assertEqual(json.loads(self.journal.export(self.run_id))["events"], [])

        other_path = self.root / "state-update.sqlite3"
        other = Journal(other_path)
        other_run = other.create_run("state-run", "plan", "d" * 64)
        with sqlite3.connect(other_path) as db:
            db.execute("CREATE TRIGGER reject_state BEFORE UPDATE OF state ON runs BEGIN SELECT RAISE(ABORT, 'injected'); END")
        payload = {
            "attempt_id": other.get_run(other_run)["attempt_id"], "attempt_revision": 0,
            "parent_event_id": None, "actor_claim": {"role": "Manager", "identity": "id", "session_ref": "session"},
            "criteria_ref": "criteria", "candidate_artifact": None,
            "terminal_reason": None, "approval_ref": None,
        }
        with self.assertRaises(JournalError):
            other.transition(other_run, 0, "READY", payload)
        self.assertEqual(other.get_run(other_run)["revision"], 0)
        self.assertEqual(json.loads(other.export(other_run))["events"], [])

    def test_commit_failure_leaves_run_and_event_log_unchanged(self):
        real_connect = sqlite3.connect

        class CommitFailure:
            def __init__(self, *args, **kwargs):
                object.__setattr__(self, "connection", real_connect(*args, **kwargs))

            def __getattr__(self, name):
                return getattr(self.connection, name)

            def __setattr__(self, name, value):
                setattr(self.connection, name, value)

            def commit(self):
                raise sqlite3.OperationalError("injected commit failure")

        with patch("journal.sqlite3.connect", side_effect=lambda *args, **kwargs: CommitFailure(*args, **kwargs)):
            with self.assertRaises(sqlite3.OperationalError):
                self.journal.transition(self.run_id, 0, "READY", self.payload())
        self.assertEqual(self.journal.get_run(self.run_id)["revision"], 0)
        self.assertEqual(json.loads(self.journal.export(self.run_id))["events"], [])

    def test_corrupt_event_json_is_reported_as_integrity_failure(self):
        self.journal.transition(self.run_id, 0, "READY", self.payload())
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET payload='not-json' WHERE run_id=?", (self.run_id,))
        report = self.journal.verify_run(self.run_id, self.root)
        self.assertEqual(report["integrity_status"], "FAIL")
        with self.assertRaises(JournalError):
            self.journal.export(self.run_id)


if __name__ == "__main__":
    unittest.main()
