# Multi-agent evolution helpers

This branch adds offline helpers based on the proposal in
[`docs/multi-agent-evolution-plan-2026-11-17/`](../multi-agent-evolution-plan-2026-11-17/).
They do not change the default role workflow or prove native host behavior.

## Role capability report

`scripts/role_capabilities.py` validates a versioned role preference object and
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

## Task graph and experience review claims

`scripts/task_graph.py` validates prerequisites, revisions, cycles and blocked
descendants. It returns a stable graph order but does not schedule or parallelize
work. `scripts/experience.py` validates review-claim metadata and filters by
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
- No OS-enforced workspace isolation; parallel mutation remains disabled.
- No dashboard or independent-model council room was added.
- Native Codex/Claude activation and route identity remain unverified for this
  branch.
