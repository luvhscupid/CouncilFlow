# CouncilFlow Evolution Readiness Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. This is a documentation-only task; preserve the CouncilFlow role sequence and use an independent Reviewer check at the end.

**Goal:** Produce one source-cited, read-only readiness packet that shows what the evolution branch proves, what remains blocked or experimental, and what an Owner must decide before any later phase can proceed.

**Architecture:** Add one non-normative report under `reports/`. It combines a current revision/evidence inventory, a tabletop trace through the fixed CouncilFlow handoffs, phase readiness receipts, and a reusable evidence-packet template. Existing plans, frozen Gate 3 records, role contracts, packages, and runtime code remain the sources of authority and are not changed.

**Tech Stack:** Markdown; read-only Git inspection (`git status`, `git rev-parse`, `git ls-remote`); `rg` for source references; `git diff --check` for document validation.

**Spec:** `docs/multi-agent-evolution-plan-2026-11-17/README.md`, `03-PHASED-DELIVERY.md`, `06-EXECUTION-BACKLOG.md`, `reports/multi-agent-evolution-status-2026-11-18.md`, `.agents/skills/council-flow/SKILL.md`, `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`, and `docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md`.

## Global Constraints

- Preserve the exact role order: Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner.
- Manager coordinates; Manager does not implement.
- Reviewer compares the Worker candidate, Tester evidence, and original frozen Owner plan, and independently reruns one Tester-declared deterministic command with the recorded executable, arguments, working directory, candidate and input identities, exit code, and normalized-stdout SHA-256.
- Treat the evolution roadmap as proposed and non-normative. A readiness report or completed checklist does not authorize a phase.
- No live model calls, provider/host changes, spending, permission changes, parallel worker writes, runtime changes, package rebuilds, promotion, merge, or push in this plan.
- Preserve historical research and frozen Gate 3 artifacts; cite them without rewriting them.
- Distinguish current observations from historical evidence, caller claims, and unknowns. Never infer native capability from a CLI option or an old run record.
- Keep P4 mutations serial unless enforceable workspace isolation is separately authorized and demonstrated.

## Review Focus

- Stale branch or main revisions: record exact current HEAD and query the remote main ref directly; do not trust a stale local `origin/main` ref.
- Historical host evidence: label its environment and date; do not present it as a current invocation.
- Capability claims: separate documented command-line options from capability discovery and effective-route attestation.
- Blocked-phase receipts: state the exact missing evidence/authority and reopening condition; do not make a receipt look like approval.
- Acceptance proof: retain frozen criteria and the independent deterministic rerun requirement; a self-reported result cannot satisfy either.

---

## Scope and Owner gate

This plan produces only `reports/multi-agent-evolution-readiness-2026-11-19.md`. The report is an evidence map and execution handoff, not a new workflow specification. It does not run a live task or fill gaps with simulated agent behavior.

Before executing this plan, the Owner authorizes this bounded documentation slice: read-only repository inspection plus creation of the single report above; zero model calls or external spend; no permission or host configuration changes; no source/runtime/package edits; acceptance is the checklist in Task 5. The execution baseline is the branch HEAD recorded in Task 1. Any phase-specific live or implementation work requires a separate Owner authorization under `03-PHASED-DELIVERY.md`.

## Planned file map

- Create `reports/multi-agent-evolution-readiness-2026-11-19.md`: the single decision-ready inventory, tabletop trace, readiness receipts, and future phase evidence template.
- Read only the source files listed in **Spec**, plus `reports/documentation-release-sync/gate3-run-01.md` and `reports/documentation-release-sync/claude-calc-001.md` for historical evidence labels.
- Modify no other files.

## Task 1: Record the current evidence baseline

**Files:**
- Create: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Read: files in **Spec** and the two Gate 3 evidence summaries in the file map.

**Interfaces:**
- Consumes: current repository state and cited status/authority documents.
- Produces: a dated source-of-truth table in the readiness report with claim, status, source, observed date/environment, what it establishes, and limitation.

- [x] **Step 1: Record the checkout identity.** Capture `git status --short --branch`, `git rev-parse HEAD`, and `git ls-remote origin refs/heads/main refs/heads/evolution/multi-agent-plan-2026-11-17`. Treat this plan file as an expected untracked artifact; stop before drawing a current-state conclusion if there are any other unexplained edits or the remote cannot be read. Compare the local HEAD with both direct remote refs and record any mismatch.
- [x] **Step 2: Extract the phase results from the current status report.** Record P0 through P7 with the report’s exact status wording and source heading. Preserve `UNKNOWN`, `UNVERIFIED`, `BLOCKED`, `EXPERIMENTAL`, and `SEPARATE_PROJECT` distinctions.
- [x] **Step 3: Add the evidence inventory.** For each claim, cite a path and heading. State explicitly that historical Codex/Claude evidence and local prototype checks do not establish current native activation, route identity, authenticated approvals, isolation, live optimization, or production promotion.
- [x] **Step 4: Check the section.** Verify the report contains HEAD, remote main SHA, all P0–P7 statuses, source citations, and a limitations column. Expected result: every status has a direct cited source; no status is inferred from a branch name or tool option.

## Task 2: Add a non-executing role-by-role tabletop trace

**Files:**
- Modify: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Read: `.agents/skills/council-flow/SKILL.md`, the Owner Charter, frozen Gate 3 criteria, and historical evidence summaries.

**Interfaces:**
- Consumes: the fixed role order and already-recorded artifacts.
- Produces: one row per role transition with frozen input, expected handoff/artifact, evidence currently available, and status (`OBSERVED`, `HISTORICAL`, `UNVERIFIED`, or `BLOCKED`).

- [x] **Step 1: Use the exact fixed role sequence.** Include Owner, Planner, Manager, Worker, Tester, Reviewer, Manager, Planner, Owner in that order; do not collapse repeated roles.
- [x] **Step 2: Bind each row to an existing artifact or mark it unavailable.** A prior `calc-001` or Gate 3 record may be cited as historical evidence only. Do not invent a current agent invocation, message, command, permission, or result.
- [x] **Step 3: Preserve role boundaries.** Mark Manager as coordinator; Worker as implementer only in the historical trace; Tester as evidence producer; Reviewer as independent comparer and rerunner; Planner as final frozen-criteria checker.
- [x] **Step 4: Review the trace.** Expected result: each role row has a source or explicit gap, and the Reviewer row retains the exact deterministic rerun requirement from the frozen charter.

## Task 3: Add phase readiness receipts and reopening conditions

**Files:**
- Modify: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Read: `reports/multi-agent-evolution-status-2026-11-18.md` and `03-PHASED-DELIVERY.md`.

**Interfaces:**
- Consumes: current phase findings and dependencies.
- Produces: one receipt per phase with current state, evidence, missing proof/authority, resolver, precise reopening condition, and safe interim behavior.

- [x] **Step 1: Cover every phase P0–P7.** Preserve the recorded outcomes: P0 refreshed with license unresolved; P1 offline-qualified/live blocked; P2 host capability query unsupported; P3 experimental local journal with host authentication unverified; P4 isolation blocked and serial; P5 offline schema complete with authority unverified; P6 live optimization blocked on Owner inputs; P7 separate project/not applicable to core.
- [x] **Step 2: Write blockers from cited evidence only.** For P1, cite missing Owner inputs such as approved host/route, frozen tasks/oracles, verifier bindings, retention/telemetry, numeric ceilings, stop control, and decision rule. For P2, require documented host capability semantics and independent route evidence. For P4, require an approved isolation harness and deny evidence. For P6, preserve its P1/P2/P3 dependencies and missing live-evaluation inputs.
- [x] **Step 3: State safe interim behavior.** Keep live calls off, routing inherited, journal experimental, mutations serial, memory/authority claims unverified, and P7 outside core scope unless a new Owner decision changes the applicable gate.
- [x] **Step 4: Validate receipts against the status report.** Expected result: no receipt grants permission, changes phase priority, or turns a missing condition into a pass.

## Task 4: Add the reusable authorized-phase evidence packet

**Files:**
- Modify: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Read: `06-EXECUTION-BACKLOG.md`, the communication contract, and frozen Reviewer criteria.

**Interfaces:**
- Consumes: the backlog’s proposed completion packet and current CouncilFlow message/evidence boundaries.
- Produces: a copyable checklist for a future separately authorized phase.

- [x] **Step 1: Include authorization and identity fields.** Work ID, actual Owner authorization provenance, frozen plan/acceptance IDs, HEAD/base/candidate SHA-256, allowed paths, and changed-file manifest.
- [x] **Step 2: Include Tester and Reviewer execution fields.** Exact executable path, arguments, working directory, candidate/input identities, exit code, normalized-stdout SHA-256, evidence artifact, Tester result, independent Reviewer rerun result, and comparison.
- [x] **Step 3: Include decision and limit fields.** Manager decision, Planner final check, observed and unknown route/usage fields, open limits, rollback action, and recommended Owner decision.
- [x] **Step 4: Mark the packet as a template only.** Expected result: it requires a real phase authorization and cannot be used as approval or a self-attested role identity.

## Task 5: Verify the readiness packet and hand off

**Files:**
- Verify: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Expected changed files: this plan and that report only; no other tracked or untracked files.

- [x] **Step 1: Check formatting and changed-file scope.** Run `git diff --check`; then run this PowerShell check against the untracked report so it is covered too:

```powershell
$bad = Select-String -Path 'reports/multi-agent-evolution-readiness-2026-11-19.md' -Pattern '[ \t]+$'
if ($bad) { $bad; exit 1 }
```

Expected: both checks exit 0 and the whitespace check emits no matches. Inspect `git status --short` and confirm the only new/changed files are this plan and the readiness report.
- [x] **Step 2: Tester checks source fidelity.** Independently compare each phase status, role sequence, and blocker condition in the report against the cited source documents. Record the outcome and any discrepancies in the report's [document review record](../../../reports/multi-agent-evolution-readiness-2026-11-19.md#verification-and-handoff); do not repair source authority or weaken criteria.
- [x] **Step 3: Reviewer compares the report and Tester evidence to this plan and the original Owner sources.** Independently rerun the exact Tester-declared deterministic check, recording executable path, arguments, working directory, candidate/input identities, exit code, and normalized stdout hash in the report's [deterministic check record](../../../reports/multi-agent-evolution-readiness-2026-11-19.md#verification-and-handoff). Record any missing raw artifact that limits replay. The Reviewer runs the same check without a shell alias.
- [x] **Step 4: Planner checks the report against the requested scope and frozen acceptance.** Record the outcome in the report's [document review record](../../../reports/multi-agent-evolution-readiness-2026-11-19.md#verification-and-handoff). Expected: report is decision-ready, all limitations remain explicit, and no implementation/live phase is presented as authorized.
- [x] **Step 5: Return the report and unresolved Owner decisions.** No commit, push, merge, release, or phase promotion is part of this plan.

## Next-phase decision after this plan

The readiness packet should let the Owner select one bounded phase. The likely next proposal is to decide whether to authorize P1 live Agent Efficiency qualification, after supplying every missing P1 input in its receipt. P2, P4, and P6 remain gated by their own evidence and dependencies. This recommendation does not itself authorize P1.
