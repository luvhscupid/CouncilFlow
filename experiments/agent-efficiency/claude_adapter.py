"""Offline parser for explicitly supplied Claude Code stream-json output.

No config, environment variables, credentials, or live Claude/xKiro calls are read.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import uuid

from digest import build_digest
from recorder import record, validate, append_jsonl

SUPPORTED={"system", "assistant", "user", "result", "stream_event"}

def parse_stream(raw, *, run_id=None, gateway="xkiro", upstream_model=None, route=None, repository_revision=None, elapsed_ms=None):
    run_id=run_id or uuid.uuid4().hex
    events=[]; issues=[]; models=[]; usages=[]; notes=[]; retries=[]
    for n,line in enumerate(raw.splitlines(),1):
        if not line.strip(): continue
        try: event=json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(f"line {n}: malformed JSON at column {exc.colno}"); continue
        if not isinstance(event,dict) or event.get("type") not in SUPPORTED:
            issues.append(f"line {n}: unsupported event type"); continue
        events.append(event)
        model=event.get("model")
        message=event.get("message")
        if isinstance(message,dict): model=model or message.get("model")
        if model: models.append(model)
        usage=event.get("usage")
        if not isinstance(usage,dict) and isinstance(message,dict): usage=message.get("usage")
        if isinstance(usage,dict): usages.append(usage)
        # Retry counts are recorded only when a gateway explicitly reports them.
        gateway_meta=event.get("gateway")
        if isinstance(gateway_meta,dict) and isinstance(gateway_meta.get("retry_count"),int) and gateway_meta["retry_count"]>=0:
            retries.append(gateway_meta["retry_count"])
    distinct=list(dict.fromkeys(models))
    if len(distinct)>1: notes.append("model changed during stream: "+", ".join(distinct))
    if retries: notes.append(f"gateway-reported retry_count={sum(retries)}")
    else: notes.append("gateway retry count not reported")
    if upstream_model is None and len(distinct)==1: upstream_model=distinct[0]
    elif len(distinct)>1: upstream_model=None
    # Use final structured usage event as a snapshot; never sum message and result
    # counters because common formats repeat cumulative totals.
    usage=usages[-1] if usages else {}
    mappings={"input":"input_tokens","cached_input":"cache_read_input_tokens","cache_creation":"cache_creation_input_tokens","output":"output_tokens"}
    metrics={}; availability={}
    for name,source in mappings.items():
        value=usage.get(source)
        if isinstance(value,int) and not isinstance(value,bool) and value>=0:
            metrics[name]=value; availability[name]=""
        else:
            metrics[name]=None; availability[name]=f"{source} absent from captured Claude output"
    metrics["reported_cost"]=None
    availability["reported_cost"]="no verified xKiro billing field in captured Claude output"
    if not usages: notes.append("no usage event; all usage remains unknown")
    if not any(e.get("type")=="result" for e in events): notes.append("stream incomplete: no result event")
    notes.extend(issues)
    route=route or f"claude-code/{gateway}/stream-json"
    item=record(run_id=run_id,harness="claude-code",gateway=gateway,route=route,upstream_model=upstream_model,
        repository_revision=repository_revision,elapsed_ms=elapsed_ms,usage_scope="task",
        usage={**metrics,"availability":availability},acceptance={"status":"unknown","evidence_ref":None,"provenance":"unknown"},
        source_kind="claude-code-stream-json",notes=notes)
    validate(item)
    return {"record":item,"events_seen":len(events),"unsupported_or_malformed":issues,"complete":any(e.get("type")=="result" for e in events) and not issues}

def process(raw, *, artifact_dir, **kwargs):
    run_id=kwargs.pop("run_id",None) or uuid.uuid4().hex
    result=parse_stream(raw,run_id=run_id,**kwargs)
    result["digest"]=build_digest(raw,b"",exit_code=0 if result["complete"] else None,
        command=["claude","--output-format","stream-json","(captured input)"],artifact_dir=artifact_dir,run_id=run_id)
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("events",nargs="?"); p.add_argument("--artifacts",required=True); p.add_argument("--records"); p.add_argument("--run-id"); p.add_argument("--gateway",default="xkiro"); p.add_argument("--route"); p.add_argument("--model"); p.add_argument("--revision"); p.add_argument("--elapsed-ms",type=int)
    a=p.parse_args(argv); raw=Path(a.events).read_bytes() if a.events else sys.stdin.buffer.read()
    result=process(raw,artifact_dir=a.artifacts,run_id=a.run_id,gateway=a.gateway,route=a.route,upstream_model=a.model,repository_revision=a.revision,elapsed_ms=a.elapsed_ms)
    if a.records: append_jsonl(a.records,result["record"])
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["complete"] else 2

if __name__=="__main__": raise SystemExit(main())
