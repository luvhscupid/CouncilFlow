# Agent Efficiency Toolkit — phased implementation plan (draft)

> **Status:** DRAFT / READY FOR OWNER REVIEW. Planning only; **no implementation authorized by this document**.  
> **Prepared:** 2026-11-15, for Owner execution when back at the Windows PC.  
> **Repository:** `luvhscupid/CouncilFlow`. Repository state inspected on `main` at `990cbc67987d50969e07577aff6b36cbaa14dc9f`; recheck at execution time.  
> **Goal:** A small **opt-in**, provider/harness-neutral efficiency toolkit useful with **Codex** and **Claude Code routed through xKiro** now, with the ability to add adapters later. Do not pretend this already works.  
> **Research source:** [AI Agent Token & Context Efficiency](AI-Agent-Token-and-Context-Efficiency-2026-11-15.md). This draft converts possible experiments into bounded implementation tasks and does not alter that closed research or its authority boundary.

## 0. What we know and must preserve

Current repo is a Codex-native skill with `.agents/skills/council-flow/`, `.codex/agents/`, JSON message validation, test suites, and a separate **frozen Gate 3** activation experiment. It is not already a universal Claude Code plugin or a trusted Supervisor. Its docs contain historical role definitions that conflict with newer Owner authority. The **Gate 3 Owner Charter**, `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`, supersedes older UX-Reviewer text; Reviewer is the **three-way Worker/Tester/Owner-plan comparator**, including an independent deterministic command rerun, **not a mandatory UX scorer**. Never resolve this discrepancy by silently editing the frozen charter or running a new audit as a substitute for work.

Frozen Gate 3 forbids changing skill/config/policy in its experiment; keep its candidate and experiment workspace separate. This toolkit is **not Gate 3**. It must not claim to enforce authorization, access controls, sandboxing, evidence authenticity or completion quality that native hosts do not expose.

**Do not edit** `docs/gate3/`, the frozen Owner Charter, normative specifications, existing `council-flow` skills, `.codex/agents/`, `README.md`, project-wide configuration, global hooks or xKiro/Claude credentials as a side effect of Phase 0–2. Those phases can be developed in a dedicated optional folder and isolated feature branch/worktree. Any later integration into CouncilFlow's live skill requires separate Owner approval; documentation alone does not grant it.

A clean optional location proposed for the prototype is `experiments/agent-efficiency/`. Keep emitted run artifacts under `experiments/agent-efficiency/.local-runs/`, ignored by Git. Do not create an orchestration server, proxy, billing service, model router, memory graph or Supervisor. Use Python stdlib unless empirical need justifies a dependency.

## 1. Minimal architecture

```text
Codex CLI --------------[Codex adapter]---------\
                                                 +--> opt-in metrics & digest toolkit
Claude Code -> xKiro ---[Claude/xKiro adapter]---/         |
                                                          +--> local sanitized run records
Any later app ----------[new adapter later]-----/         +--> full artifacts + bounded views
```

- **Core**: local run-record schema and validation, artifact hashing, bounded deterministic digests, explicit expand operation, benchmark comparison. No LLM required for these operations.
- **Adapters**: individually detect *capabilities actually available* for current version, harness and route; ingest documented, locally consented outputs. Missing usage/billing fields remain `unknown`, never zero. Use explicit routes `codex/native-or-configured` and `claude-code/xkiro/<upstream-model>`, **not** the model name alone.
- **Opt-in**: no implicit interception of chats or installation of global hooks. Prefer a CLI wrapper/standalone parser first. A model-facing skill is optional and later; never assume a skill controls raw host transport.
- **Safety**: no secrets, auth files, raw prompts, hidden chain of thought or private session transcripts in committed telemetry. User opt-in for collecting any raw CLI events; process only test-owned tasks, and redact or decline unsafe payloads. Preserve complete **test/tool evidence** locally where allowed, but do not indiscriminately persist private model-session logs.

## 2. Phases, outputs and gates

### Phase 0 — Environment and baseline observations (first PC step, no feature coding)

**Work:** In an isolated, non-destructive branch/worktree, confirm local checkout, git status, `py -3 --version`, `codex --version`, `codex exec --help`, `claude --version`, `claude --help`, and existing test commands. For Claude Code, identify whether `ANTHROPIC_BASE_URL` points to xKiro **without printing its value if sensitive** or exposing any token; record the *route class* and chosen upstream model string if the CLI itself exposes it safely. Check official command/hook documentation against the locally installed version. Do not change authentication. Read current source first; don't re-audit the entire repository.

**Output:** `experiments/agent-efficiency/notes/local-capabilities.md` with supported/unverified capabilities, evidence origin, and a small comparison of *what Codex vs Claude Code/xKiro can actually report*. Capture baseline run data only from an innocuous, explicitly selected test-owned task.

**Gate:** Can observe a safe baseline without changing CouncilFlow's workflow. If unavailable, mark `UNAVAILABLE` and stop that adapter without pretending the host provides it.

### Phase 1 — Provider-neutral baseline recorder

**Work:** Create a tiny stdlib-only `RunRecord` JSON/JSONL format, validator and test fixtures; parse **documented** Codex `codex exec --json` completion usage where verified and Claude Code's documented machine-readable output or permitted local metrics where verified. Distinguish input, cached input, cached write, output, wall time, retries, host scope, route/model identity, accepted-task outcome, and provider-reported cost. Some fields can be absent. Do not derive authoritative xKiro cost or cache hit rates from Anthropic pricing or Claude Code's display.

Suggested record fields: `schema_version`, `run_id`, `task_class`, `harness`, `route`, `upstream_model`, `repository_revision`, `elapsed_ms`, `usage_scope`, `usage{input,cached_input,cache_creation,output,reported_cost}`, `attempt`, `acceptance{status,evidence_ref}`, `source_kind`, and `notes`. Missing values are `null` with a reason. Use explicit evidence sources, not agent-declared success.

**Output:** schema, parser(s), tests, example sanitized JSONL, one repeatable invocation path; summary table of measured versus unavailable metrics.

**Gate:** Does not alter token usage on its own; validates native sample events and recognizes unsupported event formats without fabricated measurements. A baseline needs **comparable accepted tasks**, not merely token counts.

### Phase 2 — Deterministic tool-result digest, with failure-blind-spot controls

**Work:** A small opt-in wrapper for a **known safe local command** or parser for its already-produced output. Record exact exit code, bounded stream excerpts, failing test identifiers where deterministically extractable, source command identity, environment/cwd reference, and SHA-256 of complete captured `stdout` and `stderr`; retain the full permitted output as an **expandable local artifact**. Do not silently drop warnings, stack traces, or errors. If parsing is incomplete or uncertain, flag `DIGEST_INCOMPLETE` and provide direct expansion rather than giving an all-clear. Nonzero exits, timeouts, oversized output, decoding failures, mixed CRLF, ANSI escapes and parser errors get explicit negative tests. Prevent path traversal and artifact symlink escapes; do not claim race-free OS containment.

**Output:** `digest` and `expand` commands, machine-readable and human-readable output, tests including seeded root-cause details outside the excerpt. Keep the original full outputs and hashes for inspection.

**Gate:** Correct exit and artifact integrity; no missing failure classifications in controlled fixtures; measured blind spots vs unmodified full logs, not just token reduction. Existing trusted Tester/Reviewer verification still applies.

### Phase 3 — Codex opt-in adapter, not CouncilFlow skill integration

**Work:** Exercise the standalone tool with a small, authorized Codex task using supported `codex exec --json` event output; ensure no transformation of Codex's internal messages/permissions. Test Windows path handling, cancellation/error cases, and per-thread versus aggregated usage. An optional repo-scoped invocation helper can be considered if needed, but **do not edit** `.agents/skills/council-flow/` or native agent TOMLs in this phase.

**Gate:** Working trace with authoritative observed fields, honest missing fields, and no impairment of Codex invocation or task outcome. If hooks or app UI behave differently, list differences, do not emulate phantom support.

### Phase 4 — Claude Code + xKiro opt-in adapter

**Work:** Confirm the locally installed Claude Code version and documented stream output/hook support. Implement *only available* ingestion or a repo-local opt-in helper; never overwrite existing user/project hooks or model settings. Test on a bounded innocuous request through the user's already-configured xKiro route; report exact effective upstream model where observable. Native Claude Code counters, xKiro gateway counters, and true upstream billing are distinct data sources; compare only when they have compatible meanings. Test missing usage, gateway retries, models changing, partial streams, and unsupported caching fields.

**Gate:** One reproducible successful local smoke test plus an honest capability/limitations matrix; no key is read, displayed or committed. If the gateway doesn't report cache hits or true costs, those metrics stay `unknown`.

### Phase 5 — Small paired evaluation (Owner-approved protocol before running)

**Work:** Compare baseline and digest-enabled workflows on **the same class of tasks**. Record accepted-task outcomes, execution cost/quota where reliable, time, retries, cache hits where available, and digest-induced diagnostic misses. Keep task order and environment conditions visible. Evaluate enough tasks to bound the **Owner-predeclared minimum worthwhile effect**, rather than declaring a fixed sample size adequate. Start with low-cost pilot observations; do not construct a huge benchmark framework without a demonstrated need.

**Preconditions:** The Owner explicitly approves experimental task set, cost/quota budget, scope, minimum worthwhile effect, reliability and security thresholds, decision rule, maximum runs/time, and terminal outcomes. Freeze and hash the protocol artifact before the first controlled run; no post-hoc tuning.

**Gate:** `BENEFIT_OBSERVED`, `CLOSED_NO_BENEFIT`, or `INCONCLUSIVE` under the prespecified rule. Stop automatically at authorization or budget bounds. No claims of benefit from a successful static test alone.

### Phase 6 — Optional CouncilFlow integration and later adapters (separately authorized)

**Work:** Only after evidence supports it and the Owner authorizes integration, propose a minimal opt-in boundary linking CouncilFlow to the toolkit. Preserve its exact Owner/Planner/Manager/Worker/Tester/Reviewer/Manager/Planner/Owner route and the **newer authoritative Reviewer comparator**; Tester command evidence and frozen-plan fidelity remain mandatory. No automatic schema rewrites or implicit activation of global hooks. Existing trusted-Supervisor and host enforcement limitations remain explicit.

For new applications, add an adapter conforming to the tested core contract and its own capability tests. Do not promise “any app” before it exposes a suitable CLI/API/hook/log surface.

**Gate:** Native host behavior validated separately for each adapter/route, full existing regressions unaffected, no changes to frozen Gate 3 candidate or policy by accident. Promotion/integration only with Owner approval.

## 3. Suggested executable work packages

**Package A (first coding authorization):** Phase 0 + Phase 1 only, in `experiments/agent-efficiency/`, with simulated fixtures where local CLI usage is unavailable. Required: executable unit tests, clear provenance labels, working sanitized sample; no CouncilFlow runtime edits.

**Package B:** Phase 2 only; controlled negative tests and digest-blind-spot review.

**Package C:** Phases 3 and 4 one adapter at a time, only when those tools are actually available locally.

**Package D:** Phase 5 protocol and experiment after Owner budget approval. Phase 6 integration separately authorized only on demonstrated benefit.

Each package ends with changed-file paths, test commands/results, a clear observed/untested matrix, resource usage where known, and one suggested next action. No more than one adapter should be modified in a package without explicit authorization. No automatic broad refactor, forced migration or installer.

## 4. When home: exact first steps (PowerShell)

Use the **actual local checkout**, for example `E:\Saint\PROJECTS\CouncilFlow-main` if that is still its path. Do not assume the path has not changed.

```powershell
Set-Location "E:\Saint\PROJECTS\CouncilFlow-main"
git status --short
git branch --show-current
git log -1 --oneline
```

If the working tree has unrelated changes, **do not discard, reset, stash, or overwrite them automatically**; use a separately checked out worktree or ask the coding agent to choose a non-destructive isolation strategy. Once the local checkout is safely up-to-date (fetch and fast-forward only if appropriate), copy the implementation prompt below into **Codex or Claude Code**. One chosen host implements Package A; do not run two Writers over the same files.

You do **not** need to uninstall/reconfigure xKiro, supply API keys, or convert the Codex skill to Claude Code to execute the first package. Native Claude Code/xKiro observation occurs only when local tools and outputs can be inspected legitimately.

## 5. Ready-to-paste **Package A** implementation prompt

> **Owner authorizes Package A only when this prompt is explicitly submitted to a coding agent.** Reading the plan or being sent the link is not authorization to start.

```text
MODEL: [Identify actual executing model and route at start; do not guess.]

You are implementing Package A of the non-normative agent-efficiency prototype in the existing repository:
https://github.com/luvhscupid/CouncilFlow

PRIMARY PLAN:
docs/research/Agent-Efficiency-Implementation-Phases-DRAFT-2026-11-15.md
RESEARCH:
docs/research/AI-Agent-Token-and-Context-Efficiency-2026-11-15.md

OWNER AUTHORIZATION FOR THIS RUN: Implement Phase 0 and Phase 1 ONLY. Do not implement later phases, begin paid benchmarks, modify CouncilFlow skill/roles/config, alter Gate 3/frozen specifications, change global settings, alter authentication, or route around native permissions.

First inspect current Git status, current main and relevant repo docs. Work from a clean, isolated branch/worktree, preserving existing changes. Read Gate 3 Owner Charter so no older role descriptions override it. No separate deep repo audit: inspect only what is necessary to implement this package.

Implement a minimal Python-standard-library prototype entirely under experiments/agent-efficiency/ (plus a narrowly scoped .gitignore only if required). It must safely capture/validate/represent **available** baseline usage metrics from documented Codex and Claude Code execution surfaces with explicit host/source labels. Codex CLI JSONL parsing may be built using sanitized fixtures; Claude Code via xKiro must be treated as a DISTINCT harness/route/model identity, not automatically credited with Anthropic-native accounting. Unknown fields must be null, not invented. Do not collect or commit credentials, raw private conversations or hidden reasoning.

Add tests and test fixtures for valid/partial/missing/malformed/unknown usage events, mixed model routes, and accepted-outcome provenance. Do not run expensive model calls without Owner budget approval. If local CLI capabilities cannot be observed, mark them UNVERIFIED; complete offline parser/fixture work, do not fabricate live integrations.

Run only relevant tests, report changed paths, real commands/results, limitations, and a concise next-step for Package B. Do not claim verified token savings, native installation, or integration with CouncilFlow.
```

## 6. Subsequent implementation prompts (once Owner approves each)

- **Package B:** “Implement only Phase 2 of the draft plan on a clean branch, after checking Package A results. Add the deterministic tool-output digest and expand interface with full-artifact retention, exact exit preservation, and blind-spot negative controls. No live host integration or global hooks. Run tests and report evidence.”
- **Package C1:** “Implement only Phase 3, Codex adapter, after verifying current Codex CLI documentation and local version. No CouncilFlow skill changes. Provide a bounded verified smoke test and unsupported-field list.”
- **Package C2:** “Implement only Phase 4, Claude Code through my existing xKiro route, after verifying local capabilities. Never read or expose keys; do not overwrite hooks or model config. Preserve separate route/model accounting, run a bounded smoke test, and list unverified fields.”
- **Package D:** “Prepare the proposed Phase 5 experimental protocol, with predeclared meaningful effect, reliability thresholds, budget, and stop rules for my approval. Do not run controlled paid trials or Phase 6 integration until I approve.”

## 7. References and priorities

- Frozen CouncilFlow roles and Gate 3: `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`, `02-GATE3-v0.2-FROZEN.md`.
- Known implementation discrepancy record: `docs/gate3/current-implementation-gaps.md`. Read as historical/static evidence, not authorization to fix the skill during Gate 3.
- Independent research: `docs/research/AI-Agent-Token-and-Context-Efficiency-2026-11-15.md`.
- Codex CLI JSON events: https://learn.chatgpt.com/docs/non-interactive-mode
- Codex CLI options: https://learn.chatgpt.com/docs/cli/reference
- Claude Code official hooks (check current version): https://code.claude.com/docs/en/hooks

**Priority rule:** Do not let this optional efficiency experiment displace an already approved CouncilFlow development task unless the Owner explicitly chooses to prioritize it. Stop at useful evidence, not another round of speculative architecture design.
