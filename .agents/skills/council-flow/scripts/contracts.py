"""CouncilFlow 1.0 controlled-file validation, not a transport or security sandbox."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
from datetime import datetime

MAX_BYTES = 65536
MAX_DEPTH = 16
MAX_ITEMS = 128
MAX_STRING = 8192
ROLES = {"planner", "manager", "worker", "tester", "reviewer", "owner"}
FIELDS = {"protocol", "version", "message_id", "message_type", "plan_id", "plan_revision",
          "task_id", "attempt_id", "sender", "recipient", "in_reply_to",
          "payload", "evidence_refs"}
ROUTES = {
    "plan.publish": ("planner", {"manager"}),
    "plan.check": ("planner", {"manager"}),
    "plan.progress": ("manager", {"planner"}),
    "job.assign": ("manager", {"worker", "tester", "reviewer"}),
    "job.report": ({"worker", "tester", "reviewer"}, {"manager"}),
    "task.decision": ("manager", {"planner"}),
    "approval.request": ("manager", {"owner"}),
    "approval.decision": ("owner", {"manager"}),
}
EVENT_TYPES = {"plan_published", "worker_dispatched", "worker_reported", "test_failed",
               "review_completed", "rework_requested", "acceptance_blocked", "task_completed"}


class ContractError(ValueError):
    def __init__(self, code, field, detail):
        self.code, self.field, self.detail = code, field, detail
        super().__init__(f"{code} at {field}: {detail}")


def fail(code, field, detail):
    raise ContractError(code, field, detail)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("duplicate_key", "$", key)
        result[key] = value
    return result


def _constant(value):
    fail("nonfinite", "$", value)


def _tree(value, depth=0):
    if isinstance(value, (dict, list)):
        if depth >= MAX_DEPTH:
            fail("depth", "$", f"maximum {MAX_DEPTH} containers")
        if len(value) > MAX_ITEMS:
            fail("items", "$", f"maximum {MAX_ITEMS} entries")
        if isinstance(value, dict) and any(type(k) is not str for k in value):
            fail("type", "$", "JSON object keys must be strings")
        values = list(value.keys()) + list(value.values()) if isinstance(value, dict) else value
        for child in values:
            _tree(child, depth + 1)
    elif isinstance(value, str):
        try:
            value.encode("utf-8", "strict")
        except UnicodeError:
            fail("utf8", "$", "unencodable Unicode surrogate")
        if len(value) > MAX_STRING:
            fail("string_size", "$", f"maximum {MAX_STRING} characters")
    elif isinstance(value, float) and not math.isfinite(value):
        fail("nonfinite", "$", "numeric overflow or nonfinite number")


def loads(source):
    """Strict bounded UTF-8 JSON; duplicate keys and nonfinite values are errors."""
    try:
        raw = source.encode("utf-8", "strict") if isinstance(source, str) else bytes(source)
        if len(raw) > MAX_BYTES:
            fail("size", "$", f"maximum {MAX_BYTES} UTF-8 bytes")
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs,
                           parse_constant=_constant)
        _tree(value)
        return value
    except ContractError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError) as exc:
        fail("json", "$", str(exc)[:240])


def read_json(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return loads(raw)


def _authoritative_criteria(reference, root):
    """Load criteria from an explicitly trusted caller reference.

    The artifact digest detects stale bytes; it does not authenticate who approved
    them. The caller must obtain this reference from the Owner-approved source.
    """
    if root is None:
        fail("criteria_source", "authoritative_criteria_ref", "a repository root is required")
    artifact(reference, root, "authoritative_criteria_ref")
    if reference["kind"] != "owner-approved-criteria":
        fail("criteria_source", "authoritative_criteria_ref.kind", "expected owner-approved-criteria artifact")
    source = read_json(Path(root) / reference["path"])
    if type(source) is not dict or set(source) != {"criteria"}:
        fail("criteria_source", "authoritative_criteria_ref", "expected exact criteria fixture object")
    criteria = source["criteria"]
    if type(criteria) is not list or not criteria or len(criteria) > MAX_ITEMS:
        fail("criteria_source", "authoritative_criteria_ref.criteria", "expected bounded nonempty ordered criteria")
    result = []
    seen = set()
    for entry in criteria:
        if type(entry) is not dict or set(entry) != {"id", "criterion"}:
            fail("criteria_source", "authoritative_criteria_ref.criteria", "each entry requires only id and criterion")
        identity = _identity(entry["id"], "authoritative_criteria_ref.criteria.id")
        criterion = _criterion(entry["criterion"], "authoritative_criteria_ref.criteria.criterion")
        if identity in seen:
            fail("criteria_source", "authoritative_criteria_ref.criteria", "criterion identities must be unique")
        seen.add(identity)
        result.append((identity, criterion))
    return result


def _compare_authoritative_criteria(plan, expected):
    acceptance = plan.get("acceptance")
    if type(acceptance) is not list or len(acceptance) != len(expected):
        fail("acceptance_fidelity", "plan.acceptance", "criteria count differs from authoritative source")
    actual = []
    for entry in acceptance:
        if type(entry) is not dict:
            fail("acceptance_fidelity", "plan.acceptance", "criterion entry must be an object")
        identity = _identity(entry.get("id"), "plan.acceptance.id")
        criterion = _criterion(entry.get("criterion"), "plan.acceptance.criterion")
        actual.append((identity, criterion))
    if actual != expected:
        fail("acceptance_fidelity", "plan.acceptance", "ordered criteria differ byte-for-byte from authoritative source")


def _object(value, required, optional=(), field="$"):
    if type(value) is not dict:
        fail("type", field, "expected object")
    if set(value) - set(required) - set(optional):
        fail("unknown_field", field, ",".join(sorted(set(value) - set(required) - set(optional))))
    if set(required) - set(value):
        fail("required", field, ",".join(sorted(set(required) - set(value))))


def _string(value, field, limit=MAX_STRING):
    if type(value) is not str or not value.strip() or len(value) > limit:
        fail("string", field, f"expected nonempty string, at most {limit} characters")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        fail("control", field, "control characters are not allowed")
    return value


def _criterion(value, field):
    """Validate plan text while preserving ordinary LF or CRLF line breaks."""
    if type(value) is not str or not value.strip() or len(value) > MAX_STRING:
        fail("string", field, f"expected nonempty string, at most {MAX_STRING} characters")
    if any((ord(char) < 32 and char not in "\r\n") or ord(char) == 127
           for char in value):
        fail("control", field, "control characters other than line breaks are not allowed")
    if "\r" in value.replace("\r\n", ""):
        fail("control", field, "carriage returns must be part of CRLF line breaks")
    return value


def _identity(value, field):
    return _string(value, field, 128)


def _strings(value, field, nonempty=False, unique=False):
    if type(value) is not list or len(value) > MAX_ITEMS or (nonempty and not value):
        fail("array", field, "expected bounded string array")
    for child in value:
        _string(child, field)
    if unique and len(set(value)) != len(value):
        fail("duplicate_item", field, "entries must be unique")
    return value


def _ids(value, field):
    _strings(value, field, True, True)
    for child in value:
        _identity(child, field)


def _enum(value, choices, field):
    if type(value) is not str or value not in choices:
        fail("enum", field, "unsupported value")


def _timestamp(value, field="created_at"):
    if type(value) is not str or not re.fullmatch(
            r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z", value):
        fail("timestamp", field, "expected UTC RFC3339 timestamp ending Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail("timestamp", field, "invalid calendar date/time")


def artifact(value, root=None, field="evidence_ref"):
    _tree(value)
    _object(value, {"artifact_id", "path", "sha256", "kind"}, field=field)
    _identity(value["artifact_id"], field + ".artifact_id")
    _string(value["kind"], field + ".kind", 64)
    path = _string(value["path"], field + ".path", 1024)
    pure = PurePosixPath(path)
    if pure.is_absolute() or PureWindowsPath(path).drive or "\\" in path or ".." in pure.parts or path in {".", ""}:
        fail("artifact_path", field, "expected repository-relative POSIX path")
    if type(value["sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"]):
        fail("hash", field + ".sha256", "expected lowercase SHA-256")
    if root is not None:
        base = Path(root).resolve()
        target = (base / path).resolve()
        if not target.is_relative_to(base):
            fail("artifact_path", field, "resolved path leaves authorized root")
        if not target.is_file():
            fail("artifact_missing", field, path)
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
        if digest.hexdigest() != value["sha256"]:
            fail("artifact_hash", field, path)
    return value


def _refs(value, root=None, field="evidence_refs"):
    if type(value) is not list or len(value) > MAX_ITEMS:
        fail("array", field, "expected bounded evidence array")
    seen = set()
    for item in value:
        artifact(item, root, field)
        if item["artifact_id"] in seen:
            fail("duplicate_artifact", field, item["artifact_id"])
        seen.add(item["artifact_id"])


def _actor(value, field):
    _object(value, {"role", "instance_id"}, field=field)
    _enum(value["role"], ROLES, field + ".role")
    _identity(value["instance_id"], field + ".instance_id")


def validate_message(message, *, root=None, expected_sender=None):
    # Re-serialization also bounds already-decoded Python callers and rejects surrogates.
    try:
        encoded = json.dumps(message, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, UnicodeError, TypeError, RecursionError):
        fail("json", "$", "not finite UTF-8 JSON")
    if len(encoded) > MAX_BYTES:
        fail("size", "$", f"maximum {MAX_BYTES} bytes")
    _tree(message)
    _object(message, FIELDS)
    if message["protocol"] != "council-flow" or type(message["protocol"]) is not str:
        fail("protocol", "protocol", "unsupported protocol")
    if message["version"] != "1.0" or type(message["version"]) is not str:
        fail("version", "version", "supported version is string 1.0")
    for field in ("message_id", "plan_id", "task_id", "attempt_id"):
        _identity(message[field], field)
    if type(message["plan_revision"]) is not int or not 1 <= message["plan_revision"] <= 2147483647:
        fail("integer", "plan_revision", "expected positive integer, never bool")
    if message["in_reply_to"] is not None:
        _identity(message["in_reply_to"], "in_reply_to")
        if message["in_reply_to"] == message["message_id"]:
            fail("reference", "in_reply_to", "cannot reference itself")
    _actor(message["sender"], "sender")
    _actor(message["recipient"], "recipient")
    if expected_sender is not None and message["sender"] != expected_sender:
        fail("origin_binding", "sender", "does not match externally observed sender")
    kind = message["message_type"]
    if type(kind) is not str or kind not in ROUTES:
        fail("message_type", "message_type", "unsupported type")
    senders, recipients = ROUTES[kind]
    if isinstance(senders, str):
        senders = {senders}
    if message["sender"]["role"] not in senders or message["recipient"]["role"] not in recipients:
        fail("route", "sender/recipient", "role cannot send this message type to recipient")
    _refs(message["evidence_refs"], root)
    p = message["payload"]
    if kind == "plan.publish":
        _object(p, {"objective", "scope", "acceptance_ids", "plan_ref"}, field="payload")
        _string(p["objective"], "payload.objective")
        _strings(p["scope"], "payload.scope", True)
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        artifact(p["plan_ref"], root, "payload.plan_ref")
    elif kind == "job.assign":
        _object(p, {"objective", "scope", "acceptance_ids", "instructions"},
                {"candidate_ref", "oracle_ref"}, "payload")
        _string(p["objective"], "payload.objective")
        _strings(p["scope"], "payload.scope", True)
        _strings(p["instructions"], "payload.instructions", True)
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        if message["recipient"]["role"] != "worker" and "candidate_ref" not in p:
            fail("required", "payload.candidate_ref", "verification requires exact assigned candidate")
        if "candidate_ref" in p:
            artifact(p["candidate_ref"], root, "payload.candidate_ref")
        if message["recipient"]["role"] == "tester" and "oracle_ref" not in p:
            fail("required", "payload.oracle_ref", "Tester requires Manager-assigned strategy/oracle")
        if "oracle_ref" in p:
            artifact(p["oracle_ref"], root, "payload.oracle_ref")
    elif kind == "job.report":
        _object(p, {"status", "summary", "acceptance_ids", "candidate_ref", "findings", "errors"},
                {"changed_files", "checks", "input_candidate_ref", "oracle_ref",
                 "deterministic_commands", "comparison"}, "payload")
        _enum(p["status"], {"passed", "failed", "blocked", "in_progress"}, "payload.status")
        _string(p["summary"], "payload.summary")
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        artifact(p["candidate_ref"], root, "payload.candidate_ref")
        _strings(p["findings"], "payload.findings")
        if type(p["errors"]) is not list or len(p["errors"]) > MAX_ITEMS:
            fail("array", "payload.errors", "expected bounded error array")
        for error in p["errors"]:
            _object(error, {"code", "field", "message"}, field="payload.errors")
            for field in error:
                _string(error[field], "payload.errors." + field)
        role = message["sender"]["role"]
        if "input_candidate_ref" in p:
            if role != "worker":
                fail("role_payload", "payload.input_candidate_ref", "only Worker reports input/output changes")
            artifact(p["input_candidate_ref"], root, "payload.input_candidate_ref")
        if role == "worker":
            if "changed_files" not in p:
                fail("required", "payload.changed_files", "Worker must report changed files")
        if "changed_files" in p:
            _strings(p["changed_files"], "payload.changed_files")
        if role == "tester":
            if "deterministic_commands" not in p:
                fail("required", "payload.deterministic_commands", "Tester must declare deterministic commands or an empty list")
            if not p.get("checks"):
                fail("required", "payload.checks", "Tester must supply technical checks")
            if "oracle_ref" not in p:
                fail("required", "payload.oracle_ref", "Tester must echo Manager-assigned strategy")
            artifact(p["oracle_ref"], root, "payload.oracle_ref")
            commands = p.get("deterministic_commands", [])
            if type(commands) is not list or len(commands) > MAX_ITEMS:
                fail("array", "payload.deterministic_commands", "expected bounded command records")
            for i, command in enumerate(commands):
                field = f"payload.deterministic_commands[{i}]"
                _object(command, {"command_id", "command", "arguments", "workdir", "candidate_ref",
                                  "input_refs", "exit_code", "stdout_sha256", "acceptance_id", "evidence_ref"}, field=field)
                _identity(command["command_id"], field + ".command_id")
                _string(command["command"], field + ".command")
                _strings(command["arguments"], field + ".arguments")
                _string(command["workdir"], field + ".workdir", 1024)
                artifact(command["candidate_ref"], root, field + ".candidate_ref")
                _refs(command["input_refs"], root, field + ".input_refs")
                if type(command["exit_code"]) is not int:
                    fail("integer", field + ".exit_code", "expected actual integer exit code")
                if type(command["stdout_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", command["stdout_sha256"]):
                    fail("hash", field + ".stdout_sha256", "expected SHA-256 of CRLF-to-LF normalized stdout")
                _identity(command["acceptance_id"], field + ".acceptance_id")
                artifact(command["evidence_ref"], root, field + ".evidence_ref")
                if command["candidate_ref"] != p["candidate_ref"] or command["acceptance_id"] not in p["acceptance_ids"]:
                    fail("command_binding", field, "command must bind to this report candidate and original criterion")
            if len({x["command_id"] for x in commands}) != len(commands):
                fail("command_identity", "payload.deterministic_commands", "command IDs must be unique")
        elif "deterministic_commands" in p:
            fail("role_payload", "payload.deterministic_commands", "only Tester declares deterministic commands")
        elif "oracle_ref" in p:
            fail("role_payload", "payload.oracle_ref", "only Tester echoes assigned verification strategy")
        if "checks" in p:
            if type(p["checks"]) is not list or len(p["checks"]) > MAX_ITEMS:
                fail("array", "payload.checks", "expected bounded check array")
            for check in p["checks"]:
                _object(check, {"name", "status", "evidence_ref"}, field="payload.checks")
                _string(check["name"], "payload.checks.name")
                _enum(check["status"], {"passed", "failed", "blocked", "unverified"}, "payload.checks.status")
                artifact(check["evidence_ref"], root, "payload.checks.evidence_ref")
            if role == "tester" and p["status"] == "passed" and any(x["status"] != "passed" for x in p["checks"]):
                fail("contradictory_report", "payload.status", "passed technical report cannot contain unmet mandatory checks")
        if role == "reviewer" and "comparison" not in p:
            fail("required", "payload.comparison", "Reviewer must compare plan, candidate and Tester evidence and rerun a declared command")
        if "comparison" in p:
            if role != "reviewer":
                fail("role_payload", "payload.comparison", "only Reviewer submits comparator findings")
            comparison = p["comparison"]
            _object(comparison, {"plan_ref", "tester_report_ref", "candidate_ref", "findings", "discrepancies", "independent_rerun"}, field="payload.comparison")
            for key in ("plan_ref", "tester_report_ref", "candidate_ref"):
                artifact(comparison[key], root, "payload.comparison." + key)
            if comparison["candidate_ref"] != p["candidate_ref"]:
                fail("candidate", "payload.comparison.candidate_ref", "must identify the compared candidate")
            _strings(comparison["findings"], "payload.comparison.findings")
            _strings(comparison["discrepancies"], "payload.comparison.discrepancies")
            rerun = comparison["independent_rerun"]
            _object(rerun, {"status"}, {"command_id", "command", "arguments", "workdir", "candidate_ref", "input_refs", "exit_code", "stdout_sha256", "acceptance_id", "evidence_ref", "tester_evidence_ref", "tester_exit_code", "tester_stdout_sha256"}, "payload.comparison.independent_rerun")
            _enum(rerun["status"], {"MATCH", "MISMATCH", "NOT_COMPARABLE"}, "payload.comparison.independent_rerun.status")
            if rerun["status"] == "NOT_COMPARABLE":
                _object(rerun, {"status"}, field="payload.comparison.independent_rerun")
                if p["status"] == "passed":
                    fail("comparison", "payload.comparison.independent_rerun", "NOT_COMPARABLE cannot satisfy mandatory review")
            else:
                required = {"command_id", "command", "arguments", "workdir", "candidate_ref", "input_refs", "exit_code", "stdout_sha256", "acceptance_id", "evidence_ref", "tester_evidence_ref", "tester_exit_code", "tester_stdout_sha256"}
                _object(rerun, required, {"status"}, "payload.comparison.independent_rerun")
                for key in ("command_id", "command", "workdir", "acceptance_id"):
                    _string(rerun[key], "payload.comparison.independent_rerun." + key)
                _strings(rerun["arguments"], "payload.comparison.independent_rerun.arguments")
                _refs(rerun["input_refs"], root, "payload.comparison.independent_rerun.input_refs")
                artifact(rerun["candidate_ref"], root, "payload.comparison.independent_rerun.candidate_ref")
                artifact(rerun["evidence_ref"], root, "payload.comparison.independent_rerun.evidence_ref")
                artifact(rerun["tester_evidence_ref"], root, "payload.comparison.independent_rerun.tester_evidence_ref")
                for key in ("exit_code", "tester_exit_code"):
                    if type(rerun[key]) is not int: fail("integer", "payload.comparison.independent_rerun." + key, "expected integer exit code")
                for key in ("stdout_sha256", "tester_stdout_sha256"):
                    if type(rerun[key]) is not str or not re.fullmatch(r"[0-9a-f]{64}", rerun[key]): fail("hash", "payload.comparison.independent_rerun." + key, "expected normalized stdout SHA-256")
                equal = rerun["exit_code"] == rerun["tester_exit_code"] and rerun["stdout_sha256"] == rerun["tester_stdout_sha256"]
                if (rerun["status"] == "MATCH") != equal:
                    fail("comparison", "payload.comparison.independent_rerun.status", "recorded result must equal the exit-code and stdout-hash comparison")
                if rerun["candidate_ref"] != comparison["candidate_ref"]:
                    fail("candidate", "payload.comparison.independent_rerun.candidate_ref", "rerun candidate identity changed")
                if rerun["status"] == "MISMATCH" and p["status"] == "passed":
                    fail("comparison", "payload.status", "mismatching independent rerun cannot pass")
            if comparison["discrepancies"] and p["status"] == "passed":
                fail("comparison", "payload.status", "a comparison with unresolved discrepancies cannot pass")
        if p["status"] != "in_progress" and not message["evidence_refs"]:
            fail("evidence", "evidence_refs", "completed report requires evidence references")
    elif kind == "task.decision":
        _object(p, {"disposition", "reason", "acceptance_ids", "candidate_ref", "report_ids"},
                {"failed_acceptance_ids"}, "payload")
        _enum(p["disposition"], {"accept", "rework", "reject", "escalate"}, "payload.disposition")
        _string(p["reason"], "payload.reason")
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        artifact(p["candidate_ref"], root, "payload.candidate_ref")
        _strings(p["report_ids"], "payload.report_ids", True, True)
        if p["disposition"] == "rework":
            _ids(p.get("failed_acceptance_ids"), "payload.failed_acceptance_ids")
        elif "failed_acceptance_ids" in p:
            _strings(p["failed_acceptance_ids"], "payload.failed_acceptance_ids", unique=True)
            for identity in p["failed_acceptance_ids"]:
                _identity(identity, "payload.failed_acceptance_ids")
        if not set(p.get("failed_acceptance_ids", [])) <= set(p["acceptance_ids"]):
            fail("acceptance", "payload.failed_acceptance_ids", "failed criteria must be assigned criteria")
        if p["disposition"] == "accept" and p.get("failed_acceptance_ids"):
            fail("contradictory_acceptance", "payload.failed_acceptance_ids", "accept cannot declare current failed criteria")
    elif kind == "plan.progress":
        _object(p, {"status", "objective", "scope", "acceptance_ids", "verified_progress", "next_action"},
                {"candidate_ref"}, "payload")
        for field in ("status", "objective", "next_action"):
            _string(p[field], "payload." + field)
        _strings(p["scope"], "payload.scope", True)
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        _strings(p["verified_progress"], "payload.verified_progress")
        if "candidate_ref" in p:
            artifact(p["candidate_ref"], root, "payload.candidate_ref")
    elif kind == "plan.check":
        _object(p, {"status", "summary", "acceptance_ids", "plan_ref", "results"}, field="payload")
        _enum(p["status"], {"passed", "failed", "blocked"}, "payload.status")
        _string(p["summary"], "payload.summary")
        _ids(p["acceptance_ids"], "payload.acceptance_ids")
        artifact(p["plan_ref"], root, "payload.plan_ref")
        if type(p["results"]) is not list or not p["results"] or len(p["results"]) > MAX_ITEMS:
            fail("array", "payload.results", "expected bounded acceptance results")
        ids = []
        for result in p["results"]:
            _object(result, {"acceptance_id", "status", "evidence_refs"}, field="payload.results")
            _identity(result["acceptance_id"], "payload.results.acceptance_id")
            _enum(result["status"], {"passed", "failed", "blocked", "unverified"}, "payload.results.status")
            _refs(result["evidence_refs"], root, "payload.results.evidence_refs")
            if result["status"] == "passed" and not result["evidence_refs"]:
                fail("evidence", "payload.results.evidence_refs", "passed criterion requires explicit evidence references")
            ids.append(result["acceptance_id"])
        if len(set(ids)) != len(ids) or set(ids) != set(p["acceptance_ids"]):
            fail("acceptance", "payload.results", "must map each listed acceptance exactly once")
        if p["status"] == "passed" and any(r["status"] != "passed" for r in p["results"]):
            fail("acceptance", "payload.status", "cannot pass with unmet acceptance")
    elif kind == "approval.request":
        _object(p, {"question", "reason", "options", "operation_ref"}, field="payload")
        _string(p["question"], "payload.question")
        _string(p["reason"], "payload.reason")
        _strings(p["options"], "payload.options", True, True)
        artifact(p["operation_ref"], root, "payload.operation_ref")
    elif kind == "approval.decision":
        _object(p, {"decision", "approval_request_id", "provenance_ref"}, field="payload")
        _enum(p["decision"], {"approved", "rejected"}, "payload.decision")
        _identity(p["approval_request_id"], "payload.approval_request_id")
        artifact(p["provenance_ref"], root, "payload.provenance_ref")
    return message


def validate_sequence(messages, *, root=None, expected_senders=None, owner_provenance=(),
                      authoritative_criteria_ref=None, require_criteria_fidelity=False):
    """Validate supplied ordered context, never authenticate opaque native transport."""
    if not isinstance(messages, (list, tuple)) or len(messages) > 1024:
        fail("context", "$", "supply at most 1024 ordered messages")
    seen, actors, plans, artifact_ids = {}, {}, {}, {}
    # Supplied context is data too: a falsey wrong type must not disable checks.
    if expected_senders is None:
        expected_senders = {}
    if type(expected_senders) is not dict or len(expected_senders) > 1024:
        fail("context_bindings", "expected_senders", "expected at most 1024 message-to-actor bindings")
    for message_id, actor in expected_senders.items():
        _tree(message_id)
        _identity(message_id, "expected_senders.message_id")
        _tree(actor)
        _actor(actor, "expected_senders." + message_id)
    if type(owner_provenance) not in {list, tuple, set, frozenset} or len(owner_provenance) > 1024:
        fail("context_owner", "owner_provenance", "expected a bounded collection of Owner artifact identities")
    for identity in owner_provenance:
        _tree(identity)
        _identity(identity, "owner_provenance")
    owner_provenance = set(owner_provenance)
    if type(require_criteria_fidelity) is not bool:
        fail("criteria_source", "require_criteria_fidelity", "expected boolean")
    if require_criteria_fidelity and authoritative_criteria_ref is None:
        fail("criteria_source", "authoritative_criteria_ref", "authoritative criteria source is required; failing closed")
    expected_criteria = None
    if authoritative_criteria_ref is not None:
        expected_criteria = _authoritative_criteria(authoritative_criteria_ref, root)
    for m in messages:
        # Validate the object and identity before using either as a lookup key.
        validate_message(m, root=root)
        expected_sender = expected_senders.get(m["message_id"])
        if expected_sender is not None and m["sender"] != expected_sender:
            fail("origin_binding", "sender", "does not match externally observed sender")
        mid, kind, p = m["message_id"], m["message_type"], m["payload"]
        if mid in seen:
            fail("message_identity", "message_id", "duplicate message identity")
        for who in ("sender", "recipient"):
            actor = m[who]
            old = actors.get(actor["instance_id"])
            if old is not None and old != actor["role"]:
                fail("origin_binding", who, "known instance cannot change role")
            actors[actor["instance_id"]] = actor["role"]
        reply = m["in_reply_to"]
        predecessor = seen.get(reply) if reply is not None else None
        if reply is not None and predecessor is None:
            fail("causal_reference", "in_reply_to", "predecessor is not in supplied earlier context")
        if predecessor:
            for field in ("plan_id", "plan_revision", "task_id"):
                if m[field] != predecessor[field]:
                    fail("causal_identity", field, "must match predecessor")
        key = (m["plan_id"], m["plan_revision"])
        if kind == "plan.publish":
            if key in plans:
                original = plans[key]
                if p != original["payload"] or any(m[actor] != original[actor] for actor in ("sender", "recipient")):
                    fail("plan_immutable", "payload", "published objective, scope, acceptance, plan or actors changed")
            if any(plan == m["plan_id"] and revision != m["plan_revision"] for plan, revision in plans):
                fail("plan_revision", "plan_revision", "amendments need separately approved context; not inferred")
            plans.setdefault(key, m)
            if root is not None:
                plan = read_json(Path(root) / p["plan_ref"]["path"])
                # Plan metadata is project-owned, not a second wire schema. Its
                # context identities and criteria still need strict type guards.
                if type(plan) is not dict:
                    fail("plan_artifact", "payload.plan_ref", "plan context must be an object")
                _identity(plan.get("plan_id"), "plan.plan_id")
                revision = plan.get("plan_revision")
                if type(revision) is not int or not 1 <= revision <= 2147483647:
                    fail("plan_artifact", "plan.plan_revision", "expected positive integer, never bool")
                if plan["plan_id"] != m["plan_id"] or revision != m["plan_revision"]:
                    fail("plan_artifact", "payload.plan_ref", "plan identity differs")
                acceptance = plan.get("acceptance")
                if type(acceptance) is not list or not acceptance or len(acceptance) > MAX_ITEMS:
                    fail("plan_artifact", "plan.acceptance", "expected bounded nonempty criterion array")
                ids = []
                for entry in acceptance:
                    if type(entry) is not dict:
                        fail("plan_artifact", "plan.acceptance", "criterion entry must be an object")
                    _identity(entry.get("id"), "plan.acceptance.id")
                    if "criterion" in entry:
                        _criterion(entry["criterion"], "plan.acceptance.criterion")
                    ids.append(entry["id"])
                if len(set(ids)) != len(ids):
                    fail("plan_artifact", "plan.acceptance", "criterion identities must be unique")
                if ids != p["acceptance_ids"]:
                    fail("plan_artifact", "payload.acceptance_ids", "does not match original artifact")
                if expected_criteria is not None:
                    _compare_authoritative_criteria(plan, expected_criteria)
        elif kind != "plan.progress" and key not in plans:
            fail("plan_context", "plan_id", "published plan required")
        if key in plans and "acceptance_ids" in p:
            published = set(plans[key]["payload"]["acceptance_ids"])
            if not set(p["acceptance_ids"]) <= published:
                fail("acceptance", "payload.acceptance_ids", "unknown original acceptance")
            if kind in {"plan.check", "task.decision"} and (kind == "plan.check" or p["disposition"] == "accept"):
                if set(p["acceptance_ids"]) != published:
                    fail("acceptance", "payload.acceptance_ids", "cannot silently omit mandatory criteria")
        if ((kind == "task.decision" and p["disposition"] == "accept")
                or (kind == "plan.check" and p["status"] == "passed")):
            if any(check["message_type"] == "plan.check" and check["payload"]["status"] != "passed"
                   and all(check[field] == m[field] for field in ("plan_id", "plan_revision", "task_id", "attempt_id"))
                   for check in seen.values()):
                fail("failed_planner_check", "attempt_id", "an unmet original Planner check requires preserved rework and a fresh attempt")
        if kind == "job.report":
            if not predecessor or predecessor["message_type"] != "job.assign":
                fail("assignment", "in_reply_to", "report must reply to actual assignment")
            if m["sender"] != predecessor["recipient"] or m["recipient"] != predecessor["sender"]:
                fail("assignment", "sender", "report actors differ from assignment")
            if m["attempt_id"] != predecessor["attempt_id"]:
                fail("attempt", "attempt_id", "report attempt differs from assignment")
            assigned_input = predecessor["payload"].get("candidate_ref")
            if m["sender"]["role"] == "worker":
                if p.get("input_candidate_ref") != assigned_input:
                    fail("candidate_input", "payload.input_candidate_ref", "Worker must echo assigned input separately from output")
            elif p["candidate_ref"] != assigned_input:
                fail("candidate", "payload.candidate_ref", "verification candidate differs from assignment")
            if m["sender"]["role"] == "tester" and p["oracle_ref"] != predecessor["payload"]["oracle_ref"]:
                fail("oracle_binding", "payload.oracle_ref", "Tester cannot change or self-approve strategy")
            if m["sender"]["role"] == "reviewer":
                comparison = p["comparison"]
                plan = plans.get(key)
                if plan is None or comparison["plan_ref"] != plan["payload"]["plan_ref"]:
                    fail("plan_immutable", "payload.comparison.plan_ref", "Reviewer must identify original frozen plan")
                tester = next((x for x in seen.values() if x["message_type"] == "job.report"
                               and x["sender"]["role"] == "tester" and x["task_id"] == m["task_id"]
                               and x["attempt_id"] == m["attempt_id"] and x["payload"]["candidate_ref"] == p["candidate_ref"]), None)
                if tester is None:
                    fail("comparison_evidence", "payload.comparison", "actual prior Tester report for exact candidate required")
                worker = next((x for x in seen.values() if x["message_type"] == "job.report"
                               and x["sender"]["role"] == "worker" and x["task_id"] == m["task_id"]
                               and x["attempt_id"] == m["attempt_id"] and x["payload"]["candidate_ref"] == p["candidate_ref"]), None)
                if worker is None or tester["payload"]["candidate_ref"] != worker["payload"]["candidate_ref"]:
                    fail("candidate", "payload.comparison.candidate_ref", "must bind the Worker's actual candidate checked by Tester")
                tc = comparison["independent_rerun"]
                tester_ref = comparison["tester_report_ref"]
                if tester_ref["artifact_id"] != tester["message_id"] or tester_ref["kind"] != "message":
                    fail("comparison_evidence", "payload.comparison.tester_report_ref", "must reference the exact earlier Tester message")
                if root is not None:
                    tester_file = read_json(Path(root) / tester_ref["path"])
                    if tester_file != tester:
                        fail("comparison_evidence", "payload.comparison.tester_report_ref", "referenced bytes must contain the exact earlier Tester message")
                commands = tester["payload"].get("deterministic_commands", [])
                declared = next((x for x in commands if x["command_id"] == tc.get("command_id")), None)
                if tc["status"] == "NOT_COMPARABLE":
                    if commands:
                        fail("comparison", "payload.comparison.independent_rerun", "Tester declared a deterministic command; Reviewer must select one")
                else:
                    if declared is None:
                        fail("comparison_evidence", "payload.comparison.independent_rerun.command_id", "must select an actual Tester-declared command")
                    if tc["acceptance_id"] not in p["acceptance_ids"]:
                        fail("comparison_binding", "payload.comparison.independent_rerun.acceptance_id", "rerun must address an assigned Reviewer criterion")
                    for field in ("command", "arguments", "workdir", "candidate_ref", "input_refs", "acceptance_id"):
                        if tc[field] != declared[field]:
                            fail("comparison_binding", "payload.comparison.independent_rerun." + field, "rerun conditions differ from Tester record")
                    if tc["tester_exit_code"] != declared["exit_code"] or tc["tester_stdout_sha256"] != declared["stdout_sha256"] or tc["tester_evidence_ref"] != declared["evidence_ref"]:
                        fail("comparison_binding", "payload.comparison.independent_rerun", "Tester execution result/evidence identity changed")
                    if not any(tc["tester_evidence_ref"] == x for x in tester["evidence_refs"]):
                        fail("comparison_evidence", "payload.comparison.independent_rerun.tester_evidence_ref", "Tester execution record must be cited by Tester report")
                    if not any(tc["evidence_ref"] == x for x in m["evidence_refs"]):
                        fail("comparison_evidence", "payload.comparison.independent_rerun.evidence_ref", "Reviewer rerun record must be cited by Reviewer report")
                    if p["status"] == "passed" and tc["status"] != "MATCH":
                        fail("comparison", "payload.status", "only an exactly matching independent rerun can pass review")
                if not comparison["findings"]:
                    fail("comparison", "payload.comparison.findings", "record comparison findings against plan, candidate and Tester evidence")
            if p["acceptance_ids"] != predecessor["payload"]["acceptance_ids"]:
                fail("acceptance", "payload.acceptance_ids", "report changed assigned criteria")
        if kind == "job.assign" and predecessor:
            if predecessor["message_type"] == "task.decision" and predecessor["payload"]["disposition"] == "rework":
                if m["recipient"]["role"] == "worker":
                    if m["attempt_id"] == predecessor["attempt_id"]:
                        fail("fresh_attempt", "attempt_id", "repair requires fresh attempt")
                    old_workers = {x["recipient"]["instance_id"] for x in seen.values()
                                   if x["message_type"] == "job.assign" and x["attempt_id"] == predecessor["attempt_id"]
                                   and x["recipient"]["role"] == "worker"}
                    if m["recipient"]["instance_id"] in old_workers:
                        fail("fresh_worker", "recipient.instance_id", "repair requires fresh native Worker")
            elif m["attempt_id"] != predecessor["attempt_id"]:
                fail("attempt", "attempt_id", "unexpected attempt change")
        if kind == "task.decision":
            reports = []
            for report_id in p["report_ids"]:
                report = seen.get(report_id)
                if report is None or report["message_type"] != "job.report":
                    fail("decision_evidence", "payload.report_ids", "known prior reports required")
                if any(report[f] != m[f] for f in ("plan_id", "plan_revision", "task_id", "attempt_id")):
                    fail("decision_identity", "payload.report_ids", "report belongs to another task/attempt")
                if report["payload"]["candidate_ref"] != p["candidate_ref"]:
                    fail("candidate", "payload.report_ids", "report candidate differs")
                reports.append(report)
            if p["disposition"] == "accept":
                known_failures = [r for r in seen.values()
                                  if r["message_type"] == "job.report" and r["sender"]["role"] in {"tester", "reviewer"}
                                  and r["payload"]["status"] == "failed"
                                  and all(r[f] == m[f] for f in ("plan_id", "plan_revision", "task_id", "attempt_id"))
                                  and r["payload"]["candidate_ref"] == p["candidate_ref"]]
                if known_failures:
                    fail("failed_verification", "payload.report_ids", "cannot hide known failed mandatory verification for this candidate")
                if any(r["sender"]["role"] in {"tester", "reviewer"} and r["payload"]["status"] != "passed" for r in reports):
                    fail("failed_verification", "payload.report_ids", "cannot accept supplied failed mandatory verification")
                testers = [r for r in reports if r["sender"]["role"] == "tester" and r["payload"]["status"] == "passed"]
                reviewers = [r for r in reports if r["sender"]["role"] == "reviewer" and r["payload"]["status"] == "passed"]
                workers = {r["sender"]["instance_id"] for r in reports if r["sender"]["role"] == "worker"}
                if not testers or not reviewers:
                    fail("independent_evidence", "payload.report_ids", "passing separate Tester and Reviewer required")
                identities = {r["sender"]["instance_id"] for r in testers + reviewers}
                if len(identities) < 2 or identities & workers:
                    fail("independent_evidence", "payload.report_ids", "role sessions must be distinct")
                for role_reports in (testers, reviewers):
                    covered = set().union(*(set(r["payload"]["acceptance_ids"]) for r in role_reports))
                    if not set(p["acceptance_ids"]) <= covered:
                        fail("acceptance", "payload.report_ids", "Tester and Reviewer must each cover all required criteria")
            if p["disposition"] == "rework":
                failures = [r for r in reports if r["payload"]["status"] == "failed"]
                planner_check = predecessor if predecessor and predecessor["message_type"] == "plan.check" else None
                if planner_check is not None:
                    if planner_check["payload"]["status"] == "passed":
                        fail("rework_evidence", "in_reply_to", "Planner rework must cite a failed or blocked check")
                    check_progress = seen.get(planner_check["in_reply_to"])
                    if not check_progress or check_progress["message_type"] != "plan.progress":
                        fail("rework_evidence", "in_reply_to", "failed Planner check must follow Manager progress")
                    prior_acceptance = seen.get(check_progress["in_reply_to"])
                    if (not prior_acceptance or prior_acceptance["message_type"] != "task.decision"
                            or prior_acceptance["payload"]["disposition"] != "accept"
                            or prior_acceptance["payload"]["candidate_ref"] != p["candidate_ref"]
                            or prior_acceptance["attempt_id"] != m["attempt_id"]):
                        fail("rework_evidence", "in_reply_to", "Planner-detected rework must preserve the earlier Manager acceptance of this candidate")
                    if not set(prior_acceptance["payload"]["report_ids"]) <= set(p["report_ids"]):
                        fail("rework_evidence", "payload.report_ids", "rework must retain the reports cited by the earlier Manager acceptance")
                    planner_failures = {result["acceptance_id"] for result in planner_check["payload"]["results"]
                                        if result["status"] in {"failed", "blocked", "unverified"}}
                    if not planner_failures:
                        fail("rework_evidence", "in_reply_to", "failed Planner check must identify unmet original criteria")
                    if set(p["failed_acceptance_ids"]) != planner_failures:
                        fail("rework_evidence", "payload.failed_acceptance_ids", "must preserve every failed Planner criterion exactly")
                elif not failures:
                    fail("rework_evidence", "payload.report_ids", "failed verification or a failed Planner check must be explicit")
                known_failed = set().union(*(set(r["payload"]["acceptance_ids"]) for r in failures)) if failures else set()
                if planner_check is not None:
                    known_failed.update(planner_failures)
                if not set(p["failed_acceptance_ids"]) <= (set(p["acceptance_ids"]) & known_failed):
                    fail("acceptance", "payload.failed_acceptance_ids", "failed IDs must belong to original assigned criteria and supplied failure evidence")
        if kind == "plan.check" and key in plans:
            original = plans[key]
            if m["sender"] != original["sender"] or m["recipient"] != original["recipient"]:
                fail("plan_origin", "sender/recipient", "final check requires the original Planner and Manager actors")
            if p["plan_ref"] != plans[key]["payload"]["plan_ref"]:
                fail("plan_immutable", "payload.plan_ref", "must check original plan")
            if p["status"] == "passed":
                acceptance = predecessor if predecessor and predecessor["message_type"] == "task.decision" else None
                if predecessor and predecessor["message_type"] == "plan.progress":
                    progress_acceptance = seen.get(predecessor["in_reply_to"])
                    if progress_acceptance and progress_acceptance["message_type"] == "task.decision":
                        acceptance = progress_acceptance
                        if predecessor["payload"].get("candidate_ref") not in (None, acceptance["payload"]["candidate_ref"]):
                            fail("final_check_context", "in_reply_to", "Manager progress cannot change the accepted candidate")
                if (acceptance is None or acceptance["payload"]["disposition"] != "accept"
                        or acceptance["attempt_id"] != m["attempt_id"]):
                    fail("final_check_context", "in_reply_to", "passing final check must follow Manager evidence acceptance, directly or through its progress packet")
        if kind == "approval.decision":
            if not predecessor or predecessor["message_type"] != "approval.request" or p["approval_request_id"] != reply:
                fail("approval_reference", "payload.approval_request_id", "actual prior request required")
            if p["provenance_ref"]["artifact_id"] not in owner_provenance:
                fail("owner_provenance", "payload.provenance_ref", "external Owner provenance is required")
            if m["sender"] != predecessor["recipient"]:
                fail("approval_origin", "sender", "must match intended human Owner")
        refs = list(m["evidence_refs"])
        refs.extend(p[name] for name in ("candidate_ref", "input_candidate_ref", "plan_ref", "oracle_ref", "operation_ref", "provenance_ref") if name in p)
        refs.extend(check["evidence_ref"] for check in p.get("checks", []))
        for command in p.get("deterministic_commands", []):
            refs.extend([command["candidate_ref"], command["evidence_ref"]] + command["input_refs"])
        if "comparison" in p:
            refs.extend(p["comparison"][k] for k in ("plan_ref", "tester_report_ref", "candidate_ref"))
            rerun = p["comparison"]["independent_rerun"]
            refs.extend(rerun[k] for k in ("candidate_ref", "evidence_ref", "tester_evidence_ref") if k in rerun)
            refs.extend(rerun.get("input_refs", []))
        refs.extend(ref for result in p.get("results", []) for ref in result["evidence_refs"])
        for ref in refs:
            previous = artifact_ids.get(ref["artifact_id"])
            if previous is not None and ref != previous:
                fail("artifact_identity", "evidence_refs", "same artifact identity cannot change content/path")
            artifact_ids[ref["artifact_id"]] = ref
        seen[mid] = m
    return messages


def parse_policy(source):
    """Restricted block YAML: two-space maps and JSON-compatible scalars/lists."""
    try:
        raw = source.encode("utf-8", "strict") if isinstance(source, str) else bytes(source)
    except (UnicodeError, TypeError, ValueError):
        fail("policy_utf8", "$", "policy must be UTF-8")
    if len(raw) > MAX_BYTES:
        fail("policy_size", "$", "policy exceeds limit")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError:
        fail("policy_utf8", "$", "policy must be UTF-8")
    root = {}
    stack = [(-2, root)]
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            fail("policy_yaml", str(number), "tabs are unsupported")
        match = re.fullmatch(r"( *)([a-z][a-z0-9_]*):(?: (.*))?", line)
        if not match or len(match[1]) % 2:
            fail("policy_yaml", str(number), "use two-space block mappings")
        indent, key, value = len(match[1]), match[2], match[3]
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack or indent != stack[-1][0] + 2 or len(stack) > MAX_DEPTH:
            fail("policy_yaml", str(number), "invalid nesting")
        parent = stack[-1][1]
        if key in parent:
            fail("policy_duplicate", str(number), key)
        if value is None or value == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            # Quoted strings, integer/bool scalars, inline arrays of strings only.
            scalar = loads(value)
            if not (type(scalar) in {str, int, bool} or
                    (type(scalar) is list and all(type(x) is str for x in scalar))):
                fail("policy_yaml", str(number), "unsupported scalar or YAML feature")
            parent[key] = scalar
    return root


def validate_policy(policy):
    """Semantic invariants, not executable authorization or OS enforcement."""
    _object(policy, {"protocol", "version", "communication", "roles", "workflow", "authority",
                     "evidence", "context", "resources", "security", "native"})
    if policy["protocol"] != "council-flow-policy" or policy["version"] != "1.0":
        fail("policy_version", "$", "unsupported policy")
    expected = {
        "communication": {"tasks": "utf-8-json", "policy": "yaml", "native": "toml",
                          "diagnostics": "optional-jsonl", "owner": "concise-natural-language"},
        "workflow": {"order": ["owner", "planner", "manager", "worker", "tester", "reviewer",
                               "manager", "planner", "owner"]},
        "authority": {"owner_only": ["consequential_scope", "new_authorization", "subjective_acceptance"],
                      "never_self_authorize": ["external_paths", "global_configuration", "permission_bypass",
                                               "deployment", "paid_provider", "weaken_acceptance"],
                      "ordinary_repair_owner_approval": False},
        "evidence": {"independent_tests": True, "candidate_hashes": True, "original_acceptance": True,
                     "reviewer_comparison": "original_plan_candidate_tester_evidence_and_independent_rerun",
                     "execution_claims_require_recorded_evidence": True, "tester_self_approves_oracle": False},
        "context": {"fresh_worker_each_attempt": True, "independent_tester": True,
                    "independent_reviewer": True, "one_mutating_worker": True},
        "resources": {"engineering_rework": "no_fixed_lifetime_limit",
                      "stop_identical_unproductive_retries": True, "infrastructure_retries": 3,
                      "crash_recoveries": 2, "retry_accounting": "instruction_only"},
        "security": {"permissions": "inherit_native_codex", "grants_os_permissions": False,
                     "authenticates_senders": False, "native_transport_enforced": False},
        "native": {"format": "toml", "fields": ["name", "description", "developer_instructions"],
                   "mapping": "policy responsibilities become developer_instructions; no invented keys"},
    }
    for key, value in expected.items():
        # Python True == 1 is intentionally insufficient here.
        if json.dumps(policy[key], sort_keys=True) != json.dumps(value, sort_keys=True):
            fail("policy_semantics", key, "required authority/workflow invariant changed")
    _object(policy["roles"], ROLES, field="roles")
    abilities = {"owner": [], "planner": ["plan", "final_check"],
                 "manager": ["delegate", "request_rework", "evaluate_evidence"],
                 "worker": ["implement"], "tester": ["technical_test"], "reviewer": ["compare_evidence", "independent_rerun"]}
    for role in ROLES:
        definition = policy["roles"][role]
        _object(definition, {"responsibilities", "abilities", "application_code"}, field="roles." + role)
        _strings(definition["responsibilities"], "roles." + role + ".responsibilities", True)
        if definition["abilities"] != abilities[role] or type(definition["application_code"]) is not bool:
            fail("policy_authority", "roles." + role, "role authority changed")
        if definition["application_code"] != (role == "worker"):
            fail("policy_authority", "roles." + role, "only Worker implements")
    return policy


def validate_jsonl(source, *, messages=None, root=None):
    try:
        raw = source.encode("utf-8", "strict") if isinstance(source, str) else bytes(source)
    except (UnicodeError, TypeError, ValueError):
        fail("events_utf8", "$", "events must be UTF-8")
    if len(raw) > 1048576:
        fail("events_size", "$", "maximum JSONL export is 1 MiB")
    lines = raw.splitlines()
    if len(lines) > 1024:
        fail("events_size", "$", "maximum 1024 events")
    known = {m["message_id"]: m for m in messages} if messages is not None else None
    seen = set()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            fail("event_line", str(number), "blank diagnostic lines are unsupported")
        event = loads(line)
        _object(event, {"protocol", "version", "event_id", "event_type", "created_at", "message_id",
                        "plan_id", "task_id", "attempt_id", "evidence_refs"})
        if event["protocol"] != "council-flow" or event["version"] != "1.0":
            fail("event_version", str(number), "unsupported diagnostic version")
        for field in ("event_id", "message_id", "plan_id", "task_id", "attempt_id"):
            _identity(event[field], field)
        _enum(event["event_type"], EVENT_TYPES, "event_type")
        _timestamp(event["created_at"])
        _refs(event["evidence_refs"], root)
        if event["event_id"] in seen:
            fail("event_identity", str(number), "duplicate event")
        seen.add(event["event_id"])
        if known is not None:
            message = known.get(event["message_id"])
            if message is None or any(message[f] != event[f] for f in ("plan_id", "task_id", "attempt_id")):
                fail("event_reference", str(number), "event does not match supplied message")
    return len(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["message", "sequence", "policy", "events"])
    parser.add_argument("files", nargs="+")
    parser.add_argument("--root", type=Path, help="verify referenced artifact existence/hash inside this root")
    parser.add_argument("--expected-sender", choices=sorted(ROLES))
    parser.add_argument("--expected-instance")
    parser.add_argument("--bindings", type=Path, help="trusted JSON map message_id -> externally observed actor")
    parser.add_argument("--owner-provenance", action="append", default=[], help="externally confirmed Owner artifact identity")
    parser.add_argument("--authoritative-criteria-ref", type=Path,
                        help="trusted caller-supplied artifact reference to Owner-approved criteria JSON")
    parser.add_argument("--require-criteria-fidelity", action="store_true",
                        help="fail closed unless plan criteria exactly match --authoritative-criteria-ref")
    args = parser.parse_args(argv)
    try:
        if args.mode != "sequence" and (args.require_criteria_fidelity or args.authoritative_criteria_ref):
            fail("criteria_mode", "mode", "criteria fidelity options apply only to sequence validation")
        expected = None
        if args.expected_sender or args.expected_instance:
            if not args.expected_sender or not args.expected_instance:
                fail("origin_binding", "$", "supply both expected sender and instance")
            expected = {"role": args.expected_sender, "instance_id": args.expected_instance}
        if args.mode == "message":
            for path in args.files:
                validate_message(read_json(path), root=args.root, expected_sender=expected)
        elif args.mode == "sequence":
            bindings = read_json(args.bindings) if args.bindings else {}
            criteria_ref = read_json(args.authoritative_criteria_ref) if args.authoritative_criteria_ref else None
            validate_sequence([read_json(p) for p in args.files], root=args.root,
                              expected_senders=bindings, owner_provenance=args.owner_provenance,
                              authoritative_criteria_ref=criteria_ref,
                              require_criteria_fidelity=args.require_criteria_fidelity)
        elif args.mode == "policy":
            for path in args.files:
                validate_policy(parse_policy(Path(path).read_bytes()))
        else:
            for path in args.files:
                validate_jsonl(Path(path).read_bytes(), root=args.root)
        print(json.dumps({"valid": True, "mode": args.mode, "files": len(args.files),
                          "limits": {"message_bytes": MAX_BYTES, "container_depth": MAX_DEPTH},
                          "boundary": "controlled records only; not authentication/native transport enforcement"}))
        return 0
    except (ContractError, OSError) as exc:
        error = {"valid": False, "error": getattr(exc, "code", "io"),
                 "field": getattr(exc, "field", "$"), "message": str(exc)}
        print(json.dumps(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
