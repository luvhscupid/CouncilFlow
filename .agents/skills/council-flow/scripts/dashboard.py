"""Publish read-only local dashboard snapshots for one CouncilFlow task and its project."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import webbrowser


SKILL_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = SKILL_ROOT / "dashboard"
MAX_INPUT_BYTES = 65536
MAX_MESSAGE_FILES = 1024
MAX_EFFICIENCY_BYTES = 1048576
MAX_EFFICIENCY_RECORDS = 1000
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _contracts():
    path = SKILL_ROOT / "scripts" / "contracts.py"
    spec = importlib.util.spec_from_file_location("councilflow_contracts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CouncilFlow packet validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounded_text(path: Path) -> tuple[bytes, object | None, str | None]:
    contracts = _contracts()
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise contracts.ContractError("size", "$", "packet exceeds 65536 UTF-8 bytes")
        return raw, contracts.loads(raw), None
    except (OSError, contracts.ContractError) as error:
        return b"", None, f"{path.name}: could not read valid JSON ({error})."


def _modified(path: Path) -> str | None:
    """File write time as seen by the publisher; informational, not event time."""
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat(timespec="milliseconds")


def _policy() -> dict | None:
    """Read the role table from policies/roles.yaml for the read-only settings view.

    The policy file is restricted block YAML whose list values are JSON arrays,
    so only those lines are read. Anything unexpected leaves the policy out.
    """
    path = SKILL_ROOT / "policies" / "roles.yaml"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    roles: dict[str, dict] = {}
    section = None
    role = None
    order = None
    resources: dict[str, object] = {}
    try:
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            key, _, value = line.strip().partition(":")
            value = value.strip()
            if indent == 0:
                section, role = key, None
                continue
            if section == "roles" and indent == 2 and not value:
                role = key
                roles[role] = {}
            elif section == "roles" and indent == 4 and role:
                if key in {"responsibilities", "abilities"}:
                    roles[role][key] = json.loads(value)
                elif key == "application_code":
                    roles[role][key] = value == "true"
            elif section == "workflow" and key == "order":
                order = json.loads(value)
            elif section == "resources" and indent == 2:
                resources[key] = int(value) if value.isdigit() else value.strip('"')
    except (ValueError, TypeError):
        return None
    if not roles or not isinstance(order, list):
        return None
    return {"source": "policies/roles.yaml", "roles": roles, "order": order, "resources": resources}


def _efficiency(path: Path | None, task_id: str) -> dict | None:
    """Read optional, explicitly supplied Agent Efficiency records for this task."""
    if path is None:
        return None
    result = {"source": path.name, "records": [], "matched": 0, "other_runs": 0,
              "invalid": 0, "error": None}
    recorder_path = SKILL_ROOT / "scripts" / "efficiency" / "recorder.py"
    try:
        spec = importlib.util.spec_from_file_location("councilflow_efficiency_recorder", recorder_path)
        if spec is None or spec.loader is None:
            raise OSError("efficiency recorder is unavailable")
        recorder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recorder)
        with path.open("rb") as stream:
            raw = stream.read(MAX_EFFICIENCY_BYTES + 1)
        if len(raw) > MAX_EFFICIENCY_BYTES:
            raise ValueError(f"records file exceeds {MAX_EFFICIENCY_BYTES} bytes")
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError, ValueError) as error:
        result["error"] = f"{path.name}: {error}"
        return result
    for line in lines[:MAX_EFFICIENCY_RECORDS]:
        if not line.strip():
            continue
        try:
            item = recorder.validate(json.loads(line))
        except (ValueError, TypeError, KeyError, AttributeError):
            result["invalid"] += 1
            continue
        if item["run_id"] == task_id:
            result["records"].append(item)
            result["matched"] += 1
        else:
            result["other_runs"] += 1
    if len(lines) > MAX_EFFICIENCY_RECORDS:
        result["error"] = f"{path.name}: only the first {MAX_EFFICIENCY_RECORDS} records were read"
    return result


def _message_order(messages: list[dict]) -> list[dict]:
    pending = list(messages)
    ordered = []
    emitted: set[str] = set()
    while pending:
        ready = [item for item in pending
                 if item["data"].get("in_reply_to") is None
                 or item["data"].get("in_reply_to") in emitted]
        if not ready:
            return ordered + [item["data"] for item in pending]
        ready.sort(key=lambda item: item["path"])
        for item in ready:
            ordered.append(item["data"])
            emitted.add(item["data"].get("message_id", ""))
            pending.remove(item)
    return ordered


def _run_files(root: Path, task_id: str) -> tuple[list[dict], list[str]]:
    contracts = _contracts()
    run_dir = root / ".councilflow" / "runs" / task_id
    if not run_dir.is_dir() or run_dir.is_symlink():
        return [], []
    resolved_run = run_dir.resolve()
    entries: list[dict] = []
    errors: list[str] = []

    plan_path = run_dir / "plan.json"
    if plan_path.exists():
        if plan_path.is_symlink() or not plan_path.resolve().is_relative_to(resolved_run):
            raw, data, error = b"", None, f"{plan_path.name}: linked plan files are not read."
        else:
            raw, data, error = _bounded_text(plan_path)
        entries.append({
            "name": plan_path.name,
            "path": plan_path.relative_to(root).as_posix(),
            "data": data,
            "error": error,
            "isMessageFile": False,
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "modified": _modified(plan_path),
        })
        if error:
            errors.append(error)

    messages_dir = run_dir / "messages"
    candidates = []
    if messages_dir.is_symlink():
        errors.append("messages: linked message folders are not read.")
    elif messages_dir.is_dir() and messages_dir.resolve().is_relative_to(resolved_run):
        candidates = sorted(messages_dir.glob("*.json"), key=lambda item: item.name)
    if len(candidates) > MAX_MESSAGE_FILES:
        errors.append(f"messages: more than {MAX_MESSAGE_FILES} packet files were found.")
        candidates = candidates[:MAX_MESSAGE_FILES]

    message_data = []
    for path in candidates:
        if path.is_symlink() or not path.resolve().is_relative_to(resolved_run):
            errors.append(f"{path.name}: linked packet files are not read.")
            continue
        raw, data, error = _bounded_text(path)
        entry = {
            "name": path.name,
            "path": path.relative_to(root).as_posix(),
            "data": data,
            "error": error,
            "isMessageFile": True,
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "modified": _modified(path),
        }
        entries.append(entry)
        if error:
            errors.append(error)
        elif not isinstance(data, dict) or data.get("protocol") != "council-flow":
            detail = f"{path.name}: file is not a CouncilFlow packet."
            entry["error"] = detail
            errors.append(detail)
        else:
            try:
                contracts.validate_message(data, root=root)
                message_data.append({"data": data, "path": entry["path"]})
            except contracts.ContractError as error:
                detail = f"{path.name}: {error}."
                entry["error"] = detail
                errors.append(detail)

    if message_data:
        try:
            contracts.validate_sequence(_message_order(message_data), root=root)
        except contracts.ContractError as error:
            detail = f"CouncilFlow packet sequence: {error}."
            if error.code == "causal_reference" and error.field == "in_reply_to":
                valid_ids = {item["data"].get("message_id") for item in message_data}
                offender = next((item for item in message_data
                                 if item["data"].get("in_reply_to") is not None
                                 and item["data"].get("in_reply_to") not in valid_ids), None)
                if offender:
                    message = offender["data"]
                    detail = (f"{offender['path']}: {error.field} ({message.get('message_id')} -> "
                              f"{message.get('in_reply_to')}): {error.detail}.")
                    for entry in entries:
                        if entry["path"] == offender["path"]:
                            entry["error"] = detail
                            break
            errors.append(detail)

    if errors:
        entries.append({
            "name": "dashboard-validation.json",
            "path": "dashboard-validation.json",
            "data": {},
            "error": " ".join(errors),
            "isMessageFile": False,
            "sha256": None,
        })
    return entries, errors


def _inline(source: str, stylesheet: str, reader: str, app: str, files: list[dict],
            context: dict | None = None) -> str:
    source = source.replace(
        '<link rel="stylesheet" href="styles.css">',
        "<style>\n" + stylesheet + "\n</style>",
    )
    initial = json.dumps({**(context or {}), "files": files}, ensure_ascii=False, separators=(",", ":"))
    initial = (initial.replace("&", "\\u0026").replace("<", "\\u003c")
               .replace(">", "\\u003e").replace("\u2028", "\\u2028")
               .replace("\u2029", "\\u2029"))
    scripts = (
        "<script>\n" + reader + "\n</script>\n"
        '<script id="councilflow-run-data" type="application/json">'
        + initial + "</script>\n"
        "<script>\n" + app + "\n</script>"
    )
    source = source.replace(
        '<script src="run-reader.js"></script>\n    <script src="app.js"></script>', scripts
    )
    if "id=\"councilflow-run-data\"" not in source:
        raise RuntimeError("dashboard template no longer matches the publisher interface")
    return source


MAX_LISTED_RUNS = 200


def _write_atomic(output: Path, page: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=".dashboard-", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(page)
        Path(temporary_name).replace(output)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()


def _last_write(run_dir: Path) -> float:
    """Latest packet or board write time in one run folder; informational only."""
    stamps = []
    for path in [run_dir / "dashboard.html", run_dir / "plan.json"]:
        try:
            stamps.append(path.stat().st_mtime)
        except OSError:
            pass
    messages = run_dir / "messages"
    if messages.is_dir() and not messages.is_symlink():
        for index, path in enumerate(messages.glob("*.json")):
            if index >= MAX_MESSAGE_FILES:
                break
            try:
                stamps.append(path.stat().st_mtime)
            except OSError:
                pass
    return max(stamps, default=0.0)


def _project_runs(root: Path, current: str) -> list[dict]:
    """Published boards of this project's runs, newest first, for the Project list tab.

    Only runs that already have a dashboard.html are listed, so each entry is a plain
    link to an existing local file. Nothing here is read until the user follows it.
    """
    runs_dir = root / ".councilflow" / "runs"
    if not runs_dir.is_dir() or runs_dir.is_symlink():
        return []
    found = []
    for run_dir in runs_dir.iterdir():
        name = run_dir.name
        if not TASK_ID.fullmatch(name) or run_dir.is_symlink() or not run_dir.is_dir():
            continue
        board = run_dir / "dashboard.html"
        if name != current and (not board.is_file() or board.is_symlink()):
            continue
        found.append((_last_write(run_dir), name))
    found.sort(key=lambda item: (item[0], item[1]), reverse=True)
    listed = []
    for stamp, name in found[:MAX_LISTED_RUNS]:
        listed.append({
            "taskId": name,
            "path": f".councilflow/runs/{name}/dashboard.html",
            "updated": datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat(timespec="milliseconds") if stamp else None,
            "current": name == current,
        })
    return listed


def _with_hrefs(runs: list[dict], page_dir: str) -> list[dict]:
    """Give each listed run a link relative to the page that embeds it."""
    return [{**run, "href": os.path.relpath(run["path"], page_dir).replace(os.sep, "/")} for run in runs]


def publish_run(root: Path, task_id: str, *, open_browser: bool = False, opener=None,
                efficiency_records: Path | None = None) -> dict:
    """Validate one canonical task directory and atomically publish its HTML views.

    Two self-contained pages are written: the task's own board in
    .councilflow/runs/<task-id>/dashboard.html, and the project board in
    .councilflow/dashboard.html, which always shows the most recently published run
    of this project. --open opens the project board, so the same browser tab keeps
    following whichever run this project is working on.
    """
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id) or task_id in {".", ".."}:
        raise ValueError("task ID must be a single safe path segment")
    root = Path(root).resolve()
    run_dir = root / ".councilflow" / "runs" / task_id
    existing = run_dir if run_dir.exists() else run_dir.parent
    if run_dir.is_symlink() or not existing.resolve().is_relative_to(root):
        raise ValueError("task run directory must stay inside the repository")
    if not run_dir.exists():
        run_dir.mkdir(parents=True)
    if not run_dir.resolve().is_relative_to(root):
        raise ValueError("task run directory must stay inside the repository")
    project_dir = root / ".councilflow"
    if project_dir.is_symlink() or not project_dir.resolve().is_relative_to(root):
        raise ValueError("the .councilflow folder must stay inside the repository")

    files, errors = _run_files(root, task_id)
    template = (
        (DASHBOARD_ROOT / "index.html").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "styles.css").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "run-reader.js").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "app.js").read_text(encoding="utf-8"),
    )
    context = {
        "taskId": task_id,
        "project": root.name or None,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "policy": _policy(),
        "efficiency": _efficiency(efficiency_records, task_id),
    }
    output = run_dir / "dashboard.html"
    project_output = project_dir / "dashboard.html"
    # List the current run first so the task board exists before other pages link to it.
    runs = _project_runs(root, task_id)
    _write_atomic(output, _inline(*template, files, {
        **context, "board": "task", "runs": _with_hrefs(runs, f".councilflow/runs/{task_id}")}))
    _write_atomic(project_output, _inline(*template, files, {
        **context, "board": "project", "runs": _with_hrefs(runs, ".councilflow")}))

    opened = None
    if open_browser:
        open_url = opener or webbrowser.open
        opened = bool(open_url(project_output.resolve().as_uri()))
    return {
        "task_id": task_id,
        "snapshot_path": str(output),
        "project_path": str(project_output),
        "opened": opened,
        "issues": errors,
        "packet_count": sum(1 for item in files if item["isMessageFile"] and item["data"] is not None),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    publish = subparsers.add_parser("publish", help="write a task-specific dashboard snapshot")
    publish.add_argument("--root", type=Path, default=Path.cwd())
    publish.add_argument("--task-id", required=True)
    publish.add_argument("--open", action="store_true", dest="open_browser",
                         help="open the project board (.councilflow/dashboard.html) once in the default browser")
    publish.add_argument("--efficiency-records", type=Path, default=None,
                         help="optional Agent Efficiency JSONL; records whose run_id equals the task ID are shown")
    args = parser.parse_args(argv)
    try:
        result = publish_run(args.root, args.task_id, open_browser=args.open_browser,
                             efficiency_records=args.efficiency_records)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["opened"] is not False else 3


if __name__ == "__main__":
    raise SystemExit(main())
