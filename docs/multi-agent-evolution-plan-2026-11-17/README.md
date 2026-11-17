# CouncilFlow: Multi-Agent Systems Evolution Plan

**Status:** RESEARCH_PLAN / PROPOSED / NON_NORMATIVE / NOT_AUTHORIZED_FOR_IMPLEMENTATION  
**Prepared:** 2026-11-17 (UTC+07)  
**Destination:** `docs/multi-agent-evolution-plan-2026-11-17/`  
**CouncilFlow baseline:** `main` at `6c4e4770876c8c86092c3cfca6ef83444adfae6e` when researched.  
**Source projects:** [Forge Orchestrator](https://github.com/nxtg-ai/forge-orchestrator), [Agyn introduction](https://agyn.io/blog/introducing-agyn), [Agyn original v1](https://github.com/agynio/v1), [Agyn current platform](https://github.com/agynio/platform), [MetaGPT](https://github.com/FoundationAgents/MetaGPT).

## Purpose

This is a CouncilFlow-specific, evidence-led plan to learn from three mature *ideas* and differently mature *implementations*: Forge's coordination, Agyn's runtime and evidence discipline, and MetaGPT's typed role artifacts and experimental workflow optimization.

**We are planning an improved installable workflow skill for Codex and Claude Code, NOT an autonomous product, replacement coding agent, model gateway, Kubernetes deployment, or change to the approved Council 001 architecture.** The role order, Owner authority, frozen acceptance and independent verification remain in force. The plan is not approval to code, install, buy model calls, change credentials, alter permissions, run benchmarks, push product code, or start a previously withheld implementation slice.

The controlling documents override any conflict here:
- [Root AGENTS.md](../../AGENTS.md), [current skill](../../.agents/skills/council-flow/SKILL.md), and [role policy](../../.agents/skills/council-flow/policies/roles.yaml).
- [Gate 3 Owner Charter](../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md), frozen Gate 3 experiment and existing Owner decisions.
- [Current workflow](../../.agents/skills/council-flow/references/workflow.md), [communication contract](../../.agents/skills/council-flow/references/communication.md), [recovery rules](../../.agents/skills/council-flow/references/recovery.md), [source-fidelity rules](../../.agents/skills/council-flow/references/source-fidelity.md).
- [Research status index](../research/README.md): historical research remains non-normative.

## Read in this order

1. [01 — Evidence and transfer decisions](01-EVIDENCE-AND-TRANSFER.md): what the three projects implement, limitations, licensing, and which ideas are compatible.
2. [02 — Target architecture and proposed contracts](02-ARCHITECTURE-AND-CONTRACTS.md): precise boundaries, workflow state, model routing, journal, context, memory, isolation, and UI.
3. [03 — Phased implementation roadmap](03-PHASED-DELIVERY.md): concrete work packages, prerequisites, outputs, acceptance and rollback.
4. [04 — Validation and comparative experiments](04-VALIDATION-AND-METRICS.md): reproducibility, safety controls, native-host evidence, baseline comparison, and how to use tokens wisely.
5. [05 — Risk register and decisions](05-RISKS-AND-DECISIONS.md): known failure modes, unresolved decisions, licensing, invariants, non-goals.
6. [06 — Execution backlog and acceptance matrix](06-EXECUTION-BACKLOG.md): bounded proposed tasks, dependencies, test oracles and review order.

## Executive decision

**Proposed priority order:** first finish *authorized* validation of the already existing optional Agent Efficiency helpers; then prototype capability-aware per-role model binding; then isolated durable-recovery state; then controlled dependency/parallel scheduling; then independently evaluated workflow optimization. Do not reimplement the existing toolkit, force automatic model downgrades, or introduce a server just for this plan.

The first live evaluation remains separately gated: `experiments/agent-efficiency/evaluation/PROTOCOL.md` is **DRAFT_NOT_AUTHORIZED**. A draft protocol is not permission to run it.

### Research findings mapped to CouncilFlow

| Idea | Upstream | CouncilFlow treatment |
| --- | --- | --- |
| Provider/model registry and per-role bindings | Agyn, MetaGPT | Optional host-capability routing; no assumption that OAuth subscription equals API use |
| Explicit task states, durable event log, task dependencies | Forge | Small bounded journal/graph experiment; do not claim exactly-once semantics |
| Separate control/runtime/telemetry data | Agyn | Keep host execution distinct from CouncilFlow evidence and UI projections |
| Context summary + referenced large outputs | Agyn | Reuse existing digest/expand; preserve original bytes and frozen criteria |
| Cost/usage attribution and guardrails | Agyn, MetaGPT | Meter observed facts with provenance and UNKNOWN for missing data |
| Typed agent artifacts / SOPs | MetaGPT | Extend existing validated JSON protocol only if gaps are proven |
| Verifier / negative controls / independent UAT | Forge, Agyn | Preserve stronger CouncilFlow Tester/Reviewer boundaries |
| Reconciliation, orphan detection, leases | Agyn | Recovery prototype; never silently reopen a previously completed attempt |
| Knowledge/experience memory | Forge, MetaGPT | Reviewed, tagged learnings for Manager/Planner, not unfiltered Worker memory |
| Offline workflow optimizer | MetaGPT AFlow | Candidate branches + fixed benchmarks + explicit Owner promotion |
| Multi-model discussion surface | Agyn threads, MetaGPT messages | Optional read-only independent submissions; no auto-approval |
| Health diagnostics | Forge doctor | Deterministic evidence-driven diagnostics; unknown != passing |

## Current product evidence at baseline

- Codex native skill and custom role workflow are packaged; Gate 3 Run 01 is **NATIVE_ROLE_WORKFLOW_PARTIAL** (E1, E2, E4 unverified, seven other checks passed).
- Claude Code plugin: one real `calc-001` smoke run reported **VERIFIED_ACCEPT** with native agents and an 11-message validated sequence. This does not establish broad compatibility.
- Model identity, effective gateway, cost/quota remain **UNKNOWN** unless individually evidenced. Codex/Claude offline adapters and digest helpers exist, opt-in, but live billing compatibility is **LIVE_UNVERIFIED**.
- The `main` SHA above includes the merged Slice 1 remediation. Its merge states native activation remains unverified in the Slice 1 release context and **Slice 2 was not authorized**. Don't treat this plan as reversal of that decision.
- Re-read HEAD and role policy before any future implementation. This plan snapshots a date, not a permanent claim about `main`.

## How to use this plan

An Owner may approve a *bounded phase* by specifying scope, execution environment, spending/permission limits and acceptance. The Manager may then break it into tasks that preserve frozen criteria; later phases remain only proposals. Commit and publish of these documents alone does not authorize anything else.

The preferred evaluation loop is **baseline -> candidate -> independent oracle -> evidence -> decision -> Owner-authorized promotion**. Stop if evidence is missing; record blocked/unverified instead of manufacturing a success state.
