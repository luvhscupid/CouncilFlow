# Project state (plain files)

Purpose: ADR-001 section 3 defines authoritative project state: a Planner-written
requirements ledger, a Manager-owned execution plan and evidence records. This
reference describes the plain-file form and its validator,
`scripts/project_state.py`. Plain files are the authoritative record. Codebase
Memory, where available, is only a lookup layer over them (Owner decision D5).

Status: `planner_contract.py readiness --project` uses it to check assumptions and the budget. The Manager procedure is in [workflow](workflow.md), section "Adaptive execution with project state".

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
`model_routing`. Evidence: `evidence_id`, `source_agent`, `finding`,
`artifacts` (path and sha256, not hash-checked), `ledger_ids`, `affected_slices`,
`created_at`, `reopen_request` (null, or status, contradiction, consequence). A
non-null reopen request needs ledger ids, affected slices and artifacts.

`model_routing` is null or an object keyed by role (`worker`, `tester`, `reviewer`).
Each value has exactly `hint` (string or null), `used` (string), `source` (`hint`,
`role_default` or `host`) and `reason` (nonempty). Source `hint` needs a non-null
`hint` equal to `used`. Error code: `slice_model_routing`.

## Packets that reference these files (version 1.1)

- `ledger.publish`: `ledger_ref` is a `ledger/L####.json` file.
- `evidence.reopen`: `evidence_ref` is an `evidence/E####.json` record and
  `evidence_id` its `E####` id; `ledger_ids` and `affected_slices` come from it.
- `job.assign` and `job.report`: `ledger_version` and `slice_id` name a ledger
  version and a plan slice.
- `approval.decision`: `owner_source_ref` is a `sources/S####.txt` file.
- `approval.request`: `operation_ref` may be a readiness answer; its `questions`
  are forwarded exactly.

## CLI

    python project_state.py init --project DIR [--budget N]
    python project_state.py source-add --project DIR --file F --received-at 2026-11-26T10:00:00Z
    python project_state.py bootstrap --project DIR --criteria frozen-criteria.json \
        --source-id S0001 [--goal TEXT] --created-at 2026-11-26T10:00:00Z
    python project_state.py validate --project DIR
    python project_state.py affected --project DIR --to-version M [--from-version N]

`affected` is read-only. It validates first, then lists `changed_entry_ids` (entries
new in M or with a different status than in N, default N = M - 1) and sorts plan
slices into `affected_slices` (pinned below M and citing a changed id or an id
superseded by a new entry), `unaffected_slices` and `closed_affected` (DONE or
CANCELLED slices that would be affected; their verification may be stale). Bad
versions fail with `bad_input`.

Output is one JSON object with `status` (PASS or FAIL) and `errors` (code, path,
detail). Exit 0 on PASS, 1 on FAIL, 2 on usage error. Existing files are never
overwritten (error code `exists`).

## Tester retests (ADR-001 M5)

    python project_state.py retest-select --project DIR --to-version M [--from-version N]
    python project_state.py retest-record --project DIR --slice S --to-version M \
        --result pass|fail --finding TEXT --artifact F [--artifact F ...] --oracle F \
        --route-used MODEL --route-source hint|role_default|host [--route-hint H] \
        --route-reason TEXT [--contradiction TEXT --consequence TEXT] --created-at TS

`retest-select` (read-only) returns `retest`: the `closed_affected` slices plus slices whose
retest failed for ledger version M, minus those with a recorded pass for M, and
`already_passed`. `retest-record` accepts only a slice in `retest`. A fail also sets that
slice's plan status to PAUSED and changes nothing else in `plan.json`; a pass leaves
`plan.json` alone. It writes two files: `evidence/E####.json` (source_agent `tester`,
`affected_slices` = [slice], `ledger_ids` from the slice pin, and a submitted reopen
request on a fail; none on a pass) and `retest/T####.json` (`slice_id`, `ledger_version`
M, `result`, `evidence_id`, `oracle` path and sha256, `model_routing` with one
`tester` choice, `created_at`). A fail needs `--contradiction` and `--consequence`; a pass
takes neither. Artifacts and the oracle must exist; their sha256 is recorded. The command
validates before and after writing. It never touches `ledger/`, and it touches `plan.json` only to pause a failed slice.
Validation checks each retest record against the evidence it cites: the source must
be `tester`, the slice must be listed, and pass and fail must match the reopen request.

## Technical Audit (ADR-001 M6)

    python project_state.py audit-select --project DIR --ledger-version N
    python project_state.py audit-record --project DIR --ledger-version N --entries FILE         --route-used MODEL --route-source hint|role_default|host [--route-hint H]         --route-reason TEXT --created-at TS

`audit-select` (read-only) reports whether the audit may run: N must be the latest ledger
version, every slice that is not CANCELLED must be DONE, and N must not be audited yet.
Blockers are returned as `not_eligible` errors. `FILE` is JSON with `entries` (one per
ledger ID of the audited slices: `ledger_id`, `verdict` pass|gap|risk, `kind`
none|implementation|requirement_change|owner_choice, `finding`, `slice_ids`, `consequence`)
and `reruns` (at least one deterministic check the Reviewer reran: `command`, `exit_code`,
`output` file). A pass has kind `none`; a gap or risk needs one of the other kinds.

Routing, one rule per finding kind:
- `implementation`: recorded in the audit only. No state changes.
- `requirement_change`: writes `evidence/E####.json` (source_agent `reviewer`, the
  cited ledger ID, the affected slices, a submitted reopen request with the finding as
  contradiction and the given consequence). The Planner decides whether the ledger
  changes. Plan and ledger are untouched.
- `owner_choice`: sets each affected slice to PAUSED (plan status only) and lists the
  finding in `owner_items`. The Manager presents it to the Owner.

`audit-record` writes `audit/A####.json` plus any reopen evidence and any owner pause. It
never writes the ledger. The audit is advisory: its record has no delivery or status field,
and a fully passing audit leaves plan statuses unchanged. Reviewer routing must not be Haiku.
Validation checks the record shape, routing rules, reopen evidence, owner items and reruns.

## Owner view (ADR-001 M7)

    python owner_view.py generate --project DIR [--output FILE] [--generated-at TS]
    python owner_view.py status --project DIR [--view FILE]

`generate` writes one static, read-only file, `owner-view.json` (schema `councilflow-owner-view`
1.0), built from the latest ledger version, `plan.json`, `retest/` and `audit/`. It shows the ADR-001
section 4 fields: goal, confirmed requirements, provisional assumptions, open questions, decision
history, ledger version (with the SHA-256 of that ledger file), slice readiness and status, QA
results (Tester retests), audit findings and default budget usage. The ledger stays the source of
truth. The generator never writes the ledger, the plan, evidence, retests, audits or sources and has no
way to record an Owner decision; the Owner answers through the Manager. The output must be
`DIR/owner-view.json` or a path outside the project, and may only replace an earlier Owner view
(error `write_refused`). Nothing runs it automatically; generate it on demand.

An open question's wording is the Open entry's `content`, unchanged. An optional
`questions/<question_id>.json` (a Planner question packet) adds its permitted default,
blocking flag, reversibility class and reason; the view says "no default is stored" otherwise.
Nothing writes `questions/` yet. `status` is read-only and reports `stale` when a newer ledger
version exists or the ledger file's bytes changed. `dashboard.py publish` embeds
`.councilflow/project/owner-view.json` with a stale marker computed from ledger file names only; the
board never opens the ledger.

## Limitations

Validation is structural. It does not authenticate who wrote a file, and role
ownership (Planner writes the ledger, Manager the plan) is an instruction-level
rule, not enforced here. It is not a database, runtime or transport.
