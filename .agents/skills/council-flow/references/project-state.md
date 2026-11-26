# Project state (plain files)

Purpose: ADR-001 section 3 defines authoritative project state: a Planner-written
requirements ledger, a Manager-owned execution plan and evidence records. This
reference describes the plain-file form and its validator,
`scripts/project_state.py`. Plain files are the authoritative record. Codebase
Memory, where available, is only a lookup layer over them (Owner decision D5).

Status: `planner_contract.py readiness --project` uses it (M2) to check assumptions and the budget. Later steps (M3, M4) wire in the rest.

## Layout (normally `.councilflow/project/`)

- `project.json`: `{"schema": "councilflow-project", "version": "1.0", "default_budget": 5}`
- `sources/S0001.txt` and `S0001.json`: immutable Owner source. The record holds
  `source_id`, `kind`, `received_at` (ISO-8601 UTC, Z or +00:00), `path`, and the
  `sha256` of the .txt bytes exactly as stored.
- `ledger/L0001.json`, `L0002.json`, ...: one full file per ledger version.
- `plan.json` (optional) and `evidence/E0001.json`, ... (optional).

Numbering is contiguous from 1 with no gaps.

## Ledger version

`schema`, `version` ("1.0"), `ledger_version`, `previous_sha256` (null for version 1,
else SHA-256 of the previous file's raw bytes), `created_at`, `entries`.

Entry keys, exactly: `id`, `type` (Goal, Requirement, Assumption, Constraint,
Decision, Open), `content`, `source_ids`, `evidence_ids`, `status`, `created_at`,
`version_introduced`, `supersedes`, `affected_slices`. `source_ids` may be empty
only when `evidence_ids` is not.

Status: Assumption is unconfirmed, confirmed, rejected or superseded. Open is open,
resolved or superseded. Everything else is active or superseded.

## Rules

- Append-only: each entry of version N appears in N+1 unchanged except `status`.
- Allowed moves: unconfirmed to confirmed, rejected or superseded; open to resolved
  or superseded; active to superseded. Nothing is revived.
- An entry becomes superseded only when an entry introduced in the same version
  lists it in `supersedes`; each superseded id must exist in the previous version.
- No silent promotion: confirming or rejecting an Assumption, or a Requirement that
  supersedes one, needs a Decision introduced in that version with existing sources.
- Every source id must exist with a matching hash; every evidence id must exist.
- Budget: `used` is the number of unconfirmed Assumptions in the latest version,
  `limit` is `default_budget`. Exceeding it is reported (`exceeded: true`) and is not
  a validation error; enforcement belongs to the Manager.

## Plan and evidence

Plan slices: `slice_id`, `ledger_version`, `ledger_ids` (must exist in that version),
`depends_on` (acyclic), `readiness`, `status`, `run_dir` (relative, no `..`),
`model_routing` (not interpreted). Evidence: `evidence_id`, `source_agent`, `finding`,
`artifacts` (path and sha256, not hash-checked), `ledger_ids`, `affected_slices`,
`created_at`, `reopen_request` (null, or status, contradiction, consequence). A
non-null reopen request needs ledger ids, affected slices and artifacts.

## CLI

    python project_state.py init --project DIR [--budget N]
    python project_state.py source-add --project DIR --file F --received-at 2026-11-26T10:00:00Z
    python project_state.py bootstrap --project DIR --criteria frozen-criteria.json \
        --source-id S0001 [--goal TEXT] --created-at 2026-11-26T10:00:00Z
    python project_state.py validate --project DIR

Output is one JSON object with `status` (PASS or FAIL) and `errors` (code, path,
detail). Exit 0 on PASS, 1 on FAIL, 2 on usage error. Existing files are never
overwritten (error code `exists`).

## Limitations

Validation is structural. It does not authenticate who wrote a file, and role
ownership (Planner writes the ledger, Manager the plan) is an instruction-level
rule, not enforced here. It is not a database, runtime or transport.
