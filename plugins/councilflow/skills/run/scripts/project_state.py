"""Plain-file project state for CouncilFlow (ADR-001 section 3).

Commands: init, source-add, bootstrap, validate, affected (read-only), retest-select (read-only),
retest-record (writes evidence/ and retest/ only; ADR-001 M5). Every command prints one JSON
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


def retest_select(project, to_version, from_version):
    """Closed-but-affected slices the Tester must still re-check for to_version (M5)."""
    errors, out = affected(project, to_version, from_version)
    if errors:
        return errors, {}
    passed = _retest_passed(project, to_version)
    return errors, {"from_version": out["from_version"], "to_version": to_version,
                    "retest": [s for s in out["closed_affected"] if s not in passed],
                    "already_passed": [s for s in out["closed_affected"] if s in passed]}


def retest_record(project, slice_id, to_version, from_version, result, finding, artifacts, oracle,
                  routing, contradiction, consequence, created_at):
    """Record one Tester retest. Writes only evidence/ and retest/; never plan.json or the ledger.

    A pass carries no reopen request and leaves the slice's pin to the Manager. A fail carries a
    submitted reopen request for the Manager to forward unchanged to the Planner; nothing reopens
    automatically.
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
    final, _ = validate(project)
    if final:
        return final, {}
    return [], {"evidence_id": evidence_id, "ledger_version": to_version, "result": result,
                "retest_id": retest_id, "slice_id": slice_id}


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
    for name in ("init", "source-add", "bootstrap", "validate", "affected", "retest-select", "retest-record"):
        p = sub.add_parser(name)
        p.add_argument("--project", required=True)
        if name == "init":
            p.add_argument("--budget", type=int, default=5)
        if name in ("affected", "retest-select", "retest-record"):
            p.add_argument("--to-version", type=int, required=True)
            p.add_argument("--from-version", type=int)
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
    else:
        errors, extra = validate(project)
    if errors and errors[0]["code"] == "usage":
        parser.error(errors[0]["detail"])
    return _report(errors, extra)


if __name__ == "__main__":
    sys.exit(main())
