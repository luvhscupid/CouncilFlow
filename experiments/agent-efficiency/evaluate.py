"""Offline paired evaluation and approval-ready protocol drafting."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

def _mean_ci(values):
    if not values: return {"n":0,"mean":None,"sd":None,"ci95":None}
    mean=statistics.mean(values)
    sd=statistics.stdev(values) if len(values)>1 else None
    margin=1.96*sd/math.sqrt(len(values)) if sd is not None else None
    return {"n":len(values),"mean":mean,"sd":sd,"ci95":[mean-margin,mean+margin] if margin is not None else None}

def _valid_measurement(rec, key):
    value=rec.get("usage",{}).get(key)
    return value if isinstance(value,(int,float)) and not isinstance(value,bool) and value>=0 else None

def evaluate(pairs, *, minimum_worthwhile_improvement, reliability_threshold, spending_budget):
    """Compare matched baseline/optimized observations; unknowns are excluded, never zero-filled."""
    if minimum_worthwhile_improvement<0 or not 0<=reliability_threshold<=1 or spending_budget<0: raise ValueError("invalid owner thresholds")
    cost_delta=[]; time_delta=[]; baseline_cost=[]; optimized_cost=[]; baseline_time=[]; optimized_time=[]
    b_accept=o_accept=0; b_known=o_known=0; b_retries=[]; o_retries=[]; b_cache=[]; o_cache=[]
    missed=[]; budget_total=0.; budget_known=True; valid_pairs=[]
    for pair in pairs:
        b,o=pair["baseline"],pair["optimized"]
        for r in (b,o):
            if r.get("acceptance",{}).get("status") in ("accepted","rejected"): pass
        bid=b.get("task_id"); oid=o.get("task_id")
        if not bid or bid!=oid: raise ValueError("paired records require matching task_id")
        valid_pairs.append(bid)
        for rec,side in ((b,"b"),(o,"o")):
            status=rec.get("acceptance",{}).get("status")
            if status in ("accepted","rejected"):
                if side=="b": b_known+=1; b_accept+=status=="accepted"
                else: o_known+=1; o_accept+=status=="accepted"
            attempt=rec.get("attempt")
            if isinstance(attempt,int) and attempt>=1: (b_retries if side=="b" else o_retries).append(attempt-1)
            cache=_valid_measurement(rec,"cached_input"); inp=_valid_measurement(rec,"input")
            if cache is not None and inp and inp>0: (b_cache if side=="b" else o_cache).append(cache/inp)
        bc,oc=_valid_measurement(b,"reported_cost"),_valid_measurement(o,"reported_cost")
        if b.get("acceptance",{}).get("status")=="accepted" and bc is not None: baseline_cost.append(bc)
        if o.get("acceptance",{}).get("status")=="accepted" and oc is not None: optimized_cost.append(oc)
        if bc is not None and oc is not None and b.get("acceptance",{}).get("status")=="accepted" and o.get("acceptance",{}).get("status")=="accepted": cost_delta.append((bc-oc)/bc if bc>0 else 0)
        bt,ot=b.get("elapsed_ms"),o.get("elapsed_ms")
        if isinstance(bt,(int,float)) and isinstance(ot,(int,float)):
            baseline_time.append(bt); optimized_time.append(ot); time_delta.append(bt-ot)
        for rec in (b,o):
            c=_valid_measurement(rec,"reported_cost")
            if c is None: budget_known=False
            else: budget_total+=c
        review=o.get("digest_review",{})
        if review.get("failure_present") is True and review.get("summary_detected") is False:
            missed.append({"task_id":oid,"evidence_ref":review.get("evidence_ref")})
    reliability={"baseline":{"accepted":b_accept,"known":b_known,"rate":b_accept/b_known if b_known else None},"optimized":{"accepted":o_accept,"known":o_known,"rate":o_accept/o_known if o_known else None}}
    avg_improvement=statistics.mean(cost_delta) if cost_delta else None
    outcome="INCONCLUSIVE"
    if avg_improvement is not None and avg_improvement>=minimum_worthwhile_improvement and reliability["optimized"]["rate"] is not None and reliability["optimized"]["rate"]>=reliability_threshold and not missed and budget_known and budget_total<=spending_budget: outcome="BENEFIT_OBSERVED"
    elif missed or (reliability["optimized"]["rate"] is not None and reliability["optimized"]["rate"]<reliability_threshold) or (budget_known and budget_total>spending_budget): outcome="CLOSED_NO_BENEFIT"
    return {"pair_count":len(valid_pairs),"paired_task_ids":valid_pairs,"accepted_cost_improvement_fraction":_mean_ci(cost_delta),"elapsed_time_saved_ms":_mean_ci(time_delta),"accepted_cost":{"baseline_n":len(baseline_cost),"baseline_mean":statistics.mean(baseline_cost) if baseline_cost else None,"optimized_n":len(optimized_cost),"optimized_mean":statistics.mean(optimized_cost) if optimized_cost else None},"reliability":reliability,"retries":{"baseline":_mean_ci(b_retries),"optimized":_mean_ci(o_retries)},"cache_hit_fraction":{"baseline":_mean_ci(b_cache),"optimized":_mean_ci(o_cache),"meaning":"cached_input/input where both reported; not gateway cache efficacy"},"digest_missed_failures":missed,"spending":{"known":budget_known,"observed_total":budget_total if budget_known else None,"owner_budget":spending_budget,"within_budget":budget_total<=spending_budget if budget_known else None},"thresholds":{"minimum_worthwhile_improvement":minimum_worthwhile_improvement,"reliability_threshold":reliability_threshold},"provisional_outcome":outcome,"approval_status":"NOT_APPROVED; offline analysis only"}

def draft_protocol(*, task_set, minimum_worthwhile_improvement, reliability_threshold, spending_budget, max_runs, max_elapsed_minutes):
    if max_runs<1 or max_elapsed_minutes<=0: raise ValueError("positive run and time bounds required")
    return {"title":"Agent efficiency paired evaluation (DRAFT)","status":"PROPOSED_FOR_OWNER_APPROVAL","scope":"Phase 5 paired baseline versus optimized workflow; no run authorized by this artifact","task_set":task_set,"pairing":"same task and environment; record task_id and randomized/order details","metrics":["accepted-task reported cost","acceptance reliability","attempts/retries","elapsed time","reported cache counters where available","digest-related missed failures"],"minimum_worthwhile_improvement":minimum_worthwhile_improvement,"minimum_reliability":reliability_threshold,"spending_budget":spending_budget,"max_runs":max_runs,"max_elapsed_minutes":max_elapsed_minutes,"missing_data":"remain unknown; no imputation; exclude from metric denominators and report counts","decision_rule":"BENEFIT_OBSERVED only if paired accepted-task cost improvement meets minimum, reliability threshold is met, no digest-missed failures occur, and complete reported spend is within budget; CLOSED_NO_BENEFIT for missed failure, reliability breach, or known budget breach; otherwise INCONCLUSIVE","terminal_outcomes":["BENEFIT_OBSERVED","CLOSED_NO_BENEFIT","INCONCLUSIVE"],"approval":"Owner approval required before execution; this draft does not approve or activate the experiment","hash_binding":"After Owner approval, freeze exact protocol bytes and record SHA-256 before first run; do not alter thresholds after observations"}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest="cmd",required=True)
    e=sub.add_parser("evaluate"); e.add_argument("pairs"); e.add_argument("--minimum-improvement",type=float,required=True); e.add_argument("--minimum-reliability",type=float,required=True); e.add_argument("--budget",type=float,required=True); e.add_argument("--output")
    d=sub.add_parser("draft"); d.add_argument("--task-set",required=True); d.add_argument("--minimum-improvement",type=float,required=True); d.add_argument("--minimum-reliability",type=float,required=True); d.add_argument("--budget",type=float,required=True); d.add_argument("--max-runs",type=int,required=True); d.add_argument("--max-minutes",type=float,required=True); d.add_argument("--output",required=True)
    a=p.parse_args(argv)
    if a.cmd=="evaluate": result=evaluate(json.loads(Path(a.pairs).read_text()),minimum_worthwhile_improvement=a.minimum_improvement,reliability_threshold=a.minimum_reliability,spending_budget=a.budget)
    else: result=draft_protocol(task_set=a.task_set,minimum_worthwhile_improvement=a.minimum_improvement,reliability_threshold=a.minimum_reliability,spending_budget=a.budget,max_runs=a.max_runs,max_elapsed_minutes=a.max_minutes)
    encoded=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if getattr(a,"output",None): Path(a.output).write_text(encoded,encoding="utf-8")
    print(encoded,end="")

if __name__=="__main__": main()
