"""Experimental local metadata journal; it does not authenticate or authorize."""

import hashlib
import json
import ntpath
import os
import sqlite3
import stat
import uuid
from contextlib import closing
from pathlib import Path


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
_EVENT_KEYS = {
    "attempt_id", "attempt_revision", "parent_event_id", "actor_claim", "criteria_ref",
    "candidate_artifact", "terminal_reason", "approval_ref", "evidence_refs",
    "criteria_ids", "candidate_sha256", "tester_ref", "reviewer_ref",
    "planner_check_ref", "manager_decision_ref", "reason",
}
_LEGACY_KEYS = {
    "evidence_refs", "criteria_ids", "candidate_sha256", "tester_ref", "reviewer_ref",
    "planner_check_ref", "manager_decision_ref", "reason",
}
_DIGEST_LENGTH = 64


def _valid_digest(value):
    return isinstance(value, str) and len(value) == _DIGEST_LENGTH and all(c in "0123456789abcdef" for c in value)


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _validate_artifact(value):
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise JournalError("candidate_artifact must be null or contain path and sha256")
    path = value["path"]
    if (not _nonempty_string(path) or "\\" in path or "\x00" in path or path.startswith("/")
            or bool(ntpath.splitdrive(path)[0])
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise JournalError("candidate artifact path must be a normalized relative path")
    if not _valid_digest(value["sha256"]):
        raise JournalError("candidate artifact sha256 must be a lowercase SHA-256 digest")


def _validate_payload(payload):
    if not isinstance(payload, dict) or not set(payload).issubset(_EVENT_KEYS):
        raise JournalError("event payload must be an allowlisted object")
    required = {"attempt_id", "attempt_revision", "parent_event_id", "actor_claim", "criteria_ref",
                "candidate_artifact", "terminal_reason", "approval_ref"}
    if not required.issubset(payload):
        raise JournalError("event payload is missing v2 event fields")
    if not _nonempty_string(payload["attempt_id"]):
        raise JournalError("attempt_id must be a non-empty string")
    revision = payload["attempt_revision"]
    if type(revision) is not int or revision < 0:
        raise JournalError("attempt_revision must be a non-negative integer")
    parent = payload["parent_event_id"]
    if parent is not None and not _nonempty_string(parent):
        raise JournalError("parent_event_id must be null or a non-empty string")
    actor = payload["actor_claim"]
    if (not isinstance(actor, dict) or set(actor) != {"role", "identity", "session_ref"}
            or any(not _nonempty_string(v) for v in actor.values())):
        raise JournalError("actor_claim must contain non-empty role, identity, and session_ref strings")
    if not _nonempty_string(payload["criteria_ref"]):
        raise JournalError("criteria_ref must be a non-empty string")
    _validate_artifact(payload["candidate_artifact"])
    for key in ("terminal_reason", "approval_ref"):
        if payload[key] is not None and not _nonempty_string(payload[key]):
            raise JournalError(f"{key} must be null or a non-empty string")
    for key in _LEGACY_KEYS:
        if key not in payload:
            continue
        value = payload[key]
        if key in {"evidence_refs", "criteria_ids"}:
            if not isinstance(value, list) or any(not _nonempty_string(item) for item in value):
                raise JournalError(f"{key} must be a list of non-empty strings")
        elif key == "candidate_sha256":
            if not _valid_digest(value):
                raise JournalError("candidate_sha256 must be a lowercase SHA-256 digest")
        elif not _nonempty_string(value):
            raise JournalError(f"{key} must be a non-empty string")


def _hash_under_root(evidence_root, descriptor):
    try:
        _validate_artifact(descriptor)
    except JournalError as exc:
        return {"status": "FAIL", "detail": str(exc)}
    if descriptor is None:
        return {"status": "BLOCKED", "detail": "candidate artifact is missing"}
    if not os.supports_dir_fd or os.open not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
        return {"status": "UNVERIFIED", "detail": "this platform cannot enforce descriptor-relative no-follow reads"}
    try:
        root = Path(evidence_root).resolve(strict=True)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
        current_fd = os.open(root, directory_flags)
        parts = descriptor["path"].split("/")
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, directory_flags, dir_fd=current_fd)
                os.close(current_fd)
                current_fd = next_fd
            file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
            file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
            try:
                before = os.fstat(file_fd)
                path_before = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
                if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (path_before.st_dev, path_before.st_ino):
                    return {"status": "BLOCKED", "detail": "candidate artifact is not a regular file"}
                digest = hashlib.sha256()
                with os.fdopen(file_fd, "rb", closefd=False) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                after = os.fstat(file_fd)
                path_after = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
                signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
                if signature(before) != signature(after) or signature(after) != signature(path_after):
                    return {"status": "BLOCKED", "detail": "candidate artifact changed during verification"}
            finally:
                os.close(file_fd)
        finally:
            os.close(current_fd)
    except (OSError, RuntimeError, ValueError) as exc:
        return {"status": "BLOCKED", "detail": f"candidate artifact could not be safely opened ({type(exc).__name__})"}
    if digest.hexdigest() != descriptor["sha256"]:
        return {"status": "FAIL", "detail": "candidate artifact digest mismatch"}
    return {"status": "PASS", "detail": "candidate artifact bytes match the declared digest"}


class Journal:
    def __init__(self, path):
        self.path = os.fspath(path)
        self._read_only = False
        if os.path.exists(self.path):
            with closing(self._connect(read_only=True)) as db:
                version = self._schema_version(db)
            if version == "1":
                raise JournalError("journal schema v1 is read-only; use Journal.open_readonly(path) to export; no migration is performed")
            if version != "2":
                raise JournalError("unsupported journal schema version")
            return
        with closing(self._connect()) as db:
            self._create_schema(db)

    @classmethod
    def open_readonly(cls, path):
        instance = cls.__new__(cls)
        instance.path = os.fspath(path)
        instance._read_only = True
        try:
            with closing(instance._connect(read_only=True)) as db:
                version = instance._schema_version(db)
        except sqlite3.DatabaseError as exc:
            raise JournalError("not a readable journal database") from exc
        if version != "1":
            raise JournalError("read-only legacy export supports schema v1 only")
        return instance

    def _connect(self, read_only=False):
        if read_only:
            uri = Path(self.path).resolve().as_uri() + "?mode=ro"
            db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
        else:
            db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _schema_version(db):
        try:
            row = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        except sqlite3.DatabaseError as exc:
            raise JournalError("journal metadata is missing or unreadable") from exc
        return row["value"] if row else None

    @staticmethod
    def _create_schema(db):
        db.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE runs (
                run_id TEXT PRIMARY KEY, plan_ref TEXT NOT NULL, plan_sha256 TEXT NOT NULL,
                state TEXT NOT NULL, revision INTEGER NOT NULL, attempt_id TEXT NOT NULL,
                attempt_revision INTEGER NOT NULL, initial_attempt_id TEXT NOT NULL
            );
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, revision INTEGER NOT NULL,
                state TEXT NOT NULL, payload TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            );
            INSERT INTO metadata VALUES ('schema_version', '2');
        """)

    def _ensure_writable(self):
        if self._read_only:
            raise JournalError("legacy journal is read-only")

    def create_run(self, run_id, plan_ref, plan_sha256):
        self._ensure_writable()
        if not _nonempty_string(run_id) or not _nonempty_string(plan_ref):
            raise JournalError("run_id and plan_ref must be non-empty strings")
        if not _valid_digest(plan_sha256):
            raise JournalError("plan_sha256 must be a lowercase SHA-256 hex digest")
        attempt_id = str(uuid.uuid4())
        try:
            with closing(self._connect()) as db:
                db.execute("INSERT INTO runs VALUES (?, ?, ?, 'PLANNED', 0, ?, 0, ?)",
                           (run_id, plan_ref, plan_sha256, attempt_id, attempt_id))
        except sqlite3.IntegrityError as exc:
            raise JournalError("run already exists") from exc
        return run_id

    def transition(self, run_id, expected_revision, new_state, payload, event_id=None):
        self._ensure_writable()
        if type(expected_revision) is not int or expected_revision < 0:
            raise JournalError("expected_revision must be a non-negative integer")
        if not isinstance(new_state, str) or (new_state not in _NEXT and new_state not in _TERMINAL):
            raise JournalError("unknown state")
        _validate_payload(payload)
        event_id = str(uuid.uuid4()) if event_id is None else event_id
        if not _nonempty_string(event_id):
            raise JournalError("event_id must be a non-empty string")
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                run = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
                if run is None:
                    raise JournalError("unknown run")
                if run["revision"] != expected_revision:
                    raise JournalError("stale revision")
                if new_state not in _NEXT.get(run["state"], set()):
                    raise JournalError("invalid state transition")
                last = db.execute("SELECT event_id, revision FROM events WHERE run_id=? ORDER BY revision DESC LIMIT 1", (run_id,)).fetchone()
                expected_parent = last["event_id"] if last else None
                if payload["parent_event_id"] != expected_parent:
                    raise JournalError("parent_event_id does not identify the prior event")
                attempt_changed = run["state"] == "REWORK_REQUIRED" and new_state == "READY"
                next_attempt_revision = run["attempt_revision"] + (1 if attempt_changed else 0)
                if payload["attempt_revision"] != next_attempt_revision:
                    raise JournalError("attempt_revision is not monotonic")
                if attempt_changed:
                    if payload["attempt_id"] == run["attempt_id"]:
                        raise JournalError("a rework attempt requires a new attempt_id")
                elif payload["attempt_id"] != run["attempt_id"]:
                    raise JournalError("attempt_id changed outside a rework transition")
                self._validate_terminal(new_state, payload)
                next_revision = expected_revision + 1
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)", (event_id, run_id, next_revision, new_state, body))
                changed = db.execute(
                    "UPDATE runs SET state=?, revision=?, attempt_id=?, attempt_revision=? WHERE run_id=? AND revision=?",
                    (new_state, next_revision, payload["attempt_id"], next_attempt_revision, run_id, expected_revision),
                ).rowcount
                if changed != 1:
                    raise JournalError("concurrent state change")
                db.commit()
                return next_revision
        except sqlite3.IntegrityError as exc:
            raise JournalError("duplicate event or invalid record") from exc
        except Exception:
            raise

    @staticmethod
    def _validate_terminal(state, payload):
        if state == "ACCEPTED":
            required = {"criteria_ids", "candidate_sha256", "tester_ref", "reviewer_ref",
                        "planner_check_ref", "manager_decision_ref", "evidence_refs"}
            if (not required.issubset(payload) or any(not payload[key] for key in required)
                    or payload["candidate_artifact"] is None or payload["approval_ref"] is None):
                raise JournalError("acceptance requires role, criteria, candidate, approval, and evidence references")
            if payload["candidate_sha256"] != payload["candidate_artifact"]["sha256"]:
                raise JournalError("candidate digest fields must agree")
        elif state in {"BLOCKED", "CANCELLED", "REJECTED"} and payload["terminal_reason"] is None:
            raise JournalError("terminal non-acceptance states require terminal_reason")

    def get_run(self, run_id):
        with closing(self._connect(read_only=True)) as db:
            row = db.execute("SELECT run_id, plan_ref, plan_sha256, state, revision, attempt_id, attempt_revision, initial_attempt_id FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def _load(self, run_id):
        with closing(self._connect(read_only=True)) as db:
            run = db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                raise JournalError("unknown run")
            events = db.execute("SELECT event_id, revision, state, payload FROM events WHERE run_id=? ORDER BY revision", (run_id,)).fetchall()
        parsed = []
        for event in events:
            try:
                payload = json.loads(event["payload"])
            except (TypeError, json.JSONDecodeError) as exc:
                raise JournalError("event payload is corrupt JSON") from exc
            parsed.append({"event_id": event["event_id"], "revision": event["revision"],
                           "state": event["state"], "payload": payload})
        return dict(run), parsed

    @staticmethod
    def _check_chain(run, events):
        event_ids = [event["event_id"] for event in events]
        if len(event_ids) != len(set(event_ids)):
            return False, "DUPLICATE_EVENT"
        expected_state = "PLANNED"
        attempt_id = run["initial_attempt_id"]
        attempt_revision = 0
        previous_event_id = None
        for revision, event in enumerate(events, start=1):
            payload = event["payload"]
            if not _nonempty_string(event["event_id"]):
                return False, "INVALID_EVENT"
            if (event["revision"] != revision or (event["state"] not in _NEXT and event["state"] not in _TERMINAL)
                    or event["state"] not in _NEXT.get(expected_state, set())):
                return False, "REVISION_GAP"
            try:
                _validate_payload(payload)
            except JournalError:
                return False, "INVALID_EVENT"
            if payload["parent_event_id"] != previous_event_id:
                return False, "EVENT_CHAIN_MISMATCH"
            rework = expected_state == "REWORK_REQUIRED" and event["state"] == "READY"
            if rework:
                if payload["attempt_id"] == attempt_id or payload["attempt_revision"] != attempt_revision + 1:
                    return False, "ATTEMPT_CHAIN_MISMATCH"
                attempt_id, attempt_revision = payload["attempt_id"], attempt_revision + 1
            elif payload["attempt_id"] != attempt_id or payload["attempt_revision"] != attempt_revision:
                return False, "ATTEMPT_CHAIN_MISMATCH"
            try:
                Journal._validate_terminal(event["state"], payload)
            except JournalError:
                return False, "INVALID_TERMINAL_EVENT"
            expected_state, previous_event_id = event["state"], event["event_id"]
        if (run["revision"] != len(events) or run["state"] != expected_state
                or run["attempt_id"] != attempt_id or run["attempt_revision"] != attempt_revision):
            return False, "REVISION_GAP"
        return True, None

    def export(self, run_id):
        if self._read_only:
            with closing(self._connect(read_only=True)) as db:
                run = db.execute("SELECT run_id, plan_ref, plan_sha256, state, revision FROM runs WHERE run_id=?", (run_id,)).fetchone()
                if run is None:
                    raise JournalError("unknown run")
                rows = db.execute("SELECT event_id, revision, state, payload FROM events WHERE run_id=? ORDER BY revision", (run_id,)).fetchall()
            try:
                events = [{"event_id": row["event_id"], "revision": row["revision"], "state": row["state"],
                           "payload": json.loads(row["payload"])} for row in rows]
            except (TypeError, json.JSONDecodeError) as exc:
                raise JournalError("legacy event payload is corrupt JSON") from exc
            return json.dumps({"schema_version": 1, "run": dict(run), "events": events},
                              ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        run, events = self._load(run_id)
        return json.dumps({"schema_version": 2, "run": run, "events": events},
                          ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    def verify_run(self, run_id, evidence_root):
        checks = []
        try:
            run, events = self._load(run_id)
        except (JournalError, sqlite3.DatabaseError) as exc:
            return {"integrity_status": "FAIL", "checks": [{"name": "journal_read", "status": "FAIL", "detail": str(exc)}]}
        chain_ok, chain_code = self._check_chain(run, events)
        checks.append({"name": "event_chain", "status": "PASS" if chain_ok else "FAIL",
                       "detail": "event revisions, states, parents, and attempts are consistent" if chain_ok else chain_code})
        descriptors = [event["payload"].get("candidate_artifact") for event in events
                       if isinstance(event["payload"], dict) and event["payload"].get("candidate_artifact") is not None]
        if not descriptors:
            artifact_results = [{"status": "BLOCKED", "detail": "candidate artifact is missing"}]
        else:
            artifact_results = [_hash_under_root(evidence_root, item) for item in descriptors]
        for index, result in enumerate(artifact_results):
            checks.append({"name": "candidate_artifact" if index == 0 else f"candidate_artifact_{index + 1}", **result})
        if any(event["payload"].get("actor_claim") for event in events if isinstance(event["payload"], dict)):
            checks.append({"name": "actor_claim", "status": "UNVERIFIED", "detail": "actor/session claim has no native attestation"})
        if any(event["payload"].get("approval_ref") for event in events if isinstance(event["payload"], dict)):
            checks.append({"name": "approval_claim", "status": "UNVERIFIED", "detail": "approval reference is a claim, not authenticated approval"})
        statuses = [check["status"] for check in checks]
        artifact_statuses = [check["status"] for check in checks if check["name"].startswith("candidate_artifact")]
        if "FAIL" in statuses:
            status = "FAIL"
        elif "BLOCKED" in statuses:
            status = "BLOCKED"
        elif "UNVERIFIED" in artifact_statuses:
            status = "UNVERIFIED"
        else:
            status = "PASS"
        return {"integrity_status": status, "checks": checks}

    def reconcile(self, run_id, evidence_root):
        run = self.get_run(run_id)
        if run is None:
            raise JournalError("unknown run")
        verification = self.verify_run(run_id, evidence_root)
        reason_codes = []
        status_by_name = {check["name"]: check["status"] for check in verification["checks"]}
        if status_by_name.get("event_chain") == "FAIL":
            detail = next(check["detail"] for check in verification["checks"] if check["name"] == "event_chain")
            reason_codes.append(detail if detail in {"REVISION_GAP", "DUPLICATE_EVENT"} else "EVENT_CHAIN_MISMATCH")
        if any(name.startswith("candidate_artifact") and status == "FAIL" for name, status in status_by_name.items()):
            reason_codes.append("DIGEST_MISMATCH")
        if any(name.startswith("candidate_artifact") and status == "BLOCKED" for name, status in status_by_name.items()):
            reason_codes.append("MISSING_CANDIDATE")
        if "actor_claim" in status_by_name:
            reason_codes.append("UNVERIFIED_ACTOR")
        if "approval_claim" in status_by_name:
            reason_codes.append("UNVERIFIED_APPROVAL")
        terminal = run["state"] in _TERMINAL
        if verification["integrity_status"] == "UNVERIFIED":
            recovery = "UNVERIFIED"
        elif verification["integrity_status"] == "BLOCKED":
            recovery = "BLOCKED"
        elif verification["integrity_status"] == "FAIL" or not terminal:
            recovery = "RECOVERY_REQUIRED"
        else:
            recovery = "COMPLETE_RECORD"
        return {"run_id": run_id, "recovery_status": recovery,
                "last_verified_revision": run["revision"] if status_by_name.get("event_chain") == "PASS" else None,
                "reason_codes": list(dict.fromkeys(reason_codes))}
