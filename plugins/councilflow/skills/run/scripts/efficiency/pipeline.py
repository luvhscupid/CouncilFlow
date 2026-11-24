"""Shared steps of the opt-in usage trackers; each host adapter only reads its own events.

A host adapter supplies parse_stream(raw, **options) -> result dict (with
"record", "complete", "process_exit_code" and "sanitized_events"). This module
owns everything after that: the sanitized-metadata digest, the common command
line, the --records append, the JSON print and the 0/2 exit code. It never
invokes a host, reads host configuration, or persists event payload text.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

_SCRIPTS = str(Path(__file__).resolve().parents[1])
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)  # shared strict_json lives in the parent scripts folder

from strict_json import loads as strict_loads  # noqa: E402
from digest import build_digest  # noqa: E402
from recorder import append_jsonl  # noqa: E402

MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}")
SENSITIVE_ID = re.compile(r"sk-|bearer|secret|password|api[_-]?key", re.I)


def safe_label(value):
    """Return a model or version label only when it is a plain, non-secret identifier."""
    return (value if isinstance(value, str) and MODEL_ID.fullmatch(value)
            and not SENSITIVE_ID.search(value) else None)


def events(lines, supported, issues, safe_events):
    """Yield (line number, event) for supported, unversioned JSON events; record the rest."""
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = strict_loads(line)
        except (ValueError, UnicodeDecodeError, RecursionError):
            issues.append(f"line {number}: malformed JSON/encoding; contents omitted")
            safe_events.append({"type": "malformed"})
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str) or event["type"] not in supported:
            issues.append(f"line {number}: unsupported event type; contents omitted")
            safe_events.append({"type": "unsupported"})
            continue
        if "schema_version" in event or "version" in event:
            issues.append(f"line {number}: explicit event version unsupported")
            safe_events.append({"type": "unsupported-version"})
            continue
        yield number, event


def process(parse_stream, raw, *, artifact_dir, host, **kwargs):
    """Digest only sanitized metadata. Original supplied transcript is never persisted."""
    result = parse_stream(raw, **kwargs)
    safe = (json.dumps({"events": result.pop("sanitized_events")}, sort_keys=True) + "\n").encode("utf-8")
    result["digest"] = build_digest(safe, b"", exit_code=result["process_exit_code"],
                                    command=[], artifact_dir=artifact_dir, run_id=result["record"]["run_id"])
    result["digest"]["source_kind"] = f"sanitized-{host}-event-metadata; not a process capture"
    if not result["complete"]:
        result["digest"]["flags"] = sorted(set(result["digest"]["flags"]) | {"DIGEST_INCOMPLETE"})
    return result


def parser(description, events_help):
    """Command-line options every tracker shares; adapters add their own after these."""
    out = argparse.ArgumentParser(description=description)
    out.add_argument("events", nargs="?", help=events_help)
    out.add_argument("--artifacts", required=True)
    out.add_argument("--records")
    out.add_argument("--run-id")
    out.add_argument("--revision")
    out.add_argument("--elapsed-ms", type=int)
    out.add_argument("--process-exit-code", type=int, help="Caller-observed exit code, never inferred")
    out.add_argument("--cancelled", action="store_true", help="Caller-observed cancellation")
    out.add_argument("--cli-version", help="Caller-observed CLI version label")
    out.add_argument("--source", choices=("supplied-capture", "synthetic-fixture"), default="supplied-capture")
    return out


def run(parse_stream, args, *, host, **host_options):
    """Read the explicit capture (or stdin), process it, append the record, print, exit 0 or 2."""
    raw = Path(args.events).read_bytes() if args.events else sys.stdin.buffer.read()
    result = process(parse_stream, raw, artifact_dir=args.artifacts, host=host, run_id=args.run_id,
                     repository_revision=args.revision, elapsed_ms=args.elapsed_ms,
                     process_exit_code=args.process_exit_code, cancelled=args.cancelled,
                     cli_version=args.cli_version, source=args.source, **host_options)
    if args.records:
        append_jsonl(args.records, result["record"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["complete"] else 2
