# Multi-agent evolution helpers

This branch adds offline helpers based on the proposal in
[`docs/multi-agent-evolution-plan-2026-11-17/`](../multi-agent-evolution-plan-2026-11-17/).
They do not change the default role workflow or prove native host behavior.

On 2026-11-24 (cleanup slice 5) the helpers that no workflow step called were
taken out of the shipped skill. `role_capabilities.py` and `experience.py` now
live in `experiments/multi-agent-evolution/` next to `journal.py`; their tests
stay in `tests/` but are not packed into the release archive. `task_graph.py`
was removed, because the Plan contract (`scripts/planner_contract.py`) already
rejects unknown dependencies and cycles for every plan. They came from backlog
items CF-M20, CF-O50 and CF-G40 of the evolution proposal, which is not
authorized to execute, and no frozen Gate 3 record names them.

## Role capability report

`experiments/multi-agent-evolution/role_capabilities.py` validates a versioned role preference object and
combines it with explicitly supplied capability metadata. Capability input is
caller-reported, so `capability_status` remains `UNKNOWN`. It never inspects host
configuration or starts a model. `effective_model` and `route_verified` remain
unknown/false; selection remains `INHERIT_HOST` because no documented host
adapter was observed in this environment.

## Doctor

Run `python .agents/skills/council-flow/scripts/doctor.py evidence.json` or pipe
JSON to `python .agents/skills/council-flow/scripts/doctor.py -`. The input is
explicit evidence, not auto-discovered host state. Output statuses are
`PASS`, `FAIL`, `BLOCKED`, `SKIP`, and `UNVERIFIED`. Schema validation and a
SHA-256 comparison against bytes read from a relative path under the evidence
file's directory (or the current directory for stdin) can pass. Missing required
references are blocked; malformed data and digest mismatches fail. Declared role
labels and native-session references remain unverified because this CLI cannot
authenticate native host sessions. A pass proves only the local check named in
that result.

Schema v1 keeps its existing result shape. Schema v2 requires nullable
`executable_artifact` (`path`, `sha256`) and `native_host` (`name`, `version`,
`evidence_ref`) fields. `executable_integrity` hashes stable regular-file bytes
under the explicit evidence root and never executes the path. `native_host`
records remain caller claims and return `UNVERIFIED`; null evidence is
`BLOCKED`, malformed records or digest mismatches are `FAIL`. Symlink and FIFO
references are not read.
The v1 output shape remains stable; artifact checks now reject symlinks without
following them, including links that resolve within the evidence root.

## Task graph and experience review claims

`scripts/task_graph.py` validated prerequisites, revisions, cycles and blocked
descendants; it was removed in favor of the Plan contract's dependency checks.
`experiments/multi-agent-evolution/experience.py` validates review-claim metadata and filters by
project scope/supersession. Its `review_claim` is caller-supplied, and every entry is
returned with `review_status: UNVERIFIED`. It does not authenticate Owner
review, ingest model output, or inject lessons into Worker context.

## Experimental journal

`experiments/multi-agent-evolution/journal.py` is an offline SQLite prototype.
It is intentionally outside the installed skill because current product tests
forbid SQLite in runtime code and no storage/retention policy has been qualified.
Schema v2 stores allowlisted event metadata, opaque evidence references, attempt
and parent-event identity, and optional rooted candidate-artifact descriptors.
`verify_run` checks local event-chain consistency and candidate bytes beneath an
explicit evidence root; `reconcile` is read-only and never dispatches or replays
work. Legacy v1 databases remain unchanged and can only be opened read-only for
export. Actor/session and approval fields are claims and stay `UNVERIFIED`.
This prototype is not a trusted authorization or native-session service, and
cross-platform crash recovery remains unverified.

## Current phase limits

- No live role/model routing, model trials, or Package D A/B experiment.
- P4 isolation remains `ISOLATION_BLOCKED`; the DAG helper does not schedule tasks.
  Codex sandbox tooling and `bwrap` are present, but no worker-specific deny
  policy or cross-workspace test evidence is available. Serial mutation remains
  in force.
- P5 doctor v2 adds local executable-byte integrity and structural native-host
  references only. Experience entries remain metadata filters labeled
  `UNVERIFIED`; no Worker-context injection is implemented. The optional local
  dashboard reads supplied run packets and user-selected JSON files, and presents
  packet-derived status without authenticating senders or granting approval.
  Its original LIVE-01–LIVE-04 acceptance remains `UNVERIFIED`: the fresh
  attempt has deterministic unit evidence, but the supported browser could not
  be inspected and no live CouncilFlow role chain was observed.
- P6 live optimization is `BLOCKED_OWNER_INPUT`; the synthetic evaluator is
  descriptive offline analysis and does not authorize a model call or promotion.
- No independent-model council room was added.
- Native Codex/Claude activation and route identity remain unverified for this
  branch.
