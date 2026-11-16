"""Opt-in metadata-only parser for explicitly supplied Codex exec JSONL.

Never invokes Codex, reads host configuration, or persists event payload text.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

from digest import build_digest
from recorder import record, validate, append_jsonl

SUPPORTED = {"thread.started", "turn.started", "turn.completed", "turn.failed",
             "item.started", "item.updated", "item.completed", "error"}
TOKEN_FIELDS = {"input": "input_tokens", "cached_input": "cached_input_tokens",
                "cache_creation": "cache_write_input_tokens", "output": "output_tokens"}
MODEL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}")
SENSITIVE_ID = re.compile(r"sk-|bearer|secret|password|api[_-]?key", re.I)


def _identifier(value):
    return (value if isinstance(value, str) and MODEL_ID.fullmatch(value)
            and not SENSITIVE_ID.search(value) else None)


def _reject_constant(_):
    raise ValueError("nonfinite JSON number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _usage(value, issues, line):
    metrics = {key: None for key in TOKEN_FIELDS}
    reasons = {key: "not reported by recognized turn.completed usage" for key in TOKEN_FIELDS}
    if not isinstance(value, dict):
        if value is not None:
            issues.append(f"line {line}: invalid usage object; values omitted")
        return metrics, reasons
    if "total_token_usage" in value or "last_token_usage" in value:
        issues.append(f"line {line}: cumulative/incremental wrapper unsupported; scope unknown")
        return metrics, reasons
    for key, field in TOKEN_FIELDS.items():
        val = value.get(field)
        if val is None:
            continue
        if isinstance(val, int) and not isinstance(val, bool) and val >= 0:
            metrics[key] = val
            reasons[key] = ""
        else:
            issues.append(f"line {line}: invalid {field}; value omitted")
    return metrics, reasons


def parse_stream(raw, *, run_id=None, route="codex/native-or-configured",
                 repository_revision=None, elapsed_ms=None, process_exit_code=None,
                 cancelled=False, cli_version=None, source="supplied-capture"):
    """Read documented per-turn counters; never sum snapshots or item deltas.

    The main record describes the latest observed turn. Earlier turn counters
    are separate in turn_usage. Session totals are unknown, including resumed
    sessions. The parser accepts an observed process exit/cancellation separately
    because an event stream alone does not prove the CLI process exit status.
    """
    if source not in ("supplied-capture", "synthetic-fixture"):
        raise ValueError("unsupported source attribution")
    if process_exit_code is not None and (not isinstance(process_exit_code, int) or isinstance(process_exit_code, bool)):
        raise ValueError("process exit code must be an integer or unknown")
    if elapsed_ms is not None and (not isinstance(elapsed_ms, int) or isinstance(elapsed_ms, bool) or elapsed_ms < 0):
        raise ValueError("elapsed milliseconds must be nonnegative or unknown")
    if cli_version is not None and not _identifier(cli_version):
        raise ValueError("invalid CLI version label")
    run_id = run_id or uuid.uuid4().hex
    issues, safe_events, turns = [], [], []
    thread_ids = set()
    models = set()
    active = False
    terminal = None
    stream_error = False
    completed_count = 0
    metrics, reasons = _usage(None, issues, 0)
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeDecodeError, RecursionError):
            issues.append(f"line {number}: malformed JSON/encoding; contents omitted")
            safe_events.append({"type": "malformed"})
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str) or event["type"] not in SUPPORTED:
            issues.append(f"line {number}: unsupported event type; contents omitted")
            safe_events.append({"type": "unsupported"})
            continue
        kind = event["type"]
        if "schema_version" in event or "version" in event:
            issues.append(f"line {number}: explicit event version unsupported")
            safe_events.append({"type": "unsupported-version"})
            continue
        safe = {"type": kind}
        if event.get("model") is not None:
            model = _identifier(event["model"])
            if model:
                models.add(model)
                safe["model"] = model
            else:
                issues.append(f"line {number}: unsafe/invalid model identity omitted")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
            if isinstance(thread_id, str) and thread_id:
                # IDs are compared in memory only; no private session identifiers persisted.
                thread_ids.add(thread_id)
            else:
                issues.append(f"line {number}: missing/invalid thread identity")
        elif kind == "turn.started":
            if active:
                issues.append(f"line {number}: overlapping turn starts")
            active, terminal = True, None
            metrics, reasons = _usage(None, issues, number)
        elif kind == "turn.completed":
            if terminal is not None and not active:
                issues.append(f"line {number}: repeated terminal without new turn; not counted")
                safe_events.append({"type": "repeated-terminal"})
                continue
            if not active:
                issues.append(f"line {number}: missing turn.started boundary")
            metrics, reasons = _usage(event.get("usage"), issues, number)
            safe["usage"] = {TOKEN_FIELDS[k]: v for k, v in metrics.items()}
            # Reasoning tokens are a reported subset, never added to output_tokens.
            reasoning = event.get("usage", {}).get("reasoning_output_tokens") if isinstance(event.get("usage"), dict) else None
            if reasoning is not None:
                if isinstance(reasoning, int) and not isinstance(reasoning, bool) and reasoning >= 0:
                    safe["usage"]["reasoning_output_tokens"] = reasoning
                else:
                    issues.append(f"line {number}: invalid reasoning_output_tokens; value omitted")
            completed_count += 1
            turns.append({"turn_index": completed_count, "usage_scope": "turn", "usage": dict(metrics),
                          "reasoning_output_tokens": safe["usage"].get("reasoning_output_tokens")})
            terminal, active = "completed", False
        elif kind == "turn.failed":
            terminal, active = "failed", False
            metrics, reasons = _usage(None, issues, number)
        elif kind == "error":
            stream_error = True
        # All message/reasoning/tool/error payloads, unknown fields and IDs are omitted.
        safe_events.append(safe)
    notes = []
    if not completed_count:
        notes.append("no completed turn usage event; usage remains unknown")
    if len(thread_ids) > 1:
        issues.append("multiple threads mixed; usage attribution unknown")
        metrics, reasons = _usage(None, issues, 0)
        turns = []
        for event in safe_events:
            event.pop("usage", None)
    if len(models) > 1:
        issues.append("multiple model identities observed; upstream model unknown")
    if cancelled:
        status = "cancelled"
    elif stream_error or terminal == "failed" or process_exit_code not in (None, 0):
        status = "failed"
    elif terminal == "completed" and not active:
        status = "completed"
    else:
        status = "partial"
    if active or status == "partial":
        notes.append("stream incomplete: final turn has no terminal event")
    notes.extend(issues)
    item = record(run_id=run_id, harness="codex", route=route,
                  upstream_model=next(iter(models)) if len(models) == 1 else None,
                  repository_revision=repository_revision, elapsed_ms=elapsed_ms,
                  usage_scope="turn" if terminal == "completed" and len(thread_ids) <= 1 and not any("scope unknown" in x for x in issues) else "unknown",
                  usage={**metrics, "reported_cost": None, "availability": {**reasons, "reported_cost": "not reported; token counts do not establish billing"}},
                  acceptance={"status": "unknown", "evidence_ref": None, "provenance": "unknown"},
                  source_kind=f"codex-exec-jsonl-{source}", notes=notes)
    validate(item)
    complete = status == "completed" and not issues
    metadata = {"harness": "codex-cli", "cli_version": cli_version,
                "route": route, "effective_provider_route": None,
                "metadata_provenance": "caller-supplied; event identity unverified",
                "source": source, "input_sha256": hashlib.sha256(raw).hexdigest(),
                "input_bytes": len(raw), "payload_storage": "allowlisted-metadata-only"}
    return {"record": item, "events_seen": len(safe_events), "unsupported_or_malformed": issues,
            "complete": complete, "completion_status": status, "process_exit_code": process_exit_code,
            "completed_turns": completed_count, "turn_usage": turns, "session_usage": None,
            "source": metadata, "sanitized_events": safe_events}


def process(raw, *, artifact_dir, **kwargs):
    """Digest only sanitized metadata. Original supplied transcript is never persisted."""
    result = parse_stream(raw, **kwargs)
    safe = (json.dumps({"events": result.pop("sanitized_events")}, sort_keys=True) + "\n").encode("utf-8")
    result["digest"] = build_digest(safe, b"", exit_code=result["process_exit_code"],
                                    command=[], artifact_dir=artifact_dir, run_id=result["record"]["run_id"])
    result["digest"]["source_kind"] = "sanitized-codex-event-metadata; not a process capture"
    if not result["complete"]:
        result["digest"]["flags"] = sorted(set(result["digest"]["flags"]) | {"DIGEST_INCOMPLETE"})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", nargs="?", help="Explicitly supplied JSONL file; defaults to stdin")
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--records")
    parser.add_argument("--run-id")
    parser.add_argument("--route", default="codex/native-or-configured")
    parser.add_argument("--revision")
    parser.add_argument("--elapsed-ms", type=int)
    parser.add_argument("--process-exit-code", type=int, help="Caller-observed Codex exit code, never inferred")
    parser.add_argument("--cancelled", action="store_true", help="Caller-observed cancellation")
    parser.add_argument("--cli-version", help="Caller-observed CLI version label")
    parser.add_argument("--source", choices=("supplied-capture", "synthetic-fixture"), default="supplied-capture")
    args = parser.parse_args(argv)
    raw = Path(args.events).read_bytes() if args.events else sys.stdin.buffer.read()
    result = process(raw, artifact_dir=args.artifacts, run_id=args.run_id, route=args.route,
                     repository_revision=args.revision, elapsed_ms=args.elapsed_ms,
                     process_exit_code=args.process_exit_code, cancelled=args.cancelled,
                     cli_version=args.cli_version, source=args.source)
    if args.records:
        append_jsonl(args.records, result["record"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
