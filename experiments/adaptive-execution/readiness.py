"""Adaptive readiness extension (ADR 5, 5.1, 6): PROCEED_WITH_ASSUMPTIONS, discovery cap,
derived default-budget counter, decision classes.
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Owner approvals live in Council 001/R6 runtime state (D5); nothing here stores or grants one."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import run_cli  # noqa: E402
import adaptive_mode as am  # noqa: E402
import ledger as lg  # noqa: E402

ADAPTIVE_STATES = ["READY", "PROCEED_WITH_ASSUMPTIONS", "BLOCKED"]
PWA = "PROCEED_WITH_ASSUMPTIONS"
MAX_DISCOVERY_CYCLES = 2
# class -> (rank, authority, effect)
CLASSES = {
    "cheap_reversible": (0, "planner_provisional_default", "proceed"),
    "costly_reversible": (1, "owner_approval", "pause_affected_slice"),
    "irreversible_or_external": (2, "owner_approval", "block"),
    "security_data_financial_legal": (2, "owner_approval", "block"),
    "owner_controlled": (2, "owner_approval", "block"),
}


def validate_readiness_ext(readiness, ledger, mode):
    if mode not in ("adaptive", "default"):
        return ["mode must be 'adaptive' or 'default'"]
    if not isinstance(readiness, dict):
        return ["readiness must be an object"]
    state = readiness.get("state")
    if mode == "default":
        errs = am.validate_readiness(readiness)
        if state == PWA:
            errs.append("PROCEED_WITH_ASSUMPTIONS is not allowed in mode 'default'")
        return errs
    probe = dict(readiness)
    if state in ADAPTIVE_STATES:
        probe["state"] = "READY"  # reuse the base field checks; the state set differs here
    errs = am.validate_readiness(probe)
    if state not in ADAPTIVE_STATES:
        errs = [e for e in errs if not e.startswith("state must")]
        errs.append("state must be one of %s in mode 'adaptive'" % ADAPTIVE_STATES)
    if state != PWA:
        if "assumption_ids" in readiness or "blocking_decision" in readiness:
            errs.append("assumption_ids and blocking_decision are only allowed with %s" % PWA)
        return errs
    if readiness.get("blocking_decision") is not False:
        errs.append("blocking_decision must be false for %s" % PWA)
    ids = readiness.get("assumption_ids")
    if not isinstance(ids, list) or not ids or not all(am._str(i) for i in ids):
        errs.append("assumption_ids must be a nonempty list of ids")
        return errs
    lerrs = lg.validate_ledger(ledger)
    if lerrs:
        return errs + ["ledger invalid: %s" % e for e in lerrs]
    active = {e["id"]: e for e in lg.active_entries(ledger)}
    for i in ids:
        e = active.get(i)
        if e is None:
            errs.append("assumption id %r is not an active ledger entry" % i)
        elif e["type"] not in ("Assumption", "Decision") or e["status"] != "provisional":
            errs.append("assumption id %r must be an active provisional Assumption or Decision (is %s %s)"
                        % (i, e["type"], e["status"]))
    return errs


def validate_readiness_bundle(obj):
    """CLI document: {"readiness": {...}, "ledger": {...}, "mode": "adaptive"|"default"}."""
    if not isinstance(obj, dict) or set(obj) != {"readiness", "ledger", "mode"}:
        return ["document must be an object with exactly readiness, ledger, mode"]
    return validate_readiness_ext(obj["readiness"], obj["ledger"], obj["mode"])


def discovery_cycles_used(events, slice_id):
    return sum(1 for e in events if isinstance(e, dict) and e.get("cycle_kind") == "discovery"
               and e.get("slice_id") == slice_id)


def request_discovery(events, slice_id):
    if discovery_cycles_used(events, slice_id) >= MAX_DISCOVERY_CYCLES:
        return {"slice_id": slice_id, "action": "escalate_scope_question"}
    return {"slice_id": slice_id, "action": "run_discovery_cycle"}


def active_unconfirmed_count(ledger):
    return sum(1 for e in lg.active_entries(ledger)
               if e.get("type") in ("Assumption", "Decision") and e.get("status") == "provisional")


def validate_budget_config(config):
    lim = config.get("unconfirmed_decision_limit") if isinstance(config, dict) else None
    if not (isinstance(lim, int) and not isinstance(lim, bool) and lim >= 0):
        return ["unconfirmed_decision_limit must be an integer >= 0"]
    return []


def evaluate_slices(ledger, slices, config):
    """Returns {slice_id: 'BLOCKED'|'PAUSED_BUDGET'|'CONTINUE'}."""
    errs = validate_budget_config(config)
    deps = {}
    for s in slices if isinstance(slices, list) else []:
        n = s.get("requires_new_defaults") if isinstance(s, dict) else None
        if not (isinstance(s, dict) and am._str(s.get("slice_id")) and isinstance(n, int)
                and not isinstance(n, bool) and n >= 0 and isinstance(s.get("blocking_decision"), bool)
                and isinstance(s.get("depends_on"), list)):
            errs.append("bad slice entry: %r" % (s,))
        else:
            deps[s["slice_id"]] = s
    if errs or not isinstance(slices, list):
        raise ValueError("; ".join(errs or ["slices must be a list"]))
    limit, used = config["unconfirmed_decision_limit"], active_unconfirmed_count(ledger)
    out = {}
    for sid, s in deps.items():
        if s["blocking_decision"]:
            out[sid] = "BLOCKED"  # never downgraded by budget
        elif used + s["requires_new_defaults"] > limit:
            out[sid] = "PAUSED_BUDGET"
    changed = True
    while changed:  # pause transitive dependents
        changed = False
        for sid, s in deps.items():
            if sid not in out and any(out.get(d) == "PAUSED_BUDGET" for d in s["depends_on"]):
                out[sid] = "PAUSED_BUDGET"
                changed = True
    return {sid: out.get(sid, "CONTINUE") for sid in deps}


def check_classification(minimum_class, planner_class):
    for c in (minimum_class, planner_class):
        if c not in CLASSES:
            return ["unknown decision class %r (allowed %s)" % (c, sorted(CLASSES))]
    if CLASSES[planner_class][0] < CLASSES[minimum_class][0]:
        return ["planner class %r downgrades minimum class %r" % (planner_class, minimum_class)]
    return []


if __name__ == "__main__":
    sys.exit(run_cli(validate_readiness_bundle, sys.argv[1:]))
