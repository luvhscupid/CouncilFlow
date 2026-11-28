"""QA/audit traceability sidecar and stale-test computation (ADR 9).
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Sidecar artifact kind 'adaptive-qa-trace'; Tester/Reviewer duties and the closed checks shape are unchanged."""
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import is_iso_timestamp, strict_load, run_cli  # noqa: E402
from ledger import SCHEMA, _artifact_ref, _posint, _str  # noqa: E402

RESULTS = ["passed", "failed", "blocked", "unverified"]
FIELDS = ["test_id", "tested_behavior", "ledger_ids", "slice_id", "pinned_ledger_version",
          "result", "evidence", "timestamp"]
TOP = ["schema_version", "candidate_ref", "records", "check_links"]


def _record(r, i):
    w = "records[%d]" % i
    if not isinstance(r, dict):
        return ["%s must be an object" % w]
    errs = ["%s: unknown field %r" % (w, k) for k in r if k not in FIELDS]
    errs += ["%s: missing field %r" % (w, k) for k in FIELDS if k not in r]
    for k in ("test_id", "tested_behavior", "slice_id"):
        if k in r and not _str(r[k]):
            errs.append("%s.%s must be a nonempty string" % (w, k))
    ids = r.get("ledger_ids")
    if "ledger_ids" in r and not (isinstance(ids, list) and ids and all(_str(x) for x in ids)):
        errs.append("%s.ledger_ids must be a nonempty list of nonempty strings" % w)
    if "pinned_ledger_version" in r and not _posint(r["pinned_ledger_version"]):
        errs.append("%s.pinned_ledger_version must be a positive integer" % w)
    if "result" in r and r["result"] not in RESULTS:
        errs.append("%s.result must be one of %s" % (w, RESULTS))
    if "evidence" in r:
        errs += _artifact_ref(r["evidence"], w + ".evidence")
    if "timestamp" in r and not is_iso_timestamp(r["timestamp"]):
        errs.append("%s.timestamp must be an ISO-8601 timestamp with timezone" % w)
    return errs


def validate_qa_sidecar(obj, ledger=None):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    errs = ["unknown field %r" % k for k in obj if k not in TOP]
    errs += ["missing field %r" % k for k in TOP if k not in obj]
    if "schema_version" in obj and obj["schema_version"] != SCHEMA:
        errs.append("schema_version must be %r" % SCHEMA)
    if obj.get("candidate_ref") is not None and "candidate_ref" in obj:
        errs += _artifact_ref(obj["candidate_ref"], "candidate_ref")
    recs = obj.get("records")
    if "records" in obj and not isinstance(recs, list):
        errs.append("records must be a list")
        recs = None
    ids = set()
    for i, r in enumerate(recs or []):
        errs += _record(r, i)
        t = r.get("test_id") if isinstance(r, dict) else None
        if _str(t):
            if t in ids:
                errs.append("records[%d]: duplicate test_id %r" % (i, t))
            ids.add(t)
    if ledger is not None and isinstance(ledger, dict):
        known = {e.get("id") for e in ledger.get("entries", []) if isinstance(e, dict)}
        lv = ledger.get("ledger_version")
        for i, r in enumerate(recs or []):
            if not isinstance(r, dict):
                continue
            for lid in r.get("ledger_ids") if isinstance(r.get("ledger_ids"), list) else []:
                if lid not in known:
                    errs.append("records[%d]: ledger id %r not in ledger" % (i, lid))
            p = r.get("pinned_ledger_version")
            if _posint(p) and _posint(lv) and p > lv:
                errs.append("records[%d]: pinned_ledger_version %d exceeds ledger_version %d" % (i, p, lv))
    links = obj.get("check_links")
    if "check_links" in obj:
        if not isinstance(links, list):
            errs.append("check_links must be a list")
        else:
            for i, c in enumerate(links):
                w = "check_links[%d]" % i
                if not isinstance(c, dict):
                    errs.append("%s must be an object" % w)
                    continue
                errs += ["%s: unknown field %r" % (w, k) for k in c if k not in ("check_name", "test_id")]
                for k in ("check_name", "test_id"):
                    if not _str(c.get(k)):
                        errs.append("%s.%s must be a nonempty string" % (w, k))
                if _str(c.get("test_id")) and recs is not None and c["test_id"] not in ids:
                    errs.append("%s: unknown test_id %r" % (w, c["test_id"]))
    return errs


def stale_results(ledger, qa_records):
    """Read-only. A record is stale if one of its ledger_ids was superseded at a version above its pin;
    a superseded Goal also stales records of the Goal's affected_slices ('goal_changed')."""
    entries = ledger.get("entries", [])
    by_id = {e["id"]: e for e in entries}
    sup = []  # (superseded id, superseding version)
    for e in entries:
        for s in e.get("superseded_entry_ids", []):
            sup.append((s, e["version_introduced"]))
    out = []
    for r in qa_records:
        pin, why = r["pinned_ledger_version"], set()
        for s, v in sup:
            if v <= pin:
                continue
            if s in r["ledger_ids"]:
                why.add("superseded:%s" % s)
            g = by_id.get(s)
            if g and g.get("type") == "Goal" and r["slice_id"] in g.get("affected_slices", []):
                why.add("goal_changed")
        if why:
            out.append({"test_id": r["test_id"], "stale": True, "reasons": sorted(why)})
    return sorted(out, key=lambda x: x["test_id"])


def retest_scope(stale):
    return sorted(s["test_id"] for s in stale)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "stale":
        if len(a) != 3:
            print(json.dumps({"error": "usage: stale LEDGER.json SIDECAR.json"}))
            sys.exit(2)
        try:
            led, sc = strict_load(a[1]), strict_load(a[2])
        except (OSError, ValueError) as e:
            print(json.dumps({"error": "cannot load: %s" % e}))
            sys.exit(2)
        errs = validate_qa_sidecar(sc, led)
        if errs:
            print(json.dumps({"valid": False, "errors": errs}))
            sys.exit(2)
        st = stale_results(led, sc["records"])
        print(json.dumps({"stale": st, "retest_scope": retest_scope(st)}))
        sys.exit(0)
    sys.exit(run_cli(validate_qa_sidecar, a))
