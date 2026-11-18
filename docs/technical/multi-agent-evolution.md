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
`PASS`, `FAIL`, `BLOCKED`, `SKIP`, and `UNVERIFIED`; missing native role evidence
is unverified and cannot become a pass.

## Task graph and reviewed experience

`scripts/task_graph.py` validates prerequisites, revisions, cycles and blocked
descendants. It returns a stable graph order but does not schedule or parallelize
work. `scripts/experience.py` validates manually Owner-reviewed lesson metadata
and filters by project scope/supersession. It does not ingest model output or
inject lessons into Worker context.

## Experimental journal

`experiments/multi-agent-evolution/journal.py` is an offline SQLite prototype.
It is intentionally outside the installed skill because current product tests
forbid SQLite in runtime code and no storage/retention policy has been qualified.
It stores state metadata and evidence references, not evidence content. It is
not a trusted authorization service and does not establish crash safety across
all filesystems or host environments.

## Current phase limits

- No live role/model routing, model trials, or Package D A/B experiment.
- No OS-enforced workspace isolation; parallel mutation remains disabled.
- No dashboard or independent-model council room was added.
- Native Codex/Claude activation and route identity remain unverified for this
  branch.
