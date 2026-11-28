# Readiness, discovery cap and default budget (S8)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

What it is: `experiments/adaptive-execution/readiness.py` adds, for adaptive mode only, the
PROCEED_WITH_ASSUMPTIONS readiness state (tied to active provisional ledger entries), a cap of two
Planner discovery cycles per slice (a third returns `escalate_scope_question`), a derived count of
active unconfirmed Assumption/Decision entries checked against an Owner-approved limit (default 5,
configurable, 0 valid), and the five decision classes with a no-downgrade check.

Preserved: default mode keeps READY/NEEDS_INFORMATION/BLOCKED; wire roles and message contract 1.0
are untouched; Owner approvals stay in existing Council 001/R6 runtime state and the ledger holds
only read-only references; blocking decisions are never downgraded by budget.

Limits: pure functions only, no persistence, no enforcement in the real workflow; the minimum class
for a decision must be supplied by the caller.

Run: `python experiments/adaptive-execution/readiness.py BUNDLE.json` (exit 0 valid, 2 invalid), and
`python -m unittest discover -s experiments/adaptive-execution/tests`.
