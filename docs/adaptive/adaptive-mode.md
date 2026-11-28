# Adaptive mode (opt-in plan-ownership split)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Step S4, Owner decision D3.

## What it is

Two standalone JSON artifacts (schema `adaptive-1`): a **slice-plan** authored by the
Manager (slices, dependencies, role assignment, advisory model routing, status, pinned
ledger version) and a per-slice **slice-readiness** authored by the Planner
(READY / NEEDS_INFORMATION / BLOCKED, with optional Planner-authored task instructions).
Field rules: `experiments/adaptive-execution/schemas/adaptive-mode.md`.

## What is preserved

- Adaptive mode is opt-in. Mode `default` means the existing `planner.md` /
  `planner_contract.py` path, unchanged; a default plan must have no slices.
- Message contract 1.0 is untouched: no new message type, field, role or route. Wire
  roles stay worker/tester/reviewer/planner/manager (display aliases are invalid on the wire).
- Planner-authored instructions stay Planner-authored. The module imports nothing from `plugins/`.
- Owner approvals/waivers are not stored here (D5); no SQLite (D6).

## Limits

Validators check structure and coherence only. They do not run or schedule anything,
and nothing in the skill calls them yet. PROCEED_WITH_ASSUMPTIONS arrives with step S8.

## Run

    python experiments/adaptive-execution/adaptive_mode.py FILE      # exit 0 valid, 2 invalid
    python -m unittest discover -s experiments/adaptive-execution/tests
