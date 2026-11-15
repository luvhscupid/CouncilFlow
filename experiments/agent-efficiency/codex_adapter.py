"""Opt-in offline adapter for Codex ``exec --json`` JSONL event streams.

Reads an explicitly supplied event file or stdin. It never invokes Codex.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

from digest import build_digest
from recorder import record, validate, append_jsonl

SUPPORTED = {"thread.started", "turn.started", "turn.completed", "turn.failed", "item.started", "item.completed", "item.failed"}

def parse_stream(raw, *, run_id=None, route="codex/native-or-configured", repository_revision=None, elapsed_ms=None):
    """Parse task-scoped aggregate usage when present; preserve unsupported/partial state honestly."""
    run_id = run_id or uuid.uuid4().hex
    events=[]; notes=[]; issues=[]
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip(): continue
        try: event=json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(f"line {line_number}: malformed JSON ({type(exc).__name__})"); continue
        if not isinstance(event,dict) or event.get("type") not in SUPPORTED:
            issues.append(f"line {line_number}: unsupported event type"); continue
        events.append(event)
    completed=[e for e in events if e.get("type")=="turn.completed"]
    usage=completed[-1].get("usage") if completed else None
    # Codex event schema revisions may use total_token_usage; accept only documented
    # aggregate totals with known fields, never infer totals from item deltas.
    totals=usage.get("total_token_usage") if isinstance(usage,dict) else None
    if totals is None and isinstance(usage,dict): totals=usage
    if not isinstance(totals,dict): totals={}
    input_count=totals.get("input_tokens")
    cached=totals.get("cached_input_tokens")
    output=totals.get("output_tokens")
    reasons={"input":"not present in completed turn usage","cached_input":"not present in completed turn usage","cache_creation":"not reported by recognized Codex event","output":"not present in completed turn usage","reported_cost":"not reported by Codex event"}
    for key,source_key,val in (("input","input_tokens",input_count),("cached_input","cached_input_tokens",cached),("output","output_tokens",output)):
        if isinstance(val,int) and not isinstance(val,bool) and val>=0: reasons[key]=""
        else: totals[source_key]=None
    model=completed[-1].get("model") if completed else None
    thread_ids=[e.get("thread_id") for e in events if e.get("type")=="thread.started" and e.get("thread_id")]
    if len(set(thread_ids))>1: notes.append("multiple thread IDs present; stream may combine sessions")
    if not completed: notes.append("no completed turn usage event; usage remains unknown")
    notes.extend(issues)
    item=record(run_id=run_id,harness="codex",route=route,upstream_model=model,repository_revision=repository_revision,elapsed_ms=elapsed_ms,usage_scope="task",
        usage={"input":totals.get("input_tokens"),"cached_input":totals.get("cached_input_tokens"),"cache_creation":None,"output":totals.get("output_tokens"),"reported_cost":None,"availability":reasons},
        acceptance={"status":"unknown","evidence_ref":None,"provenance":"unknown"},source_kind="codex-exec-jsonl",notes=notes)
    validate(item)
    return {"record":item,"events_seen":len(events),"unsupported_or_malformed":issues,"complete":bool(completed) and not issues}

def process(raw, *, artifact_dir, run_id=None, route="codex/native-or-configured", repository_revision=None, elapsed_ms=None):
    run_id=run_id or uuid.uuid4().hex
    result=parse_stream(raw,run_id=run_id,route=route,repository_revision=repository_revision,elapsed_ms=elapsed_ms)
    digest=build_digest(raw,b"",exit_code=0 if result["complete"] else None,command=["codex","exec","--json","(captured input)"],artifact_dir=artifact_dir,run_id=run_id)
    result["digest"]=digest
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("events",nargs="?",help="Codex JSONL file; defaults to stdin"); p.add_argument("--artifacts",required=True); p.add_argument("--records"); p.add_argument("--run-id"); p.add_argument("--route",default="codex/native-or-configured"); p.add_argument("--revision"); p.add_argument("--elapsed-ms",type=int)
    a=p.parse_args(argv); raw=Path(a.events).read_bytes() if a.events else sys.stdin.buffer.read()
    result=process(raw,artifact_dir=a.artifacts,run_id=a.run_id,route=a.route,repository_revision=a.revision,elapsed_ms=a.elapsed_ms)
    if a.records: append_jsonl(a.records,result["record"])
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["complete"] else 2

if __name__=="__main__": raise SystemExit(main())
