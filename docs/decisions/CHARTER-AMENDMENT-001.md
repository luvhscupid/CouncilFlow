# Owner Charter amendment 001

Amends: [`docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`](../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md)
Authority: Owner decisions D1 and D4, 2026-11-26 ([record](ADR-001-owner-decisions.md)),
under [ADR-001](ADR-001-adaptive-execution.md).

The Charter file itself is unchanged. It is part of the hash-locked Gate 3 v0.2
record (`SHA256SUMS.txt`) and stays as history. Where the Charter and this
amendment differ, this amendment controls. Everything else in the Charter is
unchanged.

## Superseded clauses

| Charter clause | Replaced by |
|---|---|
| "Only the Planner or Manager sends routine plain-English output to the Owner." | Only the Manager communicates with the Owner. The Planner never addresses the Owner directly; its questions reach the Owner through the Manager with their exact wording. (D1) |
| Owner "Submits frozen criteria once." / Planner "holds the Owner's frozen plan/criteria verbatim" | Requirements may change through controlled reassessment in a versioned, append-only ledger. Each change needs the right authority (ADR-001 sections 3 and 5). The Planner still may not silently rewrite, weaken, omit or add requirements; every change is a new ledger version that cites its source. Verbatim fidelity applies to the Owner's original source records and to each ledger version. (D1) |
| Reviewer "**Not a mandatory UX scorer.**" (scope of the Reviewer) | The Reviewer also assesses whether the delivered system meets the current Goal, as evidence for the Manager and Owner, not as acceptance authority. It is still not a general UX scorer. (D4) |

## Unchanged

- Role order: Owner → Planner → Manager → Worker → Tester → Reviewer → Manager →
  Planner → Owner. The final step reaches the Owner through the Manager.
- The Reviewer's independent rerun of a Tester-declared deterministic command,
  comparing exit code and normalized-stdout SHA-256, stays mandatory.
- The Manager does not code; the Worker implements; the Tester records executable
  evidence; the Owner does not relay messages between agents.
- Gate 3 v0.2 records stay frozen as the record of that experiment.

## Status

This amendment records decisions. It does not change how the skill behaves today.
The skill files (`.agents/skills/council-flow/`) change only in later steps (M1 to
M8), and each step needs its own Owner go-ahead.
