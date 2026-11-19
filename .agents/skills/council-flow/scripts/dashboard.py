"""Publish a read-only local dashboard snapshot for one CouncilFlow task."""
from __future__ import annotations

import argparse
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


def _inline(source: str, stylesheet: str, reader: str, app: str, files: list[dict]) -> str:
    source = source.replace(
        '<link rel="stylesheet" href="styles.css">',
        "<style>\n" + stylesheet + "\n</style>",
    )
    initial = json.dumps({"files": files}, ensure_ascii=False, separators=(",", ":"))
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
    source = source.replace(
        '<meta name="color-scheme" content="dark">',
        '<meta name="color-scheme" content="dark">\n'
        '<meta http-equiv="refresh" content="2">',
    )
    if "id=\"councilflow-run-data\"" not in source or "http-equiv=\"refresh\"" not in source:
        raise RuntimeError("dashboard template no longer matches the publisher interface")
    return source


def publish_run(root: Path, task_id: str, *, open_browser: bool = False, opener=None) -> dict:
    """Validate one canonical task directory and atomically publish its HTML view."""
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id) or task_id in {".", ".."}:
        raise ValueError("task ID must be a single safe path segment")
    root = Path(root).resolve()
    run_dir = root / ".councilflow" / "runs" / task_id
    if not run_dir.exists():
        run_dir.mkdir(parents=True)
    if run_dir.is_symlink() or not run_dir.resolve().is_relative_to(root):
        raise ValueError("task run directory must stay inside the repository")

    files, errors = _run_files(root, task_id)
    page = _inline(
        (DASHBOARD_ROOT / "index.html").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "styles.css").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "run-reader.js").read_text(encoding="utf-8"),
        (DASHBOARD_ROOT / "app.js").read_text(encoding="utf-8"),
        files,
    )
    output = run_dir / "dashboard.html"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".dashboard-", suffix=".tmp", dir=run_dir)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(page)
        Path(temporary_name).replace(output)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()

    opened = None
    if open_browser:
        open_url = opener or webbrowser.open
        opened = bool(open_url(output.resolve().as_uri()))
    return {
        "task_id": task_id,
        "snapshot_path": str(output),
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
                         help="open the snapshot once in the host's default browser")
    args = parser.parse_args(argv)
    try:
        result = publish_run(args.root, args.task_id, open_browser=args.open_browser)
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["opened"] is not False else 3


if __name__ == "__main__":
    raise SystemExit(main())
