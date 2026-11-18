# Multi-agent evolution baseline

**Status:** Phase 0 read-only inventory, 2026-11-18. This report records repository evidence; it does not authorize live model trials, host configuration changes, permission changes, release, or promotion.

## Repository baseline

- Remote `origin/main` and local starting commit: `5d8eb8686c51c392c0689e04932758ca30a76f2d` (`docs: add non-normative multi-agent evolution research plan`).
- Working branch: `evolution/multi-agent-plan-2026-11-17`, created at that commit. Existing `work` branch remains at the same commit. No local `main` branch was present. No source changes were made during inventory.
- No other remote branches were queried beyond `HEAD` and `main`; overlapping PRs/open reviews were not observable from the available Git remote query.
- The repository has no root `LICENSE` file in the inspected tree. The plan's external-source license cautions remain open; no upstream source was copied.

## Gap inventory

| Area | Status | Evidence and boundary |
| --- | --- | --- |
| Role sequence and JSON contracts | `EXISTS_VERIFIED` (repository implementation) | `.agents/skills/council-flow/SKILL.md`, `references/message-contract.json`, `scripts/contracts.py`, role policies, and tests define the current Planner/Manager/Worker/Tester/Reviewer responsibilities. Static contracts do not authenticate native agent identity. |
| Original plan fidelity and candidate/evidence hashes | `EXISTS_VERIFIED` (contract/helper level) | `references/source-fidelity.md`, contracts, and workflow require source identity and evidence references. This does not establish host-enforced permissions. |
| Efficiency recorder, digest/expand, Codex and Claude adapters | `EXISTS_VERIFIED` (offline code and tests exist; live host use unverified) | Installed copies are under `.agents/skills/council-flow/scripts/efficiency/`; CLI is `scripts/efficiency.py`; implementation history is `experiments/agent-efficiency/IMPLEMENTATION-STATUS.md`. Existing documentation says no hooks or model calls are started by these tools. |
| Efficiency evaluation | `EXISTS_UNVERIFIED` for live outcomes; `MISSING` for authorization | Package D fixture/evaluator exists. `experiments/agent-efficiency/evaluation/PROTOCOL.md` is `DRAFT_NOT_AUTHORIZED`; live compatibility, quota and billing are `UNKNOWN`. |
| Model preference/capability schema and role router | `MISSING` as implemented capability | Existing adapter metadata separates configured/reported/effective identities, but this inventory found no opt-in per-role router or documented read-only capability registry. No secrets/configuration were inspected. |
| Durable transactional run journal and replay/reconciliation | `MISSING` | Recovery is instruction-level in `references/recovery.md`; it explicitly says retry/crash counts are not persistent runtime accounting. No SQLite/event store was identified. |
| Task DAG and isolated parallel mutation | `MISSING` as an enforced capability | Workflow/recovery require one mutating Worker per workspace; no scheduler or isolation enforcement was found. No advisory lock is treated as security. |
| Reviewed cross-run memory | `EXISTS_UNVERIFIED` / optional navigation only | Codebase Memory is an optional external MCP navigation aid documented in `references/codebase-memory.md`; it is not an authoritative decision journal or reviewed lesson store. Live MCP availability was not tested. |
| Deterministic doctor / diagnostics | `MISSING` as a user-facing diagnostic command | Existing validators and tests cover contracts and packages; no `council doctor` command/catalog was found. |
| Dashboard / observability projection | `MISSING` in this repository | No dashboard implementation directory or runtime event projection was identified. Plan calls this optional. |
| Workflow optimizer and model-council room | `MISSING` | These are future experiments/product-adjacent proposals, not current runtime features. |
| Native host activation | `EXISTS_UNVERIFIED` | Repository has Codex and Claude packaging and historical smoke evidence; this inventory did not invoke either host or claim new native verification. |

## Phase dependencies and current blockers

1. P1 can qualify existing offline components without rewriting them. Any A/B live trial remains blocked by the draft protocol's missing Owner-defined host/route, spend ceiling, stop mechanism and real independent Tester/Reviewer evidence.
2. P2 requires an explicit supported host capability and route policy. Offline schema/probe design can be prepared; live model comparisons and route changes remain gated.
3. P3 is a new local persistent-state behavior. Its state model and disposable prototype need a bounded storage/retention decision before integrating it into the skill.
4. P4 depends on P3 and actual host/OS isolation evidence. Default remains serial; no parallel mutating work is enabled.
5. P5 depends on stable journal/evidence semantics. Doctor logic can be deterministic; dashboard work is optional and no dashboard exists to extend.
6. P6 depends on approved baselines and reproducible oracles; it cannot self-promote or change frozen criteria.
7. P7 is separately optional and product-adjacent; no discussion service or external model execution is authorized by this inventory.

## Evidence limits

This is a source inspection against the current checked-out commit plus a read-only remote SHA query. No test suite, model, host CLI, credential/configuration, benchmark, upstream source, or permission boundary was exercised. Host-native capability and all usage/billing claims remain `UNVERIFIED` or `UNKNOWN`.
