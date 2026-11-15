"""Offline, provider-neutral agent usage records. No host access or network calls."""
from __future__ import annotations
import json
from pathlib import Path

USAGE_FIELDS = ("input", "cached_input", "cache_creation", "output", "reported_cost")

def record(*, run_id, harness, route, task_class=None, upstream_model=None, repository_revision=None,
           elapsed_ms=None, usage_scope="unknown", usage=None, attempt=1, acceptance=None,
           source_kind="manual", notes=None):
    usage = usage or {}
    reasons = {key: usage.get("availability", {}).get(key, "not reported by source") for key in USAGE_FIELDS}
    metrics = {key: usage.get(key) for key in USAGE_FIELDS}
    metrics["availability"] = reasons
    return {"schema_version":"1.0", "run_id":run_id, "task_class":task_class,
        "harness":harness, "route":route, "upstream_model":upstream_model,
        "repository_revision":repository_revision, "elapsed_ms":elapsed_ms,
        "usage_scope":usage_scope, "usage":metrics, "attempt":attempt,
        "acceptance":acceptance or {"status":"unknown","evidence_ref":None,"provenance":"unknown"},
        "source_kind":source_kind, "notes":notes or []}

def validate(item):
    """Validate core contract without third-party JSON Schema packages."""
    required = {"schema_version","run_id","task_class","harness","route","upstream_model","repository_revision","elapsed_ms","usage_scope","usage","attempt","acceptance","source_kind","notes"}
    if set(item) != required: raise ValueError("record fields do not match schema")
    if item["schema_version"] != "1.0" or not item["run_id"]: raise ValueError("invalid version or run_id")
    if item["harness"] not in ("codex","claude-code","unknown"): raise ValueError("invalid harness")
    if item["harness"] == "codex" and item["route"] != "codex/native-or-configured": raise ValueError("invalid Codex route")
    if item["harness"] == "claude-code" and not item["route"].startswith("claude-code/xkiro/"): raise ValueError("invalid Claude/xKiro route")
    u=item["usage"]
    if set(u) != set(USAGE_FIELDS) | {"availability"} or set(u["availability"]) != set(USAGE_FIELDS): raise ValueError("usage fields/reasons required")
    for key in USAGE_FIELDS:
        value=u[key]
        if value is not None and (not isinstance(value,(int,float)) or isinstance(value,bool) or value < 0): raise ValueError(f"invalid {key}")
        if value is None and not u["availability"][key]: raise ValueError(f"missing reason for {key}")
    a=item["acceptance"]
    if a["status"] == "accepted" and (not a["evidence_ref"] or a["provenance"] not in ("owner","external-check")): raise ValueError("accepted outcome requires independent evidence provenance")
    return item

def parse_codex_event(event, *, run_id, route="codex/native-or-configured", **metadata):
    """Recognize a sanitized Codex task_complete event; unknown event formats raise ValueError."""
    if event.get("type") != "task_complete" or not isinstance(event.get("usage"),dict): raise ValueError("unsupported Codex event")
    u=event["usage"]
    return record(run_id=run_id,harness="codex",route=route,upstream_model=event.get("model"),usage_scope="task",usage={"input":u.get("input_tokens"),"cached_input":u.get("cached_input_tokens"),"cache_creation":None,"output":u.get("output_tokens"),"reported_cost":None,"availability":{"cache_creation":"not exposed by recognized event","reported_cost":"not reported by recognized event"}},source_kind="codex-json-event-synthetic",**metadata)

def parse_claude_json(event, *, run_id, upstream_model=None, **metadata):
    """Parse documented-shaped Claude result usage as harness usage, never gateway billing."""
    if not isinstance(event.get("usage"),dict): raise ValueError("unsupported Claude event")
    u=event["usage"]
    return record(run_id=run_id,harness="claude-code",route=f"claude-code/xkiro/{upstream_model or 'unknown'}",upstream_model=upstream_model,usage_scope="task",usage={"input":u.get("input_tokens"),"cached_input":u.get("cache_read_input_tokens"),"cache_creation":u.get("cache_creation_input_tokens"),"output":u.get("output_tokens"),"reported_cost":None,"availability":{"reported_cost":"xKiro/provider billing not present in Claude result"}},source_kind="claude-json-synthetic",**metadata)

def append_jsonl(path, item):
    validate(item)
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f: f.write(json.dumps(item,sort_keys=True)+"\n")
