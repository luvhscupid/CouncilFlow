"""Plain-file project state for CouncilFlow (ADR-001 section 3).

Commands: init, source-add, bootstrap, validate, affected (read-only), retest-select (read-only),
retest-record (writes evidence/ and retest/ only; ADR-001 M5), audit-select (read-only) and
audit-record (writes evidence/ and audit/; an Owner-decision finding also pauses the slices it
names; ADR-001 M6, advisory Technical Audit). Every command prints one JSON
object (`status` PASS or FAIL, `errors`, sorted keys) and exits 0 on PASS, 1 on
FAIL and 2 on a usage error. Nothing is written outside --project and an
existing file is never overwritten.

Structural validation only: it does not authenticate who wrote a file, does not
enforce role ownership (Planner writes the ledger, Manager the plan), and is not
a database, runtime or transport. Nothing in the workflow calls it yet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
import re
import sys

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
sys.dont_write_bytecode = True

import strict_json  # noqa: E402

ENTRY_FIELDS = {"id", "type", "content", "source_ids", "evidence_ids", "status",
                "created_at", "version_introduced", "supersedes", "affected_slices"}
TYPES = ("Goal", "Requirement", "Assumption", "Constraint", "Decision", "Open")
STATUSES = {"Assumption": ("unconfirmed", "confirmed", "rejected", "superseded"),
            "Open": ("open", "resolved", "superseded")}
DEFAULT_STATUSES = ("active", "superseded")
MOVES = {"Assumption": {"unconfirmed": {"confirmed", "rejected", "superseded"}},
         "Open": {"open": {"resolved", "superseded"}}}
SOURCE_FIELDS = {"source_id", "kind", "received_at", "path", "sha256"}
SLICE_FIELDS = {"slice_id", "ledger_version", "ledger_ids", "depends_on", "readiness",
                "status", "run_dir", "model_routing"}
EVIDENCE_FIELDS = {"evidence_id", "source_agent", "finding", "artifacts", "ledger_ids",
                   "affected_slices", "created_at", "reopen_request"}
REOPEN_FIELDS = {"status", "contradiction", "consequence"}
SOURCE_RE = re.compile(r"^S(\d{4,})$")
LEDGER_RE = re.compile(r"^L(\d{4,})\.json$")
EVIDENCE_RE = re.compile(r"^E(\d{4,})$")
RETEST_FIELDS = {"retest_id", "slice_id", "ledger_version", "ledger_ids", "result",
                 "evidence_id", "oracle", "model_routing", "created_at"}
RETEST_RE = re.compile(r"^T(\d{4,})$")
RETEST_RESULTS = ("pass", "fail")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
# Technical Audit (ADR-001 M6). Advisory: a record never claims delivery or approval.
AUDIT_FIELDS = {"audit_id", "ledger_version", "goal_ids", "goal_version", "verdicts",
                "independent_rerun", "artifacts", "model_routing", "paused_slices", "created_at"}
VERDICT_FIELDS = {"ledger_id", "verdict", "finding", "route", "decision_class",
                  "affected_slices", "evidence_id"}
RERUN_INPUT = {"command_id", "command", "arguments", "workdir", "exit_code", "stdout_sha256",
               "tester_exit_code", "tester_stdout_sha256", "tester_evidence", "output"}
RERUN_FIELDS = RERUN_INPUT | {"status"}
FINDING_INPUT = {"ledger_id", "verdict", "finding", "route", "affected_slices", "decision_class",
                 "contradiction", "consequence", "evidence"}
AUDIT_RE = re.compile(r"^A(\d{4,})$")
VERDICTS = ("gap", "risk", "pass")
# none: pass, or ordinary engineering for the Manager; reopen: a Reopen Request to the Planner;
# owner_decision: pauses the named slices for the Manager to present to the Owner.
AUDIT_ROUTES = ("none", "reopen", "owner_decision")
# Owner-controlled classes from policies/roles.yaml adaptive.decision_classes (all but the
# Planner's cheap_reversible default class).
OWNER_CLASSES = ("costly_reversible", "irreversible_external", "security_data_financial_legal",
                 "owner_objective")
DELIVERY_KEY = re.compile(r"deliver|approv|accept", re.IGNORECASE)


class Errors(list):
    def add(self, code, path, detail):
        self.append({"code": code, "path": str(path), "detail": detail})


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _dump(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _int(value):
    return type(value) is int


def _timestamp_ok(value):
    if type(value) is not str or not (value.endswith("Z") or value.endswith("+00:00")):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return True


def _create(path, data):
    """Exclusive create; returns an error dict list entry or None."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as handle:
            handle.write(data)
    except FileExistsError:
        return {"code": "exists", "path": str(path), "detail": "refusing to overwrite"}
    return None


def _load(path, errors):
    try:
        return strict_json.loads(path.read_bytes().decode("utf-8"), str(path))
    except (OSError, ValueError) as exc:  # ContractError and JSONDecodeError are ValueErrors
        errors.add("bad_json", path, str(exc))
        return None


def _str_list(value):
    return type(value) is list and all(type(item) is str for item in value)


def _numbered(directory, pattern, suffix, errors, label):
    """Return {number: path} for matching files; report gaps and strangers."""
    found = {}
    if not directory.is_dir():
        return found
    for item in sorted(directory.iterdir()):
        match = pattern.match(item.name[:-len(suffix)] if suffix and item.name.endswith(suffix) else item.name)
        if item.is_file() and match and (not suffix or item.name.endswith(suffix)):
            found[int(match.group(1))] = item
        elif label != "source" or item.suffix not in (".json", ".txt"):
            errors.add("unexpected_file", item, f"not a valid {label} file name")
    for number in range(1, max(found, default=0) + 1):
        if number not in found:
            errors.add("numbering_gap", directory, f"{label} number {number} is missing")
    return found


# --- sources -----------------------------------------------------------------

def _check_sources(project, errors):
    """Return (ids, bad_ids) of source records present."""
    directory = project / "sources"
    ids, bad = set(), set()
    if not directory.is_dir():
        return ids, bad
    numbers, stems = {}, {}
    for item in sorted(directory.iterdir()):
        match = SOURCE_RE.match(item.stem)
        if item.is_file() and match and item.suffix in (".json", ".txt"):
            stems.setdefault(int(match.group(1)), {})[item.suffix] = item
        else:
            errors.add("unexpected_file", item, "not a valid source file name")
    for number in range(1, max(stems, default=0) + 1):
        if number not in stems:
            errors.add("numbering_gap", directory, f"source number {number} is missing")
    for number, pair in sorted(stems.items()):
        sid = f"S{number:04d}" if number < 10000 else f"S{number}"
        if ".json" not in pair:
            errors.add("orphan_source_text", pair[".txt"], "no matching record")
            continue
        if ".txt" not in pair:
            errors.add("orphan_source_record", pair[".json"], "no matching text")
        record = _load(pair[".json"], errors)
        ids.add(pair[".json"].stem)
        if record is None:
            bad.add(pair[".json"].stem)
            continue
        if type(record) is not dict or set(record) != SOURCE_FIELDS:
            errors.add("bad_fields", pair[".json"], f"expected exactly {sorted(SOURCE_FIELDS)}")
            bad.add(pair[".json"].stem)
            continue
        stem = pair[".json"].stem
        if record["source_id"] != stem:
            errors.add("source_id_mismatch", pair[".json"], "source_id differs from file name")
            bad.add(stem)
        if type(record["kind"]) is not str or not record["kind"].strip():
            errors.add("bad_value", pair[".json"], "kind must be a nonempty string")
        if not _timestamp_ok(record["received_at"]):
            errors.add("bad_timestamp", pair[".json"], "received_at must be ISO-8601 UTC")
        if record["path"] != stem + ".txt":
            errors.add("source_path_mismatch", pair[".json"], "path must be the sibling .txt")
            bad.add(stem)
        if ".txt" in pair:
            if record["sha256"] != _sha(pair[".txt"].read_bytes()):
                errors.add("source_hash_mismatch", pair[".txt"], "sha256 differs from stored bytes")
                bad.add(stem)
    return ids, bad


# --- ledger ------------------------------------------------------------------

def _check_entry(entry, where, version, sources, bad_sources, evidence, errors):
    if type(entry) is not dict or set(entry) != ENTRY_FIELDS:
        errors.add("entry_fields", where, f"expected exactly {sorted(ENTRY_FIELDS)}")
        return None
    ok = True
    if type(entry["id"]) is not str or not entry["id"].strip():
        errors.add("entry_id", where, "id must be a nonempty string")
        ok = False
    if entry["type"] not in TYPES:
        errors.add("entry_type", where, f"type must be one of {list(TYPES)}")
        ok = False
    elif entry["status"] not in STATUSES.get(entry["type"], DEFAULT_STATUSES):
        errors.add("entry_status", where, f"status {entry['status']!r} invalid for {entry['type']}")
        ok = False
    if type(entry["content"]) is not str or not entry["content"].strip():
        errors.add("entry_content", where, "content must be a nonempty string")
        ok = False
    if not _timestamp_ok(entry["created_at"]):
        errors.add("bad_timestamp", where, "created_at must be ISO-8601 UTC")
    for key in ("source_ids", "evidence_ids", "supersedes", "affected_slices"):
        if not _str_list(entry[key]):
            errors.add("entry_list", where, f"{key} must be a list of strings")
            ok = False
    if not _int(entry["version_introduced"]) or not 1 <= entry["version_introduced"] <= version:
        errors.add("version_introduced", where, "must be an integer from 1 to this ledger_version")
        ok = False
    if not ok:
        return None
    if not entry["source_ids"] and not entry["evidence_ids"]:
        errors.add("entry_untraceable", where, "needs source_ids or evidence_ids")
    for sid in entry["source_ids"]:
        if sid not in sources:
            errors.add("source_missing", where, f"unknown source {sid!r}")
        elif sid in bad_sources:
            errors.add("source_hash_mismatch", where, f"source {sid!r} fails its integrity check")
    for eid in entry["evidence_ids"]:
        if eid not in evidence:
            errors.add("evidence_missing", where, f"unknown evidence {eid!r}")
    return entry


def _check_transition(prev, cur, version, errors, where):
    prev_by, cur_by = {e["id"]: e for e in prev}, {e["id"]: e for e in cur}
    new = [e for e in cur if e["id"] not in prev_by]
    decision = any(e["type"] == "Decision" and e["source_ids"] for e in new)
    promoted = False
    for eid, old in prev_by.items():
        now = cur_by.get(eid)
        if now is None:
            errors.add("entry_dropped", where, f"entry {eid} missing from this version")
            continue
        for key in ENTRY_FIELDS - {"status"}:
            if old[key] != now[key]:
                errors.add("entry_changed", where, f"entry {eid} changed {key}")
        if old["status"] != now["status"]:
            allowed = MOVES.get(old["type"], {}).get(old["status"], set())
            if old["type"] not in MOVES and old["status"] == "active":
                allowed = {"superseded"}
            if now["status"] not in allowed:
                errors.add("status_transition", where,
                           f"entry {eid}: {old['status']} to {now['status']} is not allowed")
            if now["status"] == "superseded" and not any(
                    eid in n["supersedes"] for n in new):
                errors.add("supersede_unbacked", where,
                           f"entry {eid} superseded without a new entry listing it")
            if old["type"] == "Assumption" and now["status"] in ("confirmed", "rejected"):
                promoted = True
    for entry in new:
        if entry["version_introduced"] != version:
            errors.add("new_entry_version", where, f"new entry {entry['id']} must be introduced in {version}")
        if entry["status"] == "superseded":
            errors.add("born_superseded", where, f"new entry {entry['id']} cannot start superseded")
        for sid in entry["supersedes"]:
            target = prev_by.get(sid)
            if target is None:
                errors.add("supersedes_unknown", where, f"{entry['id']} supersedes {sid!r}, not in previous version")
            elif sid not in cur_by:
                continue  # already reported as entry_dropped
            elif cur_by[sid]["status"] != "superseded":
                errors.add("supersedes_not_superseded", where, f"{sid} must be superseded in this version")
            elif entry["type"] == "Requirement" and target["type"] == "Assumption":
                promoted = True
    if promoted and not decision:
        errors.add("promotion_without_decision", where,
                   "confirming, rejecting or promoting an Assumption needs a new Decision entry with sources")


def _check_ledgers(project, sources, bad_sources, evidence, errors):
    """Return {version: set(entry ids)} and the latest version's entries."""
    files = _numbered(project / "ledger", LEDGER_RE, "", errors, "ledger")
    ids, prev_entries, prev_bytes, latest = {}, None, None, None
    for number in sorted(files):
        path = files[number]
        raw = path.read_bytes()
        data = _load(path, errors)
        if data is None:
            prev_entries = prev_bytes = None
            continue
        fields = {"schema", "version", "ledger_version", "previous_sha256", "created_at", "entries"}
        if type(data) is not dict or set(data) != fields:
            errors.add("bad_fields", path, f"expected exactly {sorted(fields)}")
            prev_entries = prev_bytes = None
            continue
        if data["schema"] != "councilflow-ledger" or data["version"] != "1.0":
            errors.add("bad_schema", path, "expected councilflow-ledger version 1.0")
        if data["ledger_version"] != number or not _int(data["ledger_version"]):
            errors.add("ledger_version_mismatch", path, "ledger_version must equal the file number")
        if not _timestamp_ok(data["created_at"]):
            errors.add("bad_timestamp", path, "created_at must be ISO-8601 UTC")
        expected = None if number == 1 else (_sha(prev_bytes) if prev_bytes is not None else False)
        if expected is not False and data["previous_sha256"] != expected:
            errors.add("previous_hash_mismatch", path, "previous_sha256 does not match the previous version file")
        if type(data["entries"]) is not list:
            errors.add("entry_fields", path, "entries must be a list")
            prev_entries = prev_bytes = None
            continue
        entries, seen = [], set()
        for index, raw_entry in enumerate(data["entries"]):
            where = f"{path}#entries[{index}]"
            entry = _check_entry(raw_entry, where, number, sources, bad_sources, evidence, errors)
            if entry is None:
                continue
            if entry["id"] in seen:
                errors.add("entry_duplicate_id", where, f"duplicate entry id {entry['id']!r}")
            seen.add(entry["id"])
            entries.append(entry)
        valid = len(entries) == len(data["entries"])
        if number == 1:
            for entry in entries:
                if entry["supersedes"]:
                    errors.add("supersedes_unknown", path, "version 1 cannot supersede entries")
                if entry["version_introduced"] != 1:
                    errors.add("new_entry_version", path, "version 1 entries must be introduced in 1")
                if entry["status"] == "superseded":
                    errors.add("born_superseded", path, f"new entry {entry['id']} cannot start superseded")
        elif prev_entries is not None and valid:
            _check_transition(prev_entries, entries, number, errors, str(path))
        ids[number] = seen
        latest = (number, entries)
        prev_entries, prev_bytes = (entries if valid else None), raw
    return ids, latest


# --- plan and evidence -------------------------------------------------------

ROUTING_FIELDS = {"hint", "used", "source", "reason"}


def _check_routing(routing, where, errors):
    if routing is None:
        return
    if type(routing) is not dict:
        errors.add("slice_model_routing", where, "model_routing must be an object or null")
        return
    for role, choice in routing.items():
        spot = f"{where}.model_routing.{role}"
        if role not in ("worker", "tester", "reviewer"):
            errors.add("slice_model_routing", spot, "role must be worker, tester or reviewer")
        elif type(choice) is not dict or set(choice) != ROUTING_FIELDS:
            errors.add("slice_model_routing", spot, f"expected exactly {sorted(ROUTING_FIELDS)}")
        elif (choice["hint"] is not None and type(choice["hint"]) is not str) or (
                type(choice["used"]) is not str or not choice["used"].strip()):
            errors.add("slice_model_routing", spot, "hint must be a string or null; used a nonempty string")
        elif choice["source"] not in ("hint", "role_default", "host"):
            errors.add("slice_model_routing", spot, "source must be hint, role_default or host")
        elif type(choice["reason"]) is not str or not choice["reason"].strip():
            errors.add("slice_model_routing", spot, "reason must be a nonempty string")
        elif choice["source"] == "hint" and (choice["hint"] is None or choice["hint"] != choice["used"]):
            errors.add("slice_model_routing", spot, "source hint needs a non-null hint equal to used")
        elif role == "reviewer" and "haiku" in choice["used"].lower():
            errors.add("reviewer_haiku", spot, "the Reviewer never runs on Haiku; use Sonnet or Opus")


def _check_plan(project, ledger_ids, errors):
    path = project / "plan.json"
    if not path.exists():
        return
    plan = _load(path, errors)
    if plan is None:
        return
    fields = {"schema", "version", "plan_version", "slices"}
    if type(plan) is not dict or set(plan) != fields:
        errors.add("bad_fields", path, f"expected exactly {sorted(fields)}")
        return
    if plan["schema"] != "councilflow-plan" or plan["version"] != "1.0":
        errors.add("bad_schema", path, "expected councilflow-plan version 1.0")
    if not _int(plan["plan_version"]) or plan["plan_version"] < 1:
        errors.add("bad_value", path, "plan_version must be an integer >= 1")
    if type(plan["slices"]) is not list:
        errors.add("bad_value", path, "slices must be a list")
        return
    graph, seen = {}, set()
    for index, item in enumerate(plan["slices"]):
        where = f"{path}#slices[{index}]"
        if type(item) is not dict or set(item) != SLICE_FIELDS:
            errors.add("slice_fields", where, f"expected exactly {sorted(SLICE_FIELDS)}")
            continue
        sid = item["slice_id"]
        if type(sid) is not str or not sid.strip():
            errors.add("slice_id", where, "slice_id must be a nonempty string")
            continue
        if sid in seen:
            errors.add("slice_duplicate", where, f"duplicate slice_id {sid!r}")
        seen.add(sid)
        version = item["ledger_version"]
        if not _int(version) or version not in ledger_ids:
            errors.add("slice_ledger_version", where, "ledger_version does not exist")
        refs = item["ledger_ids"]
        if not _str_list(refs) or not refs:
            errors.add("slice_ledger_ids", where, "ledger_ids must be a nonempty list of strings")
        elif _int(version) and version in ledger_ids:
            for ref in refs:
                if ref not in ledger_ids[version]:
                    errors.add("slice_ledger_ref", where, f"{ref!r} not in ledger version {version}")
        if item["readiness"] not in ("READY", "PROCEED_WITH_ASSUMPTIONS", "BLOCKED", None):
            errors.add("slice_readiness", where, "invalid readiness")
        if item["status"] not in ("PLANNED", "RUNNING", "PAUSED", "DONE", "CANCELLED"):
            errors.add("slice_status", where, "invalid status")
        run_dir = item["run_dir"]
        if run_dir is not None:
            parts = re.split(r"[\\/]", run_dir) if type(run_dir) is str else None
            if (parts is None or not run_dir or run_dir.startswith(("/", "\\"))
                    or re.match(r"^[A-Za-z]:", run_dir) or ".." in parts):
                errors.add("slice_run_dir", where, "run_dir must be a relative path without '..'")
        _check_routing(item["model_routing"], where, errors)
        graph[sid] = item["depends_on"]
    for sid, deps in graph.items():
        if not _str_list(deps):
            errors.add("slice_depends_on", path, f"{sid}: depends_on must be a list of strings")
            graph[sid] = []
            continue
        for dep in deps:
            if dep not in graph:
                errors.add("slice_depends_unknown", path, f"{sid} depends on unknown slice {dep!r}")
    remaining = {k: {d for d in v if d in graph} for k, v in graph.items()}
    while True:
        done = [k for k, v in remaining.items() if not v]
        if not done:
            break
        for k in done:
            del remaining[k]
        for v in remaining.values():
            v.difference_update(done)
    if remaining:
        errors.add("slice_cycle", path, f"dependency cycle among {sorted(remaining)}")


def _check_evidence(project, ledger_ids, errors):
    found = _numbered(project / "evidence", re.compile(r"^E(\d{4,})$"), ".json", errors, "evidence")
    every = set().union(*ledger_ids.values()) if ledger_ids else set()
    names = set()
    for number, path in sorted(found.items()):
        names.add(path.stem)
        record = _load(path, errors)
        if record is None:
            continue
        if type(record) is not dict or set(record) != EVIDENCE_FIELDS:
            errors.add("bad_fields", path, f"expected exactly {sorted(EVIDENCE_FIELDS)}")
            continue
        if record["evidence_id"] != path.stem:
            errors.add("evidence_id_mismatch", path, "evidence_id differs from file name")
        if type(record["source_agent"]) is not str or not record["source_agent"].strip():
            errors.add("bad_value", path, "source_agent must be a nonempty string")
        if type(record["finding"]) is not str or not record["finding"].strip():
            errors.add("bad_value", path, "finding must be a nonempty string")
        if not _timestamp_ok(record["created_at"]):
            errors.add("bad_timestamp", path, "created_at must be ISO-8601 UTC")
        for key in ("ledger_ids", "affected_slices"):
            if not _str_list(record[key]):
                errors.add("bad_value", path, f"{key} must be a list of strings")
        arts = record["artifacts"]
        if type(arts) is not list:
            errors.add("evidence_artifacts", path, "artifacts must be a list")
            arts = []
        for art in arts:
            if (type(art) is not dict or set(art) != {"path", "sha256"}
                    or type(art["path"]) is not str or not art["path"]
                    or type(art["sha256"]) is not str or not HEX64.match(art["sha256"])):
                errors.add("evidence_artifacts", path, "artifact needs path and 64-hex sha256")
        if _str_list(record["ledger_ids"]):
            for ref in record["ledger_ids"]:
                if ref not in every:
                    errors.add("evidence_ledger_ref", path, f"{ref!r} not in any ledger version")
        reopen = record["reopen_request"]
        if reopen is None:
            continue
        if (type(reopen) is not dict or set(reopen) != REOPEN_FIELDS
                or reopen["status"] not in ("submitted", "accepted", "declined")
                or any(type(reopen[k]) is not str or not reopen[k].strip()
                       for k in ("contradiction", "consequence"))):
            errors.add("reopen_fields", path, f"reopen_request needs exactly {sorted(REOPEN_FIELDS)}")
        if not record["ledger_ids"]:
            errors.add("reopen_no_ledger_ids", path, "reopen_request needs ledger_ids")
        if not record["affected_slices"]:
            errors.add("reopen_no_slices", path, "reopen_request needs affected_slices")
        if not arts:
            errors.add("reopen_no_artifacts", path, "reopen_request needs artifacts")
    return names


def _check_retests(project, ledger_ids, errors):
    """Tester retest records (M5). Each must agree with the evidence record it cites."""
    found = _numbered(project / "retest", RETEST_RE, ".json", errors, "retest")
    for number, path in sorted(found.items()):
        record = _load(path, errors)
        if record is None:
            continue
        if type(record) is not dict or set(record) != RETEST_FIELDS:
            errors.add("bad_fields", path, f"expected exactly {sorted(RETEST_FIELDS)}")
            continue
        if record["retest_id"] != path.stem:
            errors.add("retest_id_mismatch", path, "retest_id differs from file name")
        version = record["ledger_version"]
        if not _int(version) or version not in ledger_ids:
            errors.add("retest_ledger_version", path, "ledger_version does not exist")
        if type(record["slice_id"]) is not str or not record["slice_id"].strip():
            errors.add("bad_value", path, "slice_id must be a nonempty string")
        if not _str_list(record["ledger_ids"]) or not record["ledger_ids"]:
            errors.add("bad_value", path, "ledger_ids must be a nonempty list of strings")
        elif _int(version) and version in ledger_ids:
            for ref in record["ledger_ids"]:
                if ref not in ledger_ids[version]:
                    errors.add("retest_ledger_ref", path, f"{ref!r} not in ledger version {version}")
        if record["result"] not in RETEST_RESULTS:
            errors.add("bad_value", path, "result must be pass or fail")
        if not _timestamp_ok(record["created_at"]):
            errors.add("bad_timestamp", path, "created_at must be ISO-8601 UTC")
        oracle = record["oracle"]
        if (type(oracle) is not dict or set(oracle) != {"path", "sha256"}
                or type(oracle["path"]) is not str or not oracle["path"]
                or type(oracle["sha256"]) is not str or not HEX64.match(oracle["sha256"])):
            errors.add("retest_oracle", path, "oracle needs path and 64-hex sha256")
        routing = record["model_routing"]
        if type(routing) is not dict or set(routing) != {"tester"}:
            errors.add("slice_model_routing", path, "model_routing must hold exactly the tester choice")
        else:
            _check_routing(routing, str(path), errors)
        evidence_id = record["evidence_id"]
        evidence_path = project / "evidence" / f"{evidence_id}.json"
        if type(evidence_id) is not str or not evidence_path.is_file():
            errors.add("retest_evidence_ref", path, "evidence_id must name an existing evidence record")
            continue
        evidence = _load(evidence_path, Errors())
        if type(evidence) is not dict:
            errors.add("retest_evidence_ref", path, "cited evidence record is unreadable")
            continue
        if evidence.get("source_agent") != "tester":
            errors.add("retest_evidence_agent", path, "retest evidence must come from the tester")
        if record["slice_id"] not in (evidence.get("affected_slices") or []):
            errors.add("retest_evidence_mismatch", path, "cited evidence does not name this slice")
        if (evidence.get("reopen_request") is not None) != (record["result"] == "fail"):
            errors.add("retest_evidence_mismatch", path,
                       "a pass carries no reopen request; a fail carries one")


def _delivery_claims(value):
    """Keys anywhere in an audit record that claim delivery, approval or acceptance."""
    found = []
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is str and DELIVERY_KEY.search(key):
                found.append(key)
            found += _delivery_claims(child)
    elif type(value) is list:
        for child in value:
            found += _delivery_claims(child)
    return found


def _normalized_sha(data):
    """SHA-256 of stdout after CRLF-to-LF replacement only (the Reviewer rerun rule)."""
    return _sha(data.replace(b"\r\n", b"\n"))


def _fingerprint_ok(value):
    return (type(value) is dict and set(value) == {"path", "sha256"} and type(value["path"]) is str
            and value["path"] != "" and type(value["sha256"]) is str and bool(HEX64.match(value["sha256"])))


def _check_rerun(rerun, where, errors):
    """The Reviewer's independent rerun of one Tester-declared deterministic command."""
    if type(rerun) is not dict or set(rerun) != RERUN_FIELDS:
        errors.add("audit_rerun_required", where,
                   f"the audit needs an independent rerun with exactly {sorted(RERUN_FIELDS)}")
        return None
    ok = all(type(rerun[k]) is str and rerun[k].strip() for k in ("command_id", "command", "workdir"))
    ok = ok and _str_list(rerun["arguments"]) and _int(rerun["exit_code"]) and _int(rerun["tester_exit_code"])
    ok = ok and all(type(rerun[k]) is str and HEX64.match(rerun[k])
                    for k in ("stdout_sha256", "tester_stdout_sha256"))
    ok = ok and _fingerprint_ok(rerun["tester_evidence"]) and _fingerprint_ok(rerun["output"])
    if not ok:
        errors.add("audit_rerun_required", where, "rerun needs command, arguments, workdir, integer exit "
                   "codes, 64-hex stdout hashes and hashed tester_evidence and output files")
        return None
    equal = (rerun["exit_code"] == rerun["tester_exit_code"]
             and rerun["stdout_sha256"] == rerun["tester_stdout_sha256"])
    if rerun["status"] not in ("MATCH", "MISMATCH"):
        errors.add("audit_rerun_required", where, "status must be MATCH or MISMATCH; NOT_COMPARABLE cannot "
                   "satisfy the mandatory rerun")
        return None
    if (rerun["status"] == "MATCH") != equal:
        errors.add("audit_rerun_status", where, "status must equal the exit-code and stdout-hash comparison")
    return rerun["status"]


def _version_map(project, version):
    """{id: entry} of one ledger version, or None; errors are already reported by validation."""
    data = _load(project / "ledger" / f"L{version:04d}.json", Errors())
    if type(data) is not dict or type(data.get("entries")) is not list:
        return None
    return {e["id"]: e for e in data["entries"] if type(e) is dict and type(e.get("id")) is str}


def _check_audits(project, ledger_ids, errors):
    """Technical Audit records (M6): advisory, pinned to one ledger version, one per Goal version."""
    found = _numbered(project / "audit", AUDIT_RE, ".json", errors, "audit")
    goal_versions = {}
    for number, path in sorted(found.items()):
        record = _load(path, errors)
        if record is None:
            continue
        claims = _delivery_claims(record)
        if claims:
            errors.add("audit_claims_delivery", path, "the audit is advisory and cannot claim delivery, "
                       f"approval or acceptance (keys {sorted(set(claims))}); the Owner gives final acceptance")
            continue
        if type(record) is not dict or set(record) != AUDIT_FIELDS:
            errors.add("bad_fields", path, f"expected exactly {sorted(AUDIT_FIELDS)}")
            continue
        if record["audit_id"] != path.stem:
            errors.add("audit_id_mismatch", path, "audit_id differs from file name")
        if not _timestamp_ok(record["created_at"]):
            errors.add("bad_timestamp", path, "created_at must be ISO-8601 UTC")
        version = record["ledger_version"]
        entries = _version_map(project, version) if _int(version) and version in ledger_ids else None
        if entries is None:
            errors.add("audit_ledger_version", path, "ledger_version does not exist")
            entries = {}
        goals = record["goal_ids"]
        if not _str_list(goals) or not goals or any(
                entries.get(g, {}).get("type") != "Goal" for g in goals):
            errors.add("audit_goal", path, "goal_ids must name Goal entries of the pinned ledger version")
            goals = []
        goal_version = record["goal_version"]
        if not _int(goal_version) or not (_int(version) and 1 <= goal_version <= version):
            errors.add("bad_value", path, "goal_version must be an integer from 1 to ledger_version")
        elif goal_version in goal_versions:
            errors.add("audit_duplicate_goal", path,
                       f"Goal version {goal_version} was already audited in {goal_versions[goal_version]}")
        else:
            goal_versions[goal_version] = path.stem
        verdicts = record["verdicts"] if type(record["verdicts"]) is list else []
        if not verdicts:
            errors.add("bad_value", path, "verdicts must be a nonempty list")
        seen, paused, kinds = set(), set(), []
        for index, item in enumerate(verdicts):
            where = f"{path}#verdicts[{index}]"
            if type(item) is not dict or set(item) != VERDICT_FIELDS:
                errors.add("bad_fields", where, f"expected exactly {sorted(VERDICT_FIELDS)}")
                continue
            ledger_id = item["ledger_id"] if type(item["ledger_id"]) is str else repr(item["ledger_id"])
            if ledger_id not in entries or entries[ledger_id].get("status") == "superseded":
                errors.add("audit_ledger_ref", where,
                           f"{ledger_id!r} is not a current entry of ledger version {version}")
            if ledger_id in seen:
                errors.add("audit_duplicate", where, f"one verdict per ledger id; {ledger_id!r} repeats")
            seen.add(ledger_id)
            if item["verdict"] not in VERDICTS:
                errors.add("audit_verdict", where, "verdict must be gap, risk or pass")
            kinds.append(item["verdict"])
            if type(item["finding"]) is not str or not item["finding"].strip():
                errors.add("bad_value", where, "finding must be a nonempty string")
            route, slices = item["route"], item["affected_slices"]
            if route not in AUDIT_ROUTES:
                errors.add("audit_route", where, f"route must be one of {list(AUDIT_ROUTES)}")
            elif item["verdict"] == "pass" and route != "none":
                errors.add("audit_route", where, "a pass carries no reopen request and no pause")
            if not _str_list(slices):
                errors.add("bad_value", where, "affected_slices must be a list of strings")
                slices = []
            if route in ("reopen", "owner_decision") and not slices:
                errors.add("audit_route", where, f"route {route} needs affected_slices")
            if (route == "owner_decision") != (item["decision_class"] is not None):
                errors.add("audit_route", where, "decision_class is set exactly for route owner_decision")
            elif route == "owner_decision" and item["decision_class"] not in OWNER_CLASSES:
                errors.add("audit_route", where, f"decision_class must be one of {list(OWNER_CLASSES)}")
            if route == "owner_decision":
                paused.update(slices)
            evidence_path = project / "evidence" / f"{item['evidence_id']}.json"
            if type(item["evidence_id"]) is not str or not evidence_path.is_file():
                errors.add("audit_evidence_ref", where, "evidence_id must name an existing evidence record")
                continue
            evidence = _load(evidence_path, Errors())
            if (type(evidence) is not dict or evidence.get("source_agent") != "reviewer"
                    or evidence.get("ledger_ids") != [ledger_id]
                    or (evidence.get("reopen_request") is not None) != (route == "reopen")):
                errors.add("audit_evidence_mismatch", where, "evidence must come from the reviewer, cite only "
                           "this ledger id, and carry a reopen request exactly for route reopen")
        missing = sorted(set(goals) - seen)
        if missing:
            errors.add("audit_goal_missing", path, f"no verdict for Goal entries {missing}")
        status = _check_rerun(record["independent_rerun"], f"{path}#independent_rerun", errors)
        if status == "MISMATCH" and kinds and all(k == "pass" for k in kinds):
            errors.add("audit_contradiction", path, "a mismatching rerun needs at least one gap or risk")
        arts = record["artifacts"]
        if type(arts) is not list or not arts or not all(_fingerprint_ok(a) for a in arts):
            errors.add("audit_artifacts", path, "artifacts must be a nonempty list of path and 64-hex sha256")
        routing = record["model_routing"]
        if type(routing) is not dict or set(routing) != {"reviewer"}:
            errors.add("slice_model_routing", path, "model_routing must hold exactly the reviewer choice")
        else:
            _check_routing(routing, str(path), errors)
        if record["paused_slices"] != sorted(paused):
            errors.add("audit_paused_mismatch", path,
                       "paused_slices must list exactly the slices of owner_decision findings, sorted")


# --- commands ----------------------------------------------------------------

def validate(project):
    errors = Errors()
    extra = {"ledger_version": None, "budget": {"limit": 0, "used": 0, "exceeded": False}}
    config_path = project / "project.json"
    limit = 0
    if not config_path.is_file():
        errors.add("missing_project", config_path, "project.json not found")
    else:
        config = _load(config_path, errors)
        if config is not None:
            if (type(config) is not dict or set(config) != {"schema", "version", "default_budget"}
                    or config["schema"] != "councilflow-project" or config["version"] != "1.0"
                    or not _int(config["default_budget"]) or config["default_budget"] < 0):
                errors.add("bad_schema", config_path, "expected councilflow-project 1.0 with default_budget >= 0")
            else:
                limit = config["default_budget"]
    sources, bad_sources = _check_sources(project, errors)
    evidence_dir = project / "evidence"
    evidence_names = {p.stem for p in evidence_dir.glob("E*.json")} if evidence_dir.is_dir() else set()
    ledger_ids, latest = _check_ledgers(project, sources, bad_sources, evidence_names, errors)
    _check_plan(project, ledger_ids, errors)
    _check_evidence(project, ledger_ids, errors)
    _check_retests(project, ledger_ids, errors)
    _check_audits(project, ledger_ids, errors)
    if latest:
        used = sum(1 for e in latest[1] if e["type"] == "Assumption" and e["status"] == "unconfirmed")
        extra["ledger_version"] = latest[0]
        extra["budget"] = {"limit": limit, "used": used, "exceeded": used > limit}
    else:
        extra["budget"]["limit"] = limit
    return errors, extra


def _version_entries(project, number, errors):
    path = project / "ledger" / f"L{number:04d}.json"
    if not path.is_file():
        errors.add("bad_input", path, f"ledger version {number} does not exist")
        return None
    data = _load(path, errors)
    return {e["id"]: e for e in data["entries"]}


def affected(project, to_version, from_version):
    errors, extra = validate(project)
    if errors:
        return errors, extra
    if from_version is None:
        from_version = to_version - 1
    if from_version >= to_version:
        errors.add("bad_input", "--from-version", "from-version must be lower than to-version")
        return errors, {}
    old = _version_entries(project, from_version, errors)
    new = _version_entries(project, to_version, errors)
    if errors:
        return errors, {}
    added = [e for i, e in new.items() if i not in old]
    changed = {e["id"] for e in added} | {
        i for i, e in new.items() if i in old and e["status"] != old[i]["status"]}
    touched = changed | {s for e in added for s in e["supersedes"]}
    out = {"from_version": from_version, "to_version": to_version,
           "changed_entry_ids": sorted(changed), "affected_slices": [],
           "unaffected_slices": [], "closed_affected": []}
    plan_path = project / "plan.json"
    plan = _load(plan_path, errors) if plan_path.exists() else {"slices": []}
    for item in plan["slices"]:
        hit = item["ledger_version"] < to_version and bool(touched & set(item["ledger_ids"]))
        if item["status"] in ("DONE", "CANCELLED"):
            if hit:
                out["closed_affected"].append(item["slice_id"])
        else:
            out["affected_slices" if hit else "unaffected_slices"].append(item["slice_id"])
    for key in ("affected_slices", "unaffected_slices", "closed_affected"):
        out[key].sort()
    return errors, out


def _retest_passed(project, to_version):
    """Slice ids with a recorded tester pass pinned to to_version."""
    scratch = Errors()
    passed = set()
    for path in _numbered(project / "retest", RETEST_RE, ".json", scratch, "retest").values():
        record = _load(path, scratch)
        if type(record) is dict and record.get("result") == "pass" and record.get("ledger_version") == to_version:
            passed.add(record.get("slice_id"))
    return passed


def _retest_failed(project, to_version):
    """Slice ids with a recorded tester fail pinned to to_version (these were auto-paused)."""
    scratch = Errors()
    failed = set()
    for path in _numbered(project / "retest", RETEST_RE, ".json", scratch, "retest").values():
        record = _load(path, scratch)
        if type(record) is dict and record.get("result") == "fail" and record.get("ledger_version") == to_version:
            failed.add(record.get("slice_id"))
    return failed


def retest_select(project, to_version, from_version):
    """Slices the Tester must still re-check for to_version (M5): closed-but-affected slices,
    plus slices whose retest failed for to_version, until a pass for that version is recorded."""
    errors, out = affected(project, to_version, from_version)
    if errors:
        return errors, {}
    passed = _retest_passed(project, to_version)
    candidates = sorted(set(out["closed_affected"]) | _retest_failed(project, to_version))
    return errors, {"from_version": out["from_version"], "to_version": to_version,
                    "retest": [s for s in candidates if s not in passed],
                    "already_passed": [s for s in candidates if s in passed]}


def retest_record(project, slice_id, to_version, from_version, result, finding, artifacts, oracle,
                  routing, contradiction, consequence, created_at):
    """Record one Tester retest. Writes evidence/ and retest/; the ledger is never touched.

    A pass carries no reopen request and leaves plan.json alone; the Manager re-pins the slice.
    A fail carries a submitted reopen request for the Manager to forward unchanged to the Planner,
    and auto-pauses the slice: plan.json changes only that slice's status, to PAUSED (ADR-001 M5,
    Owner decision). Readiness and the re-pin remain with the Planner and Manager.
    """
    errors = Errors()
    if not _timestamp_ok(created_at):
        errors.add("bad_timestamp", "--created-at", "must be ISO-8601 UTC ending in Z or +00:00")
    if result not in RETEST_RESULTS:
        errors.add("bad_value", "--result", "must be pass or fail")
    if type(finding) is not str or not finding.strip():
        errors.add("bad_value", "--finding", "must be nonempty")
    if result == "fail" and not ((contradiction or "").strip() and (consequence or "").strip()):
        errors.add("bad_value", "--contradiction/--consequence", "a fail needs both")
    if result == "pass" and (contradiction or consequence):
        errors.add("bad_value", "--contradiction/--consequence", "a pass carries no reopen request")
    if not artifacts:
        errors.add("bad_value", "--artifact", "at least one artifact is required")
    if errors:
        return errors, {}
    current, _ = validate(project)
    if current:
        return current, {}
    selection_errors, selection = retest_select(project, to_version, from_version)
    if selection_errors:
        return selection_errors, {}
    if slice_id not in selection["retest"]:
        errors.add("not_retestable", "--slice", f"{slice_id!r} is not a closed-but-affected slice "
                   f"awaiting retest for ledger version {to_version}")
        return errors, {}
    plan = _load(project / "plan.json", errors)
    if plan is None:
        return errors, {}
    item = next(s for s in plan["slices"] if s["slice_id"] == slice_id)

    def fingerprint(text, label):
        path = Path(text)
        if not path.is_file():
            errors.add("bad_input", label, f"{text} is not a file")
            return None
        return {"path": text, "sha256": _sha(path.read_bytes())}

    records = [fingerprint(a, "--artifact") for a in artifacts]
    oracle_record = fingerprint(oracle, "--oracle")
    tester = {"hint": routing["hint"], "used": routing["used"],
              "source": routing["source"], "reason": routing["reason"]}
    _check_routing({"tester": tester}, "--route", errors)
    if errors or oracle_record is None or None in records:
        return errors, {}
    evidence_id = f"E{max(_numbered(project / 'evidence', EVIDENCE_RE, '.json', Errors(), 'evidence'), default=0) + 1:04d}"
    retest_id = f"T{max(_numbered(project / 'retest', RETEST_RE, '.json', Errors(), 'retest'), default=0) + 1:04d}"
    reopen = None if result == "pass" else {"status": "submitted", "contradiction": contradiction.strip(),
                                            "consequence": consequence.strip()}
    evidence = {"evidence_id": evidence_id, "source_agent": "tester", "finding": finding.strip(),
                "artifacts": records, "ledger_ids": list(item["ledger_ids"]),
                "affected_slices": [slice_id], "created_at": created_at, "reopen_request": reopen}
    retest = {"retest_id": retest_id, "slice_id": slice_id, "ledger_version": to_version,
              "ledger_ids": list(item["ledger_ids"]), "result": result, "evidence_id": evidence_id,
              "oracle": oracle_record, "model_routing": {"tester": tester}, "created_at": created_at}
    problem = _create(project / "evidence" / f"{evidence_id}.json", _dump(evidence))
    if problem:
        return [problem], {}
    problem = _create(project / "retest" / f"{retest_id}.json", _dump(retest))
    if problem:
        return [problem], {}
    if result == "fail":
        plan["slices"] = [dict(s, status="PAUSED") if s["slice_id"] == slice_id else s
                          for s in plan["slices"]]
        (project / "plan.json").write_bytes(_dump(plan))
    final, _ = validate(project)
    if final:
        return final, {}
    return [], {"evidence_id": evidence_id, "ledger_version": to_version, "result": result,
                "retest_id": retest_id, "slice_id": slice_id}


def _audit_records(project):
    scratch = Errors()
    records = {}
    for path in _numbered(project / "audit", AUDIT_RE, ".json", scratch, "audit").values():
        record = _load(path, scratch)
        if type(record) is dict:
            records[path.stem] = record
    return records


def audit_select(project, to_version):
    """Whether the Technical Audit may run for ledger version M (M6). Read-only.

    M must be the current (latest) ledger version and hold an active Goal. The Goal version is the
    highest version_introduced among the active Goal entries. Verified means: at least one slice is
    DONE, every slice that is not CANCELLED is DONE, and no slice waits in the Tester retest list of
    any ledger version from 2 to M. One audit per Goal version: `audited` names an existing one.
    """
    errors, extra = validate(project)
    if errors:
        return errors, {}
    latest = extra["ledger_version"]
    if latest is None or to_version != latest:
        errors.add("stale_ledger_version", "--to-version",
                   f"the audit pins the current ledger version ({latest}), not {to_version}")
        return errors, {}
    entries = _version_entries(project, to_version, errors)
    if errors:
        return errors, {}
    goals = sorted(i for i, e in entries.items() if e["type"] == "Goal" and e["status"] == "active")
    if not goals:
        errors.add("no_goal", "--to-version", f"ledger version {to_version} has no active Goal entry")
        return errors, {}
    goal_version = max(entries[g]["version_introduced"] for g in goals)
    plan_path = project / "plan.json"
    slices = _load(plan_path, errors)["slices"] if plan_path.exists() else []
    unverified = [{"slice_id": s["slice_id"], "reason": f"status {s['status']}"}
                  for s in slices if s["status"] not in ("DONE", "CANCELLED")]
    pending = {}
    for version in range(2, to_version + 1):
        selection_errors, selection = retest_select(project, version, None)
        if selection_errors:
            return selection_errors, {}
        for sid in selection["retest"]:
            pending.setdefault(sid, version)
    unverified += [{"slice_id": sid, "reason": f"awaiting Tester retest for ledger version {version}"}
                   for sid, version in sorted(pending.items())]
    done = sorted(s["slice_id"] for s in slices if s["status"] == "DONE")
    if not done:
        unverified.append({"slice_id": None, "reason": "no DONE slice to audit"})
    unverified.sort(key=lambda u: (u["slice_id"] or "", u["reason"]))
    audit_id = next((aid for aid, rec in sorted(_audit_records(project).items())
                     if rec.get("goal_version") == goal_version), None)
    return errors, {"ledger_version": to_version, "goal_ids": goals, "goal_version": goal_version,
                    "verified": not unverified, "unverified": unverified, "slices": done,
                    "audited": audit_id is not None, "audit_id": audit_id}


def _finding_input(item, where, entries, done, errors):
    """Check one Reviewer finding from --findings; returns True when usable."""
    if type(item) is not dict or not {"ledger_id", "verdict", "finding", "route"} <= set(item) <= FINDING_INPUT:
        errors.add("bad_findings", where, f"a finding needs ledger_id, verdict, finding and route, "
                   f"and may hold only {sorted(FINDING_INPUT)}")
        return False
    ok = True
    ledger_id = item["ledger_id"]
    if type(ledger_id) is not str or ledger_id not in entries or entries[ledger_id]["status"] == "superseded":
        errors.add("audit_ledger_ref", where, f"{ledger_id!r} is not a current entry of the pinned ledger version")
        ok = False
    if item["verdict"] not in VERDICTS:
        errors.add("audit_verdict", where, "verdict must be gap, risk or pass")
        ok = False
    if type(item["finding"]) is not str or not item["finding"].strip():
        errors.add("bad_value", where, "finding must be nonempty")
        ok = False
    route = item["route"]
    slices = item.get("affected_slices", [])
    if route not in AUDIT_ROUTES:
        errors.add("audit_route", where, f"route must be one of {list(AUDIT_ROUTES)}")
        return False
    if item["verdict"] == "pass" and route != "none":
        errors.add("audit_route", where, "a pass carries no reopen request and no pause")
        ok = False
    if not _str_list(slices) or any(s not in done for s in slices) or len(set(slices)) != len(slices):
        errors.add("audit_slice_unknown", where, "affected_slices must be distinct DONE slices of the plan")
        ok = False
    elif route != "none" and not slices:
        errors.add("audit_route", where, f"route {route} needs affected_slices")
        ok = False
    reopen = ("contradiction", "consequence")
    if route == "reopen":
        if any(type(item.get(k)) is not str or not item[k].strip() for k in reopen):
            errors.add("audit_route", where, "route reopen needs contradiction and consequence")
            ok = False
    elif any(k in item for k in reopen):
        errors.add("audit_route", where, "only route reopen carries contradiction and consequence")
        ok = False
    if route == "owner_decision":
        if item.get("decision_class") not in OWNER_CLASSES:
            errors.add("audit_route", where, f"route owner_decision needs decision_class in {list(OWNER_CLASSES)}")
            ok = False
    elif "decision_class" in item:
        errors.add("audit_route", where, "only route owner_decision carries decision_class")
        ok = False
    if "evidence" in item and not _str_list(item["evidence"]):
        errors.add("bad_findings", where, "evidence must be a list of file paths")
        ok = False
    return ok


def audit_record(project, to_version, findings_file, artifacts, rerun_file, routing, created_at):
    """Record the Technical Audit for the current Goal version (ADR-001 M6). Advisory only.

    Writes one reviewer evidence record per verdict and audit/A####.json. The ledger is never
    touched. A reopen finding carries a submitted reopen request for the Manager to forward
    unchanged to the Planner. An owner_decision finding sets the status of the slices it names to
    PAUSED (nothing else in plan.json changes) for the Manager to present to the Owner. A pass or an
    ordinary engineering finding (route none) changes nothing outside evidence/ and audit/.
    Delivery stays with the Manager presenting to the Owner; the output carries no delivery flag.
    """
    errors = Errors()
    if not _timestamp_ok(created_at):
        errors.add("bad_timestamp", "--created-at", "must be ISO-8601 UTC ending in Z or +00:00")
    if not artifacts:
        errors.add("bad_value", "--artifact", "at least one artifact is required")
    findings = _load(Path(findings_file), errors)
    rerun_in = _load(Path(rerun_file), errors)
    if errors:
        return errors, {}
    current, _ = validate(project)
    if current:
        return current, {}
    selection_errors, selection = audit_select(project, to_version)
    if selection_errors:
        return selection_errors, {}
    if not selection["verified"]:
        errors.add("not_verified", "--to-version", f"slices are not all verified for ledger version "
                   f"{to_version}: {selection['unverified']}")
        return errors, {}
    if selection["audited"]:
        errors.add("already_audited", "--to-version", f"Goal version {selection['goal_version']} was "
                   f"already audited in {selection['audit_id']}")
        return errors, {}
    entries = _version_entries(project, to_version, errors)
    done = set(selection["slices"])
    if type(findings) is not list or not findings:
        errors.add("bad_findings", findings_file, "expected a nonempty JSON array of findings")
        return errors, {}
    usable = [_finding_input(item, f"{findings_file}#[{i}]", entries, done, errors)
              for i, item in enumerate(findings)]
    if not all(usable):
        return errors, {}
    ids = [f["ledger_id"] for f in findings]
    if len(set(ids)) != len(ids):
        errors.add("audit_duplicate", findings_file, "one verdict per ledger id")
    missing = sorted(set(selection["goal_ids"]) - set(ids))
    if missing:
        errors.add("audit_goal_missing", findings_file, f"no verdict for Goal entries {missing}")
    reviewer = {"hint": routing["hint"], "used": routing["used"],
                "source": routing["source"], "reason": routing["reason"]}
    _check_routing({"reviewer": reviewer}, "--route", errors)

    def fingerprint(text, label):
        path = Path(text) if type(text) is str else None
        if path is None or not path.is_file():
            errors.add("bad_input", label, f"{text} is not a file")
            return None
        return {"path": text, "sha256": _sha(path.read_bytes())}

    if type(rerun_in) is not dict or set(rerun_in) != RERUN_INPUT:
        errors.add("audit_rerun_required", rerun_file,
                   f"the independent rerun needs exactly {sorted(RERUN_INPUT)}")
        return errors, {}
    rerun = dict(rerun_in, tester_evidence=fingerprint(rerun_in["tester_evidence"], "--rerun tester_evidence"),
                 output=fingerprint(rerun_in["output"], "--rerun output"))
    if errors:
        return errors, {}
    equal = (rerun["exit_code"] == rerun["tester_exit_code"]
             and rerun["stdout_sha256"] == rerun["tester_stdout_sha256"])
    rerun["status"] = "MATCH" if equal else "MISMATCH"
    if _check_rerun(rerun, "--rerun", errors) is None:
        return errors, {}
    if rerun["stdout_sha256"] != _normalized_sha(Path(rerun_in["output"]).read_bytes()):
        errors.add("audit_rerun_hash", "--rerun output", "stdout_sha256 must be the CRLF-to-LF normalized "
                   "SHA-256 of the captured output file")
    if rerun["status"] == "MISMATCH" and all(f["verdict"] == "pass" for f in findings):
        errors.add("audit_contradiction", findings_file, "a mismatching rerun needs at least one gap or risk")
    shared = [fingerprint(a, "--artifact") for a in artifacts]
    extra_evidence = [[fingerprint(p, f"{findings_file}#evidence") for p in f.get("evidence", [])]
                      for f in findings]
    if errors:
        return errors, {}
    plan = _load(project / "plan.json", errors)
    if plan is None:
        return errors, {}
    first = max(_numbered(project / "evidence", EVIDENCE_RE, ".json", Errors(), "evidence"), default=0) + 1
    audit_id = f"A{max(_numbered(project / 'audit', AUDIT_RE, '.json', Errors(), 'audit'), default=0) + 1:04d}"
    evidence_records, verdicts, paused = [], [], set()
    for offset, item in enumerate(findings):
        evidence_id = f"E{first + offset:04d}"
        route, slices = item["route"], sorted(item.get("affected_slices", []))
        reopen = None
        if route == "reopen":
            reopen = {"status": "submitted", "contradiction": item["contradiction"].strip(),
                      "consequence": item["consequence"].strip()}
        if route == "owner_decision":
            paused.update(slices)
        evidence_records.append((evidence_id, {
            "evidence_id": evidence_id, "source_agent": "reviewer", "finding": item["finding"].strip(),
            "artifacts": shared + extra_evidence[offset], "ledger_ids": [item["ledger_id"]],
            "affected_slices": slices, "created_at": created_at, "reopen_request": reopen}))
        verdicts.append({"ledger_id": item["ledger_id"], "verdict": item["verdict"],
                         "finding": item["finding"].strip(), "route": route,
                         "decision_class": item.get("decision_class"), "affected_slices": slices,
                         "evidence_id": evidence_id})
    audit = {"audit_id": audit_id, "ledger_version": to_version, "goal_ids": selection["goal_ids"],
             "goal_version": selection["goal_version"], "verdicts": verdicts, "independent_rerun": rerun,
             "artifacts": shared, "model_routing": {"reviewer": reviewer},
             "paused_slices": sorted(paused), "created_at": created_at}
    for evidence_id, record in evidence_records:
        problem = _create(project / "evidence" / f"{evidence_id}.json", _dump(record))
        if problem:
            return [problem], {}
    problem = _create(project / "audit" / f"{audit_id}.json", _dump(audit))
    if problem:
        return [problem], {}
    if paused:
        plan["slices"] = [dict(s, status="PAUSED") if s["slice_id"] in paused else s for s in plan["slices"]]
        (project / "plan.json").write_bytes(_dump(plan))
    final, _ = validate(project)
    if final:
        return final, {}
    return [], {"audit_id": audit_id, "ledger_version": to_version, "goal_version": selection["goal_version"],
                "evidence_ids": [e for e, _ in evidence_records],
                "reopen_evidence_ids": [v["evidence_id"] for v in verdicts if v["route"] == "reopen"],
                "owner_decisions": [{"ledger_id": v["ledger_id"], "decision_class": v["decision_class"],
                                     "affected_slices": v["affected_slices"], "evidence_id": v["evidence_id"]}
                                    for v in verdicts if v["route"] == "owner_decision"],
                "paused_slices": sorted(paused), "rerun_status": rerun["status"]}


def init(project, budget):
    if budget < 0:
        return [{"code": "usage", "path": "--budget", "detail": "must be >= 0"}], {}
    data = _dump({"schema": "councilflow-project", "version": "1.0", "default_budget": budget})
    problem = _create(project / "project.json", data)
    return ([problem] if problem else []), {}


def source_add(project, file, received_at, kind):
    errors = Errors()
    if not (project / "project.json").is_file():
        errors.add("missing_project", project / "project.json", "run init first")
    if not _timestamp_ok(received_at):
        errors.add("bad_timestamp", "--received-at", "must be ISO-8601 UTC ending in Z or +00:00")
    if type(kind) is not str or not kind.strip():
        errors.add("bad_value", "--kind", "must be nonempty")
    try:
        raw = Path(file).read_bytes()
    except OSError as exc:
        errors.add("bad_input", file, str(exc))
    if errors:
        return errors, {}
    directory = project / "sources"
    existing = [int(m.group(1)) for p in directory.glob("S*.txt")
                if (m := SOURCE_RE.match(p.stem))] if directory.is_dir() else []
    sid = f"S{max(existing, default=0) + 1:04d}"
    record = {"source_id": sid, "kind": kind, "received_at": received_at,
              "path": sid + ".txt", "sha256": _sha(raw)}
    problem = _create(directory / (sid + ".txt"), raw) or _create(directory / (sid + ".json"), _dump(record))
    return ([problem] if problem else []), {"source_id": sid}


def bootstrap(project, criteria_file, source_id, goal, created_at):
    errors = Errors()
    if not (project / "project.json").is_file():
        errors.add("missing_project", project / "project.json", "run init first")
    if not _timestamp_ok(created_at):
        errors.add("bad_timestamp", "--created-at", "must be ISO-8601 UTC ending in Z or +00:00")
    if any((project / "ledger").glob("L*.json")) if (project / "ledger").is_dir() else False:
        errors.add("exists", project / "ledger", "a ledger already exists")
    if not (project / "sources" / f"{source_id}.json").is_file():
        errors.add("source_missing", source_id, "source does not exist")
    criteria = _load(Path(criteria_file), errors)
    if criteria is not None and (type(criteria) is not list or not criteria or any(
            type(c) is not dict or type(c.get("id")) is not str or not c["id"].strip()
            or type(c.get("criterion")) is not str or not c["criterion"].strip() for c in criteria)):
        errors.add("bad_criteria", criteria_file, "expected nonempty array of {id, criterion}")
        criteria = None
    if criteria is not None and len({c["id"] for c in criteria}) != len(criteria):
        errors.add("entry_duplicate_id", criteria_file, "duplicate criterion id")
    if goal is not None and (not goal.strip() or any(c["id"] == "G1" for c in criteria or [])):
        errors.add("bad_value", "--goal", "goal must be nonempty and G1 must not collide")
    if errors:
        return errors, {}

    def entry(eid, kind, content):
        return {"id": eid, "type": kind, "content": content, "source_ids": [source_id],
                "evidence_ids": [], "status": "active", "created_at": created_at,
                "version_introduced": 1, "supersedes": [], "affected_slices": []}

    entries = ([entry("G1", "Goal", goal)] if goal is not None else [])
    entries += [entry(c["id"], "Requirement", c["criterion"]) for c in criteria]
    ledger = {"schema": "councilflow-ledger", "version": "1.0", "ledger_version": 1,
              "previous_sha256": None, "created_at": created_at, "entries": entries}
    problem = _create(project / "ledger" / "L0001.json", _dump(ledger))
    return ([problem] if problem else []), {"ledger_version": 1}


def _report(errors, extra):
    out = dict(extra)
    out["status"] = "FAIL" if errors else "PASS"
    out["errors"] = list(errors)
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "source-add", "bootstrap", "validate", "affected", "retest-select", "retest-record",
                 "audit-select", "audit-record"):
        p = sub.add_parser(name)
        p.add_argument("--project", required=True)
        if name == "init":
            p.add_argument("--budget", type=int, default=5)
        if name in ("affected", "retest-select", "retest-record"):
            p.add_argument("--to-version", type=int, required=True)
            p.add_argument("--from-version", type=int)
        if name in ("audit-select", "audit-record"):
            p.add_argument("--to-version", type=int, required=True)
        if name == "audit-record":
            p.add_argument("--findings", required=True, help="JSON array of per-ledger-id findings")
            p.add_argument("--rerun", required=True, help="JSON object: the independent rerun of one "
                           "Tester-declared deterministic command")
            p.add_argument("--artifact", action="append", default=[], required=True)
            p.add_argument("--route-used", required=True)
            p.add_argument("--route-source", required=True, choices=("hint", "role_default", "host"))
            p.add_argument("--route-hint")
            p.add_argument("--route-reason", required=True)
            p.add_argument("--created-at", required=True)
        if name == "retest-record":
            p.add_argument("--slice", required=True)
            p.add_argument("--result", required=True, choices=RETEST_RESULTS)
            p.add_argument("--finding", required=True)
            p.add_argument("--artifact", action="append", default=[], required=True)
            p.add_argument("--oracle", required=True, help="the acceptance checks the Manager assigned")
            p.add_argument("--route-used", required=True)
            p.add_argument("--route-source", required=True, choices=("hint", "role_default", "host"))
            p.add_argument("--route-hint")
            p.add_argument("--route-reason", required=True)
            p.add_argument("--contradiction")
            p.add_argument("--consequence")
            p.add_argument("--created-at", required=True)
        if name == "source-add":
            p.add_argument("--file", required=True)
            p.add_argument("--received-at", required=True)
            p.add_argument("--kind", default="owner_message")
        if name == "bootstrap":
            p.add_argument("--criteria", required=True)
            p.add_argument("--source-id", required=True)
            p.add_argument("--goal")
            p.add_argument("--created-at", required=True)
    args = parser.parse_args(argv)
    project = Path(args.project)
    if args.command == "init":
        errors, extra = init(project, args.budget)
    elif args.command == "source-add":
        errors, extra = source_add(project, args.file, args.received_at, args.kind)
    elif args.command == "bootstrap":
        errors, extra = bootstrap(project, args.criteria, args.source_id, args.goal, args.created_at)
    elif args.command == "affected":
        errors, extra = affected(project, args.to_version, args.from_version)
    elif args.command == "retest-select":
        errors, extra = retest_select(project, args.to_version, args.from_version)
    elif args.command == "retest-record":
        routing = {"hint": args.route_hint, "used": args.route_used,
                   "source": args.route_source, "reason": args.route_reason}
        errors, extra = retest_record(project, args.slice, args.to_version, args.from_version, args.result,
                                      args.finding, args.artifact, args.oracle, routing,
                                      args.contradiction, args.consequence, args.created_at)
    elif args.command == "audit-select":
        errors, extra = audit_select(project, args.to_version)
    elif args.command == "audit-record":
        routing = {"hint": args.route_hint, "used": args.route_used,
                   "source": args.route_source, "reason": args.route_reason}
        errors, extra = audit_record(project, args.to_version, args.findings, args.artifact, args.rerun,
                                     routing, args.created_at)
    else:
        errors, extra = validate(project)
    if errors and errors[0]["code"] == "usage":
        parser.error(errors[0]["detail"])
    return _report(errors, extra)


if __name__ == "__main__":
    sys.exit(main())
