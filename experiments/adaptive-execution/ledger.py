"""Versioned requirements ledger (ADR 3.1): schema validation, append-only check, promotion rule.
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Approvals live in Council 001/R6 runtime state (Owner decision D5); the ledger only carries
read-only artifact references to them and has no field that grants an approval."""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import is_iso_timestamp, run_cli  # noqa: E402

SCHEMA = "adaptive-1"
TYPES = ["Goal", "Requirement", "Assumption", "Constraint", "Decision", "Open"]
STATUS_BY_TYPE = {
    "Goal": ["established"], "Requirement": ["established"], "Constraint": ["established"],
    "Assumption": ["provisional", "confirmed", "rejected"],
    "Decision": ["provisional", "confirmed", "rejected"],
    "Open": ["open"],
}
# The eight ADR facets; "type and content" is one facet stored as two fields.
FACETS = ["id", "type", "content", "source_ids", "status", "timestamp", "version_introduced",
          "superseded_entry_ids", "affected_slices"]
AUTHORITIES = ["owner_confirmation", "preapproved_delegation_rule"]
TOP = ["schema_version", "ledger_id", "ledger_version", "author_role", "entries"]
_HEX = re.compile(r"^[0-9a-f]{64}$")


def _posint(x):
    return isinstance(x, int) and not isinstance(x, bool) and x > 0


def _str(x):
    return isinstance(x, str) and x.strip() != ""


def _strlist(x, nonempty):
    return isinstance(x, list) and (bool(x) or not nonempty) and all(_str(i) for i in x)


def _artifact_ref(r, where):
    if not isinstance(r, dict):
        return ["%s must be an artifact ref object" % where]
    errs = ["%s: unknown field %r" % (where, k) for k in r if k not in ("artifact_id", "path", "sha256", "kind")]
    for k in ("artifact_id", "path", "kind"):
        if not _str(r.get(k)):
            errs.append("%s.%s must be a nonempty string" % (where, k))
    p = r.get("path")
    if isinstance(p, str) and (p.startswith("/") or "\\" in p or ".." in p.split("/") or re.match(r"^[A-Za-z]:", p)):
        errs.append("%s.path must be repo-relative POSIX" % where)
    if not (isinstance(r.get("sha256"), str) and _HEX.match(r["sha256"])):
        errs.append("%s.sha256 must be lowercase hex sha256" % where)
    return errs


def _entry(e, i):
    w = "entries[%d]" % i
    if not isinstance(e, dict):
        return ["%s must be an object" % w]
    allowed = set(FACETS) | {"approval_ref", "promotion"}
    errs = ["%s: unknown field %r" % (w, k) for k in e if k not in allowed]
    errs += ["%s: missing facet %r" % (w, k) for k in FACETS if k not in e]
    t = e.get("type")
    if "type" in e and t not in TYPES:
        errs.append("%s.type must be one of %s" % (w, TYPES))
    for k in ("id", "content"):
        if k in e and not _str(e[k]):
            errs.append("%s.%s must be a nonempty string" % (w, k))
    if "source_ids" in e and not _strlist(e["source_ids"], True):
        errs.append("%s.source_ids must be a nonempty list of nonempty strings" % w)
    for k in ("superseded_entry_ids", "affected_slices"):
        if k in e and not _strlist(e[k], False):
            errs.append("%s.%s must be a list of nonempty strings" % (w, k))
    if "status" in e and t in STATUS_BY_TYPE and e["status"] not in STATUS_BY_TYPE[t]:
        errs.append("%s.status %r not allowed for %s (allowed %s)" % (w, e["status"], t, STATUS_BY_TYPE[t]))
    if "timestamp" in e and not is_iso_timestamp(e["timestamp"]):
        errs.append("%s.timestamp must be an ISO-8601 timestamp" % w)
    if "version_introduced" in e and not _posint(e["version_introduced"]):
        errs.append("%s.version_introduced must be a positive integer" % w)
    if "approval_ref" in e:
        if t != "Decision":
            errs.append("%s.approval_ref is only allowed on Decision entries" % w)
        errs += _artifact_ref(e["approval_ref"], w + ".approval_ref")
    if "promotion" in e:
        pr = e["promotion"]
        if t not in ("Requirement", "Decision"):
            errs.append("%s.promotion is only allowed on Requirement or Decision entries" % w)
        if not isinstance(pr, dict):
            errs.append("%s.promotion must be an object" % w)
        else:
            errs += ["%s.promotion: unknown field %r" % (w, k) for k in pr if k not in ("authority", "approval_ref")]
            if pr.get("authority") not in AUTHORITIES:
                errs.append("%s.promotion.authority must be one of %s" % (w, AUTHORITIES))
            if "approval_ref" not in pr:
                errs.append("%s.promotion.approval_ref is required" % w)
            else:
                errs += _artifact_ref(pr["approval_ref"], w + ".promotion.approval_ref")
    return errs


def validate_ledger(obj):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    errs = ["unknown field %r" % k for k in obj if k not in TOP]
    errs += ["missing field %r" % k for k in TOP if k not in obj]
    if "schema_version" in obj and obj["schema_version"] != SCHEMA:
        errs.append("schema_version must be %r" % SCHEMA)
    if "ledger_id" in obj and not _str(obj["ledger_id"]):
        errs.append("ledger_id must be a nonempty string")
    if "author_role" in obj and obj["author_role"] != "planner":
        errs.append("author_role must be 'planner' (Planner is the sole semantic writer)")
    if "ledger_version" in obj and not _posint(obj["ledger_version"]):
        errs.append("ledger_version must be a positive integer")
    entries = obj.get("entries")
    if "entries" in obj and (not isinstance(entries, list) or not entries):
        errs.append("entries must be a nonempty list")
    if not isinstance(entries, list):
        return errs
    for i, e in enumerate(entries):
        errs += _entry(e, i)
    seen = {}
    prev = 0
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            continue
        eid, v = e.get("id"), e.get("version_introduced")
        if _str(eid):
            if eid in seen:
                errs.append("entries[%d]: duplicate id %r" % (i, eid))
            else:
                seen[eid] = e
        if _posint(v):
            if v < prev:
                errs.append("entries[%d]: version_introduced %d decreases (must be non-decreasing)" % (i, v))
            prev = max(prev, v)
        sup = e.get("superseded_entry_ids")
        if not isinstance(sup, list):
            continue
        for s in sup:
            tgt = seen.get(s) if isinstance(s, str) else None
            if tgt is None or tgt is e:
                errs.append("entries[%d]: supersedes unknown or later entry id %r" % (i, s))
                continue
            if _posint(v) and _posint(tgt.get("version_introduced")) and tgt["version_introduced"] >= v:
                errs.append("entries[%d]: supersedes %r which is not of a lower version" % (i, s))
            if (tgt.get("type") == "Assumption" and e.get("type") in ("Requirement", "Decision")
                    and "promotion" not in e):
                errs.append("entries[%d]: Assumption %r promoted without a promotion block "
                            "(owner_confirmation or preapproved_delegation_rule plus approval_ref)" % (i, s))
    if _posint(obj.get("ledger_version")) and prev and obj["ledger_version"] != prev:
        errs.append("ledger_version %r must equal max version_introduced %d" % (obj["ledger_version"], prev))
    return errs


def active_entries(ledger):
    entries = ledger.get("entries", [])
    dead = {s for e in entries for s in e.get("superseded_entry_ids", [])}
    return [e for e in entries if e.get("id") not in dead]


def _canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def check_append_only(old, new):
    old_e, new_e = old.get("entries"), new.get("entries")
    if not isinstance(old_e, list) or not isinstance(new_e, list):
        return ["entries must be lists in both ledgers"]
    errs = []
    if old.get("ledger_id") != new.get("ledger_id"):
        errs.append("ledger_id changed")
    ov, nv = old.get("ledger_version"), new.get("ledger_version")
    if not (_posint(ov) and _posint(nv)) or nv < ov:
        errs.append("ledger_version must not decrease (%r -> %r)" % (ov, nv))
    if len(new_e) < len(old_e):
        errs.append("entries deleted: %d -> %d" % (len(old_e), len(new_e)))
    for i, o in enumerate(old_e[:len(new_e)]):
        if _canon(o) != _canon(new_e[i]):
            errs.append("entries[%d] is not identical to the old ledger (edited, reordered or replaced; "
                        "use a new superseding entry)" % i)
    return errs


if __name__ == "__main__":
    sys.exit(run_cli(validate_ledger, sys.argv[1:]))
