"""Generate the read-only Owner view of a CouncilFlow project (ADR-001 section 4, M7).

Commands: generate (writes one static JSON file), status (read-only freshness check).
Every command prints one JSON object (`status` PASS or FAIL, `errors`, sorted keys) and
exits 0 on PASS, 1 on FAIL and 2 on a usage error.

The view is a derived copy. The ledger stays the source of truth: this module never
writes the ledger, the plan, evidence, retests, audits or sources, and it has no way to
record an Owner decision. The Owner answers a pending question through the Manager. It
only ever writes its own output file, which must be the project's `owner-view.json` or a
path outside the project, and which may only replace an earlier Owner view.

A view records the ledger version it was built from. It becomes stale when a newer
ledger version exists; `status` and the dashboard publisher report that, and the view
file itself is never edited to say so.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
sys.dont_write_bytecode = True

import project_state  # noqa: E402
import strict_json  # noqa: E402

SCHEMA = "councilflow-owner-view"
VERSION = "1.0"
VIEW_NAME = "owner-view.json"
MAX_VIEW_BYTES = 1048576
# Everything below is authoritative state; the view is never written into it.
PROTECTED_DIRS = ("ledger", "sources", "evidence", "retest", "audit", "questions")
PROTECTED_FILES = ("plan.json", "project.json")
VIEW_FIELDS = {"schema", "version", "read_only", "authoritative_source", "generated_at",
               "ledger_version", "ledger_sha256", "goal", "confirmed_requirements",
               "provisional_assumptions", "open_questions", "decision_history", "slices",
               "qa_results", "audit_findings", "default_budget", "notes"}
NOTES = [
    "This view is generated and read-only. The ledger is the source of truth.",
    "Answer pending questions through the Manager. This view records no Owner decision.",
    "QA results are Tester retest records held in project state; per-run acceptance results "
    "stay in the run dashboard.",
]


def _dump(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _ledger_numbers(project):
    """Ledger version numbers present, from file names only."""
    directory = project / "ledger"
    found = []
    if directory.is_dir():
        for item in directory.iterdir():
            match = project_state.LEDGER_RE.match(item.name)
            if item.is_file() and match:
                found.append(int(match.group(1)))
    return sorted(found)


def latest_ledger_version(project):
    numbers = _ledger_numbers(Path(project))
    return numbers[-1] if numbers else None


def _read_json(path):
    return strict_json.loads(path.read_bytes().decode("utf-8"), str(path))


def _slice_view(item, latest):
    return {"slice_id": item["slice_id"], "readiness": item["readiness"], "status": item["status"],
            "ledger_version": item["ledger_version"], "ledger_ids": list(item["ledger_ids"]),
            "depends_on": list(item["depends_on"]),
            "pinned_to_older_ledger": item["ledger_version"] < latest}


def _questions(project, open_entries, warnings):
    """Pending questions: exact stored wording, plus the stored packet's default if any.

    Wording is the Open entry's content, byte for byte. A packet under questions/ named
    for the same ID adds the permitted default and classification; nothing is rewritten.
    """
    packets = {}
    directory = project / "questions"
    if directory.is_dir():
        import planner_contract
        for path in sorted(directory.glob("*.json")):
            try:
                packet = _read_json(path)
                planner_contract.validate_question(packet, path.name)
                packets[packet["question_id"]] = packet
            except (ValueError, OSError, KeyError, TypeError) as exc:
                warnings.append(f"questions/{path.name} was not used: {exc}")
    out = []
    for entry in open_entries:
        packet = packets.pop(entry["id"], None)
        out.append({
            "id": entry["id"], "wording": entry["content"], "status": entry["status"],
            "source_ids": list(entry["source_ids"]), "evidence_ids": list(entry["evidence_ids"]),
            "version_introduced": entry["version_introduced"],
            "affected_slices": list(packet["affected_slices"] if packet else entry["affected_slices"]),
            "default": packet["permitted_default"] if packet else None,
            "default_stored": packet is not None,
            "blocking": packet["blocking"] if packet else None,
            "reversibility": packet["decision_class"] if packet else None,
            "reason": packet["reason"] if packet else None,
            "packet_wording_matches": (packet["text"] == entry["content"]) if packet else None,
        })
    for question_id in sorted(packets):
        warnings.append(f"questions/{question_id}.json matches no open ledger entry and was not shown")
    return out


def build(project, generated_at=None):
    """Return (errors, view). Read-only; nothing is written."""
    project = Path(project)
    errors, extra = project_state.validate(project)
    if errors:
        return errors, {}
    latest = extra["ledger_version"]
    if latest is None:
        errors.add("no_ledger", project / "ledger", "the project has no ledger version yet")
        return errors, {}
    ledger_path = project / "ledger" / f"L{latest:04d}.json"
    ledger_bytes = ledger_path.read_bytes()
    entries = json.loads(ledger_bytes.decode("utf-8"))["entries"]
    warnings = []

    def pick(kind, status):
        return [e for e in entries if e["type"] == kind and e["status"] == status]

    def plain(entry):
        return {"id": entry["id"], "content": entry["content"], "status": entry["status"],
                "source_ids": list(entry["source_ids"]), "evidence_ids": list(entry["evidence_ids"]),
                "version_introduced": entry["version_introduced"], "created_at": entry["created_at"],
                "supersedes": list(entry["supersedes"])}

    goals = pick("Goal", "active")
    plan_path = project / "plan.json"
    slices = [_slice_view(s, latest) for s in _read_json(plan_path)["slices"]] if plan_path.is_file() else []

    qa = []
    retest_dir = project / "retest"
    for path in sorted(retest_dir.glob("T*.json")) if retest_dir.is_dir() else []:
        r = _read_json(path)
        qa.append({"retest_id": r["retest_id"], "slice_id": r["slice_id"], "result": r["result"],
                   "ledger_version": r["ledger_version"], "ledger_ids": list(r["ledger_ids"]),
                   "evidence_id": r["evidence_id"], "created_at": r["created_at"],
                   "stale": r["ledger_version"] < latest})

    findings = []
    audit_dir = project / "audit"
    for path in sorted(audit_dir.glob("A*.json")) if audit_dir.is_dir() else []:
        a = _read_json(path)
        for item in a["entries"]:
            findings.append({"audit_id": a["audit_id"], "ledger_version": a["ledger_version"],
                             "ledger_id": item["ledger_id"], "verdict": item["verdict"],
                             "kind": item["kind"], "finding": item["finding"],
                             "slice_ids": list(item["slice_ids"]), "consequence": item["consequence"],
                             "evidence_id": item["evidence_id"], "created_at": a["created_at"],
                             "owner_decision_needed": item["kind"] == "owner_choice",
                             "stale": a["ledger_version"] < latest})

    budget = extra["budget"]
    view = {
        "schema": SCHEMA, "version": VERSION, "read_only": True, "authoritative_source": "ledger",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ledger_version": latest, "ledger_sha256": _sha(ledger_bytes),
        "goal": plain(goals[-1]) if goals else None,
        "confirmed_requirements": [plain(e) for e in pick("Requirement", "active")],
        "provisional_assumptions": [plain(e) for e in pick("Assumption", "unconfirmed")],
        "open_questions": _questions(project, pick("Open", "open"), warnings),
        "decision_history": [plain(e) for e in entries if e["type"] == "Decision"],
        "slices": slices, "qa_results": qa, "audit_findings": findings,
        "default_budget": {"limit": budget["limit"], "used": budget["used"],
                           "remaining": max(budget["limit"] - budget["used"], 0),
                           "exceeded": budget["exceeded"]},
        "notes": NOTES + warnings,
    }
    return errors, view


def check_output(project, output):
    """Return an error list: where the view may be written. Refuses anything authoritative."""
    errors = project_state.Errors()
    project, output = Path(project).resolve(), Path(output)
    if output.is_symlink():
        errors.add("write_refused", output, "the output path is a link")
        return errors
    target = output.resolve()
    if target.suffix != ".json":
        errors.add("write_refused", output, "the Owner view is a .json file")
    if target.is_dir():
        errors.add("write_refused", output, "the output path is a directory")
    if target == project or project in target.parents:
        relative = target.relative_to(project).parts if target != project else ()
        if relative != (VIEW_NAME,):
            errors.add("write_refused", output,
                       f"inside the project the view may only be written to {VIEW_NAME}; "
                       "ledger, plan, sources, evidence, retests, audits and questions are read-only here")
    if target.is_file() and not errors:
        try:
            held = _read_json(target)
        except (ValueError, OSError):
            held = None
        if type(held) is not dict or held.get("schema") != SCHEMA:
            errors.add("write_refused", output, "the file exists and is not an Owner view; refusing to replace it")
    return errors


def generate(project, output=None, generated_at=None):
    project = Path(project)
    output = Path(output) if output is not None else project / VIEW_NAME
    errors = check_output(project, output)
    if errors:
        return errors, {}
    errors, view = build(project, generated_at)
    if errors:
        return errors, {}
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".owner-view-", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_dump(view))
        Path(temporary).replace(output)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()
    return [], {"output": str(output), "ledger_version": view["ledger_version"]}


def read_view(path):
    """Load and shape-check a generated view; raises ValueError if it is not one."""
    raw = Path(path).read_bytes()
    if len(raw) > MAX_VIEW_BYTES:
        raise ValueError(f"the Owner view exceeds {MAX_VIEW_BYTES} bytes")
    view = strict_json.loads(raw.decode("utf-8"), str(path))
    if (type(view) is not dict or set(view) != VIEW_FIELDS or view["schema"] != SCHEMA
            or view["version"] != VERSION or view["read_only"] is not True
            or type(view["ledger_version"]) is not int):
        raise ValueError("not a CouncilFlow Owner view 1.0")
    return view


def freshness(project, view, check_hash=True):
    """Compare a view with the project's newest ledger. Reads file names, and one file's bytes if hashing."""
    project = Path(project)
    latest = latest_ledger_version(project)
    stale = latest is None or latest != view["ledger_version"]
    reason = None
    if latest is None:
        reason = "the project has no ledger"
    elif latest > view["ledger_version"]:
        reason = f"the ledger is at version {latest}; this view was built from version {view['ledger_version']}"
    elif latest < view["ledger_version"]:
        reason = f"this view claims version {view['ledger_version']} but the ledger is only at {latest}"
    elif check_hash:
        current = _sha((project / "ledger" / f"L{latest:04d}.json").read_bytes())
        if current != view["ledger_sha256"]:
            stale, reason = True, "the ledger file changed after this view was generated"
    return {"stale": stale, "view_ledger_version": view["ledger_version"],
            "latest_ledger_version": latest, "reason": reason}


def status(project, view_path=None):
    project = Path(project)
    path = Path(view_path) if view_path else project / VIEW_NAME
    errors = project_state.Errors()
    try:
        view = read_view(path)
    except (OSError, ValueError) as exc:
        errors.add("no_view", path, str(exc))
        return errors, {}
    return errors, freshness(project, view)


def _report(errors, extra):
    out = dict(extra)
    out["status"] = "FAIL" if errors else "PASS"
    out["errors"] = list(errors)
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="write the static Owner view from project state")
    gen.add_argument("--project", required=True)
    gen.add_argument("--output", help=f"default: <project>/{VIEW_NAME}")
    gen.add_argument("--generated-at", help="ISO-8601 UTC time to record; default now")
    stat = sub.add_parser("status", help="report whether a view is stale (read-only)")
    stat.add_argument("--project", required=True)
    stat.add_argument("--view", help=f"default: <project>/{VIEW_NAME}")
    args = parser.parse_args(argv)
    if args.command == "generate":
        if args.generated_at is not None and not project_state._timestamp_ok(args.generated_at):
            parser.error("--generated-at must be ISO-8601 UTC ending in Z or +00:00")
        errors, extra = generate(Path(args.project), args.output, args.generated_at)
    else:
        errors, extra = status(Path(args.project), args.view)
    return _report(errors, extra)


if __name__ == "__main__":
    sys.exit(main())
