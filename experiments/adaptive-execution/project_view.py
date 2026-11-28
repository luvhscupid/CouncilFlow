"""Owner-readable generated project view (ADR 3.1/9 summary; migration step S11).
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Read-only: reads only the paths given, writes ONE Markdown file, no clock/env/git/network/service.
The view is never read back and is not a source of truth."""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import strict_load  # noqa: E402
import ledger as lg  # noqa: E402
import readiness as rd  # noqa: E402

try:
    import qa_trace as qa  # noqa: E402
except ImportError:  # T9 file optional
    qa = None

HEADER = ("GENERATED READ-ONLY VIEW - not a source of truth; the ledger and packets remain "
          "authoritative; edits to this file have no effect")
NP = "not provided"


def esc(x):
    """Inline-safe text: one line, no heading/table/link/HTML/code injection."""
    s = " ".join(str(x).split())
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = "".join("\\" + c if c in "\\`|[]*_~!#()" else c for c in s)
    return s


def _entry_lines(entries):
    return ["- `%s` (v%d, %s): %s" % (esc(e["id"]), e["version_introduced"], esc(e["status"]), esc(e["content"]))
            for e in sorted(entries, key=lambda e: e["id"])] or ["- none"]


def _check_list(obj, key, fields, name):
    errs = []
    items = obj.get(key) if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        return ["%s: %s must be a list" % (name, key)]
    for i, it in enumerate(items):
        if not (isinstance(it, dict) and all(isinstance(it.get(f), str) and it[f] for f in fields)):
            errs.append("%s[%d] needs nonempty string fields %s" % (name, i, fields))
    return errs


def render(ledger, slices=None, readiness=None, audit=None, qa_obj=None, limit=5):
    act = lg.active_entries(ledger)
    of = lambda t, st=None: [e for e in act if e["type"] == t and (st is None or e["status"] == st)]
    out = [HEADER, "", "## Current ledger", "",
           "- ledger_id: `%s`" % esc(ledger["ledger_id"]), "- ledger_version: %d" % ledger["ledger_version"], ""]
    for title, ents in (("Current goal", of("Goal")), ("Confirmed requirements", of("Requirement")),
                        ("Provisional assumptions", of("Assumption", "provisional")),
                        ("Open questions", of("Open"))):
        out += ["## " + title, ""] + _entry_lines(ents) + [""]
    sup = {s: e["id"] for e in ledger["entries"] for s in e["superseded_entry_ids"]}
    out += ["## Decision history", ""]
    decs = sorted((e for e in ledger["entries"] if e["type"] == "Decision"), key=lambda e: e["id"])
    for e in decs:
        by = sup.get(e["id"])
        out.append("- `%s` (v%d, %s): %s; superseded-by: %s" % (esc(e["id"]), e["version_introduced"],
                   esc(e["status"]), esc(e["content"]), "`%s`" % esc(by) if by else "none"))
    out += (["- none"] if not decs else []) + ["", "## Slice readiness and execution status", ""]
    ready = {r["slice_id"]: r["state"] for r in (readiness or [])}
    ex = rd.evaluate_slices(ledger, slices, {"unconfirmed_decision_limit": limit}) if slices is not None else {}
    ids = sorted(set(ready) | set(ex))
    if readiness is None:
        out.append("- readiness: " + NP)
    if slices is None:
        out.append("- execution status: " + NP)
    out += ["- `%s`: readiness=%s; execution=%s" % (esc(s), esc(ready.get(s, NP)), ex.get(s, NP)) for s in ids]
    out += ["", "## QA results", ""]
    if qa_obj is None:
        out.append("- QA results: " + NP)
    elif qa is None:
        out.append("- QA stale marks: not computed")
    else:
        recs = sorted(qa_obj["records"], key=lambda r: r["test_id"])
        stale = {s["test_id"]: s["reasons"] for s in qa.stale_results(ledger, recs)}
        for r in recs:
            m = "STALE (%s)" % esc(", ".join(stale[r["test_id"]])) if r["test_id"] in stale else "current"
            out.append("- `%s` slice `%s`: %s, pinned v%d, %s" % (esc(r["test_id"]), esc(r["slice_id"]),
                       esc(r["result"]), r["pinned_ledger_version"], m))
        out += [] if recs else ["- none"]
    out += ["", "## Audit findings", ""]
    if audit is None:
        out.append("- audit findings: " + NP)
    else:
        fs = sorted(audit, key=lambda f: f["id"])
        out += ["- `%s` [%s]: %s" % (esc(f["id"]), esc(f["severity"]), esc(f["summary"])) for f in fs] or ["- none"]
    out += ["", "## Unconfirmed default budget", "",
            "- %d of %d used" % (rd.active_unconfirmed_count(ledger), limit), ""]
    return "\n".join(out)


def _load(path, errs):
    try:
        return strict_load(path)
    except (OSError, ValueError) as e:
        errs.append("%s: %s" % (path, e))


def main(argv):
    ap = argparse.ArgumentParser()
    for k in ("ledger", "slices", "readiness", "qa", "audit", "out"):
        ap.add_argument("--" + k)
    ap.add_argument("--budget-limit", type=int, default=5)
    a = ap.parse_args(argv)
    errs = []
    if not a.ledger or not a.out:
        errs.append("--ledger and --out are required")
    if a.budget_limit < 0:
        errs.append("--budget-limit must be >= 0")
    ins = [p for p in (a.ledger, a.slices, a.readiness, a.qa, a.audit) if p]
    if a.out:
        if os.path.isdir(a.out):
            errs.append("--out is a directory")
        for p in ins:
            if os.path.exists(p) and os.path.exists(a.out) and os.path.samefile(p, a.out) \
                    or os.path.realpath(p) == os.path.realpath(a.out):
                errs.append("--out equals input %s" % p)
    L = S = R = Q = A = None
    if not errs:
        L = _load(a.ledger, errs)
        S, R, Q, A = (_load(p, errs) if p else None for p in (a.slices, a.readiness, a.qa, a.audit))
    if not errs:
        errs += lg.validate_ledger(L)
        if S is not None:
            try:
                rd.evaluate_slices(L, S, {"unconfirmed_decision_limit": a.budget_limit})
            except ValueError as e:
                errs.append("slices: %s" % e)
        if R is not None:
            errs += _check_list(R, "readiness", ["slice_id", "state"], "readiness")
        if A is not None:
            errs += _check_list(A, "findings", ["id", "summary", "severity"], "audit")
        if Q is not None and qa is not None:
            errs += qa.validate_qa_sidecar(Q, L)
        elif Q is not None and not (isinstance(Q, dict) and isinstance(Q.get("records"), list)):
            errs.append("qa: records must be a list")
    if errs:
        print(json.dumps({"valid": False, "errors": errs}))
        return 2
    R = R["readiness"] if isinstance(R, dict) else R
    A = A["findings"] if isinstance(A, dict) else A
    text = render(L, S, R, A, Q, a.budget_limit)
    with open(a.out, "wb") as f:
        f.write(text.encode("utf-8"))
    print(json.dumps({"valid": True, "errors": []}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
