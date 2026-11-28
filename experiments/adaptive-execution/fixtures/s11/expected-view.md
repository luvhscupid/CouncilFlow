GENERATED READ-ONLY VIEW - not a source of truth; the ledger and packets remain authoritative; edits to this file have no effect

## Current ledger

- ledger_id: `ledger-s11`
- ledger_version: 2

## Current goal

- `G1` (v1, established): Ship the export feature

## Confirmed requirements

- `R1` (v1, established): Export rows as CSV

## Provisional assumptions

- `A1` (v1, provisional): Default delimiter is a comma

## Open questions

- `O1` (v1, open): Which locale applies?

## Decision history

- `D1` (v1, provisional): Use UTF-8; superseded-by: `D2`
- `D2` (v2, provisional): Use UTF-8 with BOM; superseded-by: none

## Slice readiness and execution status

- `a`: readiness=READY; execution=CONTINUE
- `b`: readiness=PROCEED\_WITH\_ASSUMPTIONS; execution=PAUSED_BUDGET

## QA results

- `T-1` slice `a`: passed, pinned v2, current
- `T-2` slice `b`: failed, pinned v1, STALE (superseded:D1)

## Audit findings

- `F1` [high]: Missing test \| for R1
- `F2` [low]: Minor wording

## Unconfirmed default budget

- 2 of 5 used
