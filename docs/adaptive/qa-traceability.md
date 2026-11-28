# QA traceability and stale-test computation (ADR 9)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

## What it is
A sidecar JSON artifact (kind `adaptive-qa-trace`) in which the Tester records, per test, the behavior tested, the
ledger entries it depends on, the slice, the ledger version it was pinned to, the result and an evidence ref.
`check_links` map Tester `checks[].name` to records. `stale_results` computes which results are no longer
trustworthy after the requirements ledger changed, and `retest_scope` lists only the affected tests to rerun.

## What a QA pass means
A QA pass certifies only the tested behavior against its recorded dependencies and pinned ledger version. It says
nothing about entries it does not list or about later ledger versions.

## What is preserved
The sidecar is referenced from the Tester job.report like any artifact. Tester and Reviewer duties are unchanged;
the closed checks shape `{name, status, evidence_ref}` is unchanged; the Reviewer still performs the independent
deterministic command rerun. No message type, field, role or route is added, and wire roles stay
worker/tester/reviewer/planner/manager. Default behavior is unchanged (adaptive mode is opt-in).

## Limits
Hand-written validation, standard library only, no network, no database. Staleness is advisory input to the Planner and Manager; it
approves nothing. Approvals stay in Council 001/R6 runtime state.

## Run
    python experiments/adaptive-execution/qa_trace.py SIDECAR.json            # validate
    python experiments/adaptive-execution/qa_trace.py stale LEDGER.json SIDECAR.json   # read-only
    python -m unittest discover -s experiments/adaptive-execution/tests
