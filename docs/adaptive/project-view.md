# Generated project view (S11)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

**Deviation disclosure (Manager decision):** the migration plan says "extend the existing dashboard".
That would edit `plugins/.../scripts/dashboard.py`, which is forbidden in this batch. Instead this step
is a NEW standalone read-only generator, `experiments/adaptive-execution/project_view.py`.

## What it is
A deterministic generator that renders one self-contained Markdown file for the Owner from the
ledger (T5), optional slices/readiness (T8), optional QA sidecar (T9, stale marks via
`qa_trace.stale_results`; if `qa_trace.py` is absent it prints "QA stale marks: not computed") and an
optional audit file `{findings:[{id, summary, severity}]}`. Readiness file: `{readiness:[{slice_id, state}]}`.

## What is preserved
- The view is never a source of truth and is never read back; ledger and packets stay authoritative.
- No new message type, field, role or route. The view adds no Planner-Owner channel; the Manager-only
  conversational boundary is unchanged (ADR L218).
- Owner approvals stay in Council 001/R6 runtime state (D5); the view only displays ledger data.
- Read-only: reads only the given paths; no clock, environment, git, network access or service.

## Limits
Invalid ledger or optional inputs are refused (exit 2, nothing written). `--out` equal to an input, or a
directory, is refused. Text is escaped (pipes, `#`, backticks, angle brackets, brackets) and flattened to one
line, so entry content cannot inject headings, tables, links or HTML. Output is byte-stable (UTF-8, LF,
sorted by id, no generated timestamp).

## Run
    python experiments/adaptive-execution/project_view.py --ledger L.json [--slices S.json] [--readiness R.json] [--qa Q.json] [--audit A.json] [--budget-limit N] --out VIEW.md

Default budget limit is 5. Golden example: `experiments/adaptive-execution/fixtures/s11/expected-view.md`.
Tests: `python -m unittest discover -s experiments/adaptive-execution/tests`.
