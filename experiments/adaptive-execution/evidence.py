"""Evidence records and Reopen Requests (ADR 3.3 and 7): validation and reopen classification.
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Records only REFERENCE ledger ids; nothing here returns or writes a modified ledger."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import is_iso_timestamp, run_cli  # noqa: E402
from ledger import _artifact_ref, _str, _strlist, validate_ledger  # noqa: E402

WIRE_ROLES = ["worker", "tester", "reviewer", "planner", "manager"]
REOPEN_STATUSES = ["none", "submitted", "valid_for_reopen", "retained_as_evidence_only",
                   "decided_ledger_changed", "decided_no_change"]
EVIDENCE_FIELDS = ["evidence_id", "source_agent", "observation", "artifacts", "ledger_ids",
                   "affected_slices", "timestamp", "reopen_status"]
REQUEST_FIELDS = ["request_id", "submitter_role", "ledger_entry_ids", "contradiction_or_affected_assumption",
                  "supporting_evidence_ids", "affected_slices", "consequence"]


def _shape(obj, fields):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    # Any extra key (e.g. new_requirement, ledger_change, decision, supersedes) is rejected here.
    return (["unknown field %r (records may only reference ledger ids)" % k for k in obj if k not in fields]
            + ["missing field %r" % k for k in fields if k not in obj])


def validate_evidence(obj):
    errs = _shape(obj, EVIDENCE_FIELDS)
    if not isinstance(obj, dict):
        return errs
    for k in ("evidence_id", "observation"):
        if k in obj and not _str(obj[k]):
            errs.append("%s must be a nonempty string" % k)
    if "source_agent" in obj and obj["source_agent"] not in WIRE_ROLES:
        errs.append("source_agent must be one of %s (display aliases are rejected)" % WIRE_ROLES)
    if "artifacts" in obj:
        if not isinstance(obj["artifacts"], list):
            errs.append("artifacts must be a list")
        else:
            for i, a in enumerate(obj["artifacts"]):
                errs += _artifact_ref(a, "artifacts[%d]" % i)
    for k in ("ledger_ids", "affected_slices"):
        if k in obj and not _strlist(obj[k], False):
            errs.append("%s must be a list of nonempty strings" % k)
    if "timestamp" in obj and not is_iso_timestamp(obj["timestamp"]):
        errs.append("timestamp must be an ISO-8601 timestamp with timezone")
    if "reopen_status" in obj and obj["reopen_status"] not in REOPEN_STATUSES:
        errs.append("reopen_status must be one of %s" % REOPEN_STATUSES)
    return errs


def validate_reopen_request(obj):
    """Structural check only; whether it is valid FOR REOPENING is classify_reopen's decision."""
    errs = _shape(obj, REQUEST_FIELDS)
    if not isinstance(obj, dict):
        return errs
    for k in ("request_id", "contradiction_or_affected_assumption", "consequence"):
        if k in obj and not _str(obj[k]):
            errs.append("%s must be a nonempty string" % k)
    if "submitter_role" in obj and obj["submitter_role"] not in WIRE_ROLES:
        errs.append("submitter_role must be one of %s (display aliases are rejected)" % WIRE_ROLES)
    for k in ("ledger_entry_ids", "supporting_evidence_ids", "affected_slices"):
        if k in obj and not _strlist(obj[k], False):
            errs.append("%s must be a list of nonempty strings" % k)
    return errs


def classify_reopen(request, ledger):
    """Return (status, reasons). Never modifies request or ledger (ADR 7: submitting changes nothing)."""
    reasons = validate_reopen_request(request)
    lerrs = validate_ledger(ledger)
    reasons += ["ledger invalid: %s" % e for e in lerrs]
    if isinstance(request, dict) and not lerrs:
        if not request.get("ledger_entry_ids"):
            reasons.append("no ledger entry id cited")
        else:
            known = {e["id"] for e in ledger["entries"]}
            if not any(i in known for i in request["ledger_entry_ids"]):
                reasons.append("no cited ledger entry id exists in the supplied ledger")
        for k, why in (("contradiction_or_affected_assumption", "no contradiction or affected assumption named"),
                       ("supporting_evidence_ids", "no supporting evidence"),
                       ("affected_slices", "no affected slices identified"),
                       ("consequence", "no consequence stated")):
            if not request.get(k) or (isinstance(request[k], str) and not request[k].strip()):
                reasons.append(why)
    reasons = list(dict.fromkeys(reasons))
    return ("retained_as_evidence_only", reasons) if reasons else ("valid_for_reopen", [])


def validate_any(obj):
    if isinstance(obj, dict) and "request_id" in obj:
        return validate_reopen_request(obj)
    return validate_evidence(obj)


if __name__ == "__main__":
    sys.exit(run_cli(validate_any, sys.argv[1:]))
