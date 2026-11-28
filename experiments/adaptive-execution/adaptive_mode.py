"""Opt-in adaptive mode: slice-plan (Manager) and slice-readiness (Planner) artifacts.
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import run_cli  # noqa: E402

SCHEMA = "adaptive-1"
ROLES = ["worker", "tester", "reviewer"]
STATUSES = ["pending", "in_progress", "blocked", "done"]
STATES = ["READY", "NEEDS_INFORMATION", "BLOCKED"]  # PROCEED_WITH_ASSUMPTIONS is added by S8


def _posint(x):
    return isinstance(x, int) and not isinstance(x, bool) and x > 0


def _str(x):
    return isinstance(x, str) and x.strip() != ""


def validate_slice_plan(obj):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    errs = []
    if obj.get("schema_version") != SCHEMA:
        errs.append("schema_version must be %r" % SCHEMA)
    if obj.get("author_role") != "manager":
        errs.append("author_role must be 'manager' (Manager owns the slice plan)")
    if not _str(obj.get("plan_id")):
        errs.append("plan_id must be a nonempty string")
    if not _posint(obj.get("plan_revision")):
        errs.append("plan_revision must be a positive integer")
    mode = obj.get("mode")
    if mode not in ("adaptive", "default"):
        errs.append("mode must be 'adaptive' or 'default'")
    slices = obj.get("slices")
    if not isinstance(slices, list):
        return errs + ["slices must be a list"]
    if mode == "default" and slices:
        errs.append("mode 'default' uses the existing planner path; slices must be empty")
    seen = set()
    for i, s in enumerate(slices):
        p = "slices[%d]" % i
        if not isinstance(s, dict):
            errs.append("%s must be an object" % p)
            continue
        sid = s.get("slice_id")
        if not _str(sid):
            errs.append("%s.slice_id must be a nonempty string" % p)
        elif sid in seen:
            errs.append("duplicate slice_id %r" % sid)
        else:
            seen.add(sid)
        if not _str(s.get("title")):
            errs.append("%s.title must be a nonempty string" % p)
        dep = s.get("depends_on")
        if not isinstance(dep, list) or not all(_str(d) for d in dep):
            errs.append("%s.depends_on must be a list of slice_ids" % p)
        a = s.get("assignment")
        if not isinstance(a, dict):
            errs.append("%s.assignment must be an object" % p)
        else:
            if a.get("role") not in ROLES:
                errs.append("%s.assignment.role must be one of %s (wire names, not display aliases)" % (p, ROLES))
            if "instance_hint" in a and not _str(a["instance_hint"]):
                errs.append("%s.assignment.instance_hint must be a nonempty string if present" % p)
        if not isinstance(s.get("model_routing"), str):
            errs.append("%s.model_routing must be a string" % p)
        if s.get("execution_status") not in STATUSES:
            errs.append("%s.execution_status must be one of %s" % (p, STATUSES))
        if not _posint(s.get("pinned_ledger_version")):
            errs.append("%s.pinned_ledger_version must be a positive integer" % p)
    if not errs:
        errs += validate_slice_graph(obj)
    return errs


def validate_slice_graph(plan):
    """Dependencies exist and the graph is acyclic."""
    deps = {s["slice_id"]: s["depends_on"] for s in plan.get("slices", [])
            if isinstance(s, dict) and isinstance(s.get("slice_id"), str)
            and isinstance(s.get("depends_on"), list)}
    errs = []
    for sid, ds in deps.items():
        for d in ds:
            if d not in deps:
                errs.append("slice %r depends on unknown slice %r" % (sid, d))
    if errs:
        return errs
    state = {}

    def visit(n):
        state[n] = 1
        for d in deps[n]:
            if state.get(d) == 1 or (d not in state and visit(d)):
                return True
        state[n] = 2
        return False

    for n in deps:
        if n not in state and visit(n):
            return ["dependency cycle involving slice %r" % n]
    return []


def validate_readiness(obj):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    errs = []
    if obj.get("schema_version") != SCHEMA:
        errs.append("schema_version must be %r" % SCHEMA)
    if obj.get("author_role") != "planner":
        errs.append("author_role must be 'planner' (Planner owns readiness)")
    for k in ("plan_id", "slice_id", "reason"):
        if not _str(obj.get(k)):
            errs.append("%s must be a nonempty string" % k)
    if obj.get("state") not in STATES:
        errs.append("state must be one of %s" % STATES)
    if not _posint(obj.get("ledger_version")):
        errs.append("ledger_version must be a positive integer")
    ti = obj.get("task_instructions")
    if ti is not None and (not isinstance(ti, list) or not all(_str(x) for x in ti)):
        errs.append("task_instructions must be a list of nonempty strings if present")
    return errs


def check_coherence(plan, readinesses):
    pinned = {s["slice_id"]: s["pinned_ledger_version"] for s in plan.get("slices", [])}
    errs = []
    for i, r in enumerate(readinesses):
        sid = r.get("slice_id")
        if r.get("plan_id") != plan.get("plan_id"):
            errs.append("readiness[%d] plan_id differs from plan" % i)
        if sid not in pinned:
            errs.append("readiness[%d] refers to unknown slice %r" % (i, sid))
        elif r.get("ledger_version") != pinned[sid]:
            errs.append("readiness[%d] ledger_version %r differs from pinned %r for slice %r"
                        % (i, r.get("ledger_version"), pinned[sid], sid))
    return errs


def validate_artifact(obj):
    """CLI dispatch: slice-plan has 'slices'; readiness has 'state'."""
    if isinstance(obj, dict) and "slices" in obj:
        return validate_slice_plan(obj)
    if isinstance(obj, dict) and "state" in obj:
        return validate_readiness(obj)
    return ["not a slice-plan (needs 'slices') or slice-readiness (needs 'state')"]


if __name__ == "__main__":
    sys.exit(run_cli(validate_artifact, sys.argv[1:]))
