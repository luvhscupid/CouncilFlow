"""Opt-in local metadata journal; it is not an authorization or identity system."""

import json
import sqlite3
import uuid
from contextlib import closing


class JournalError(ValueError):
    pass


_NEXT = {
    "PLANNED": {"READY", "BLOCKED", "CANCELLED"},
    "READY": {"ASSIGNED", "BLOCKED", "CANCELLED"},
    "ASSIGNED": {"RUNNING", "BLOCKED", "CANCELLED"},
    "RUNNING": {"CANDIDATE", "BLOCKED", "CANCELLED"},
    "CANDIDATE": {"TESTING", "BLOCKED", "CANCELLED"},
    "TESTING": {"REVIEWING", "REWORK_REQUIRED", "BLOCKED", "REJECTED"},
    "REVIEWING": {"MANAGER_DECISION", "REWORK_REQUIRED", "BLOCKED", "REJECTED"},
    "MANAGER_DECISION": {"PLANNER_CHECK", "REWORK_REQUIRED", "BLOCKED", "REJECTED"},
    "PLANNER_CHECK": {"ACCEPTED", "REWORK_REQUIRED", "BLOCKED", "REJECTED"},
    "REWORK_REQUIRED": {"READY", "CANCELLED", "BLOCKED"},
}
_TERMINAL = {"ACCEPTED", "BLOCKED", "CANCELLED", "REJECTED"}
_PAYLOAD_KEYS = {"evidence_refs", "criteria_ids", "candidate_sha256", "tester_ref",
                 "reviewer_ref", "planner_check_ref", "manager_decision_ref", "reason"}


class Journal:
    def __init__(self, path):
        self.path = str(path)
        with closing(self._connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, plan_sha256 TEXT NOT NULL, state TEXT NOT NULL, revision INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, revision INTEGER NOT NULL, state TEXT NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(run_id) REFERENCES runs(run_id))")
            version = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if version is None:
                db.execute("INSERT INTO metadata VALUES ('schema_version', '1')")
            elif version["value"] != "1":
                raise JournalError("unsupported journal schema version")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def create_run(self, run_id, plan_ref, plan_sha256):
        if not all(isinstance(v, str) and v.strip() for v in (run_id, plan_ref)):
            raise JournalError("run_id and plan_ref must be non-empty strings")
        if not isinstance(plan_sha256, str) or len(plan_sha256) != 64 or any(c not in "0123456789abcdef" for c in plan_sha256):
            raise JournalError("plan_sha256 must be a lowercase SHA-256 hex digest")
        try:
            with closing(self._connect()) as db:
                db.execute("INSERT INTO runs VALUES (?, ?, ?, 'PLANNED', 0)", (run_id, plan_ref, plan_sha256))
        except sqlite3.IntegrityError as exc:
            raise JournalError("run already exists") from exc
        return run_id

    def transition(self, run_id, expected_revision, new_state, payload, event_id=None):
        if not isinstance(payload, dict):
            raise JournalError("event payload must be an object")
        if not set(payload).issubset(_PAYLOAD_KEYS):
            raise JournalError("event payload contains unsupported fields")
        for key, value in payload.items():
            if key in {"evidence_refs", "criteria_ids"}:
                if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                    raise JournalError(f"{key} must be a list of non-empty references")
            elif not isinstance(value, str) or not value.strip():
                raise JournalError(f"{key} must be a non-empty string")
        if new_state not in _NEXT and new_state not in _TERMINAL:
            raise JournalError("unknown state")
        event_id = event_id or str(uuid.uuid4())
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT state, revision FROM runs WHERE run_id=?", (run_id,)).fetchone()
                if row is None:
                    raise JournalError("unknown run")
                if row["revision"] != expected_revision:
                    raise JournalError("stale revision")
                if new_state not in _NEXT.get(row["state"], set()):
                    raise JournalError("invalid state transition")
                if new_state == "ACCEPTED":
                    required = {"criteria_ids", "candidate_sha256", "tester_ref", "reviewer_ref",
                                "planner_check_ref", "manager_decision_ref", "evidence_refs"}
                    if not required.issubset(payload) or any(not payload[key] for key in required):
                        raise JournalError("acceptance requires complete role, criteria, candidate, and evidence references")
                    digest = payload["candidate_sha256"]
                    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                        raise JournalError("candidate_sha256 must be a lowercase SHA-256 digest")
                revision = expected_revision + 1
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)", (event_id, run_id, revision, new_state, body))
                changed = db.execute("UPDATE runs SET state=?, revision=? WHERE run_id=? AND revision=?", (new_state, revision, run_id, expected_revision)).rowcount
                if changed != 1:
                    raise JournalError("concurrent state change")
                db.commit()
                return revision
        except sqlite3.IntegrityError as exc:
            raise JournalError("duplicate event or invalid record") from exc

    def get_run(self, run_id):
        with closing(self._connect()) as db:
            row = db.execute("SELECT run_id, plan_ref, plan_sha256, state, revision FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def export(self, run_id):
        with closing(self._connect()) as db:
            run = db.execute("SELECT run_id, plan_ref, plan_sha256, state, revision FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise JournalError("unknown run")
            events = db.execute("SELECT event_id, revision, state, payload FROM events WHERE run_id=? ORDER BY revision", (run_id,)).fetchall()
        return json.dumps({"schema_version": 1, "run": dict(run), "events": [
            {"event_id": e["event_id"], "revision": e["revision"], "state": e["state"], "payload": json.loads(e["payload"])} for e in events
        ]}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
