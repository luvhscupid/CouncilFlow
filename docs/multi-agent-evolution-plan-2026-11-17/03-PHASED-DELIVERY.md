# 03 — Phased delivery roadmap

**Plan only.** Every execution phase requires a **new explicit Owner authorization** with exact scope, route, spend/permissions, acceptance and baseline. Publishing this document does not authorize automatic rollout, model calls, CI experiments or Slice 2. A phase can conclude `NO_GO` with no product changes.

## Global promotion workflow

1. **Owner binds scope** to a particular phase, issue set and frozen plan. Check current `main` against baseline `6c4e477` and resolve any newly merged changes.
2. **Prepare isolated experiment branch/worktree** without affecting the main skill, release packages, model route or global settings.
3. **Implement bounded capability**; maintain a manifest of changed files, code paths, schema versions, and original acceptance IDs.
4. **Test with deterministic positive and negative controls**; record commands, output, hashes, package reproducibility, host native evidence where phase requires it.
5. **Independent Tester + Reviewer + Planner** verify the actual new candidate. No self-approval; evidence that can't be reproduced is UNVERIFIED.
6. **A/B or compatibility gate**, if relevant, with same tasks and measured budgets. Don't overclaim effects from a handful of easy tasks.
7. **Owner decision:** reject/retain experiment, revise or authorize a normal PR-based merge. Never silently merge because CI turns green.
8. **Rollback path:** disable optional feature, revert phase commits through ordinary history, restore previous package and verify no altered Owner source artifact.

## Dependencies

```text
P0 Baseline and evidence inventory
  |
P1 Existing Agent Efficiency live qualification (separate approval)
  |
  +---- P2 Per-role model capability router
  |          |
  |          +---- P6 Controlled A/B workflow optimization
  |
  +---- P3 Durable journal and recovery
             |
             +---- P4 Task DAG and isolated parallelism
             |
             +---- P5 Reviewed memory / diagnostics / dashboard
                         |
                         +---- P6 Workflow optimization

P7 Independent multi-model opinion room is optional and separate,
built only after identity, security and submission boundaries are approved.
```

P2 and P3 may be evaluated independently *after* their common evidence requirements, but should not be integrated simultaneously. The diagram expresses risk/order, not an instruction to launch them concurrently.

## P0 — Reconcile baseline and obtain reproducible evidence

**Goal:** ensure the plan is grounded in current CouncilFlow behavior, including recently merged Slice 1 changes.

**Preconditions:** permitted read-only access to latest repository and host; no model calls required. No product modifications.

**Proposed work:**
- Record HEAD, all open branches that overlap, package manifests, known native activation limitations, Agent Efficiency helper status, and whether Slice 2 is still withheld.
- Inventory already present role contracts, accepted-input source fidelity, Tester deterministic commands, Reviewer rerun, Codex/Claude packaging, CBM lifecycle and dashboard projection work; avoid implementing duplicates.
- Classify every candidate feature `EXISTS_VERIFIED` / `EXISTS_UNVERIFIED` / `MISSING` / `CONFLICTS_WITH_CHARTER`.
- Freeze a small measurable baseline: commands/versions, representative repository fixtures, observable role events and current limits, with hashes. Mark unavailable host access plainly.
- Validate license status and current external repo SHAs before importing any source or dependency.

**Deliverables:** `baseline-manifest.json` proposal; gap inventory; independent evidence links; risk-to-phase map. **Acceptance:** no unexplained discrepancy between main and plan, no inferred native capability, unchanged worktree. **Rollback:** none (read-only).

**Stop:** missing current original charter/authority for a proposed boundary; conflicting ongoing work requiring Owner resolution.

## P1 — Existing Agent Efficiency: qualify, don't rewrite

**Goal:** decide whether the *already packaged, optional* recorder/digest/expand and Codex/Claude adapters help allocate context and effort wisely while retaining result quality and original evidence. Efficiency is **not** just cutting tokens.

**Dependency:** P0 and separate explicit approval for any trial. Existing [Package D protocol](../../experiments/agent-efficiency/evaluation/PROTOCOL.md) stays DRAFT_NOT_AUTHORIZED until the Owner expressly approves it or a revised protocol.

**Proposed work:**
- First run the existing offline regression fixtures, install-path resolution and full-output hash expansion without a gateway call.
- For a permitted host, verify native response shape and the separation of configured/reported/effective model; do not touch user xKiro settings or extract tokens.
- Qualify one unambiguous, owner-approved A/B task block with identical host, model, permission and test budgets. No simultaneous provider/model changes.
- Compare evidence quality, successful original acceptance, corrective expansion behavior, extra invocations, wall time and observed context/usage. Unknown telemetry stays unknown.
- Decide whether the optional helper should remain opt-in, be simplified or be retired. No automatic enablement without separate approval.

**Outputs:** complete A/B manifest, hash-bound transcripts or safe metadata as allowed, comparison report, `NO_GO/GO_FOR_NEXT_PHASE` recommendation. **Acceptance:** full byte-preserving expansion on controls; incomplete digest cannot pass acceptance; no lost failing tests; no route/cost invention. **Rollback:** leave helper disabled; restore unchanged package. **Stop:** billing uncertainty, accidental secret capture, permission discrepancy, quota exhaustion, unverifiable host path.

## P2 — Capability-aware role/model routing (opt-in)

**Goal:** separate chosen model *preference* from observed host execution without breaking native delegation, especially when a cheap Worker or Tester is appropriate.

**Dependency:** P0 evidence, P1 known telemetry limitations, Owner-approved provider/route policy. Do not assume lower-cost models are capable until tested.

**Work packages:**
- Define versioned desired-role profile, host capability registry, effective-model provenance and explicit fallback classes.
- Implement a **read-only capability probe** using documented host interfaces; do not inspect secrets or add gateway credentials.
- Build an opt-in route selection shim restricted to host-supported selection; if impossible, mark inherited model rather than claiming independent routing.
- Unit test malformed profiles, missing model, wrong capability, stale model mapping, unsupported effort and subscription/API boundary mismatches.
- Run paired low/medium-risk coding tasks against the existing inherited-model baseline under equivalent acceptance tests and retries; keep independent verification.
- Publish a role matrix of observed identity/capability and outcome with confidence level; don't make a fixed model ranking from a tiny pilot.

**Outputs:** optional profile/schema, host-specific adapter, capability matrix and tests, no secret-bearing configuration. **Acceptance:** true or explicitly UNKNOWN model/route provenance; fail-safe fallback; existing default behavior unchanged, no model substitution across frozen comparisons. **Rollback:** feature toggle to inherit host; packaged release untouched until authorized promotion. **Stop:** API subscription misuse, provider mismatch, inability to obtain independent role evidence or excessive/unknown cost.

## P3 — Durable run journal, idempotent transitions and recovery

**Goal:** recover after Claude Code quota interruption, Codex restart, crash or Manager context loss without losing the frozen plan or misattributing completed work.

**Dependency:** P0, compatible original-message contracts, Owner permission for local non-secret state storage. This is a **new runtime experiment**, not evidence that current JSONL is crash-safe.

**Work packages:**
- Define event/state schema including run/attempt revisions, candidate SHA, criteria ref, causal parent, actor provenance, terminal reason and human approval provenance.
- Prototype local, opt-in transactional store (SQLite if selected by Owner) with atomic compare-and-swap, schema versioning and limits. Keep deterministic export. No direct writes to frozen plans.
- Build replay/reconcile on restart: verify host process/session existence, workspace revision and artifact hashes; mark interrupted runs `RECOVERY_REQUIRED`.
- Re-dispatch only if host/Owner authorization and attempt identity permit; do not replay writes or auto-merge based on remembered prompts.
- Test power-loss/crash points in isolated fixtures, simultaneous claims, stale workers, replayed reports, duplicate event IDs, repository mutation, corrupt/mixed schema, interrupted approval, retained evidence, Windows path edge cases.
- Give Manager a compact recovered handoff referencing *actual* evidence. The original chat is not a trustworthy replay channel.

**Outputs:** proposed schema, verified state machine, isolated store, deterministic replay CLI/tests, integration plan. **Acceptance:** duplicate/out-of-order cannot become `ACCEPTED`; replay cannot manufacture a Tester, Reviewer or Owner approval; any corrupt artifact blocks rather than silently resets. **Rollback:** disable journal, archive isolated test state, no modifications to production contracts. **Stop:** unrecoverable corruption, missing permission boundaries, unbounded journal size or external-state leakage.

## P4 — Task DAG and safe isolated parallel execution

**Goal:** speed only work with truly independent scopes. Preserve one mutating Worker **per workspace** and serialized verified promotion.

**Dependency:** P3 stable identity/recovery semantics; Owner-specific approval for parallel write experiments.

**Proposed work:**
- Represent prerequisites in an acyclic task graph; validate cycles, missing parents, stale criteria and blocked states.
- Implement assignment in isolated disposable Git worktrees/clones, **not only advisory path locks**. Verify host sandbox and filesystem rights.
- Separate read-only parallel exploration from mutating tasks; default to serial until actual isolation is demonstrated.
- Require commit/base matching, conflict checks and serialized candidate promotion, followed by new merged-candidate independent acceptance.
- Inject conflicting edits, symlink/reparse paths, dual claims, duplicate completion, slow worker, stale base, failed partial promotion and forced termination.
- Measure wall-time improvement *after* excluding integration repair and duplicate rework.

**Outputs:** opt-in scheduler/workspace prototype and isolated conflict test harness. **Acceptance:** no cross-workspace writes in tested conditions, no shared-state race causing false acceptance, predictable failure/rollback, integrated candidate revalidated. **Rollback:** switch to single Worker mode. **Stop:** lack of enforceable isolation, conflicting plans, unknown host permissions or tests running outside approved sandbox.

## P5 — Reviewed memory, doctor and observability

**Goal:** make decisions and progress recoverable without leaking context or growing a new platform.

**Dependency:** P3 structured events; P1 evidence semantics. Read-only dashboard is optional, never a security authority.

**Work packages:**
- Extract reviewed lessons only after final role acceptance; store `success/failure/insight` with trusted links, scope, supersession and TTL or review rule.
- Test retrieval with counterexamples: stale instructions, irrelevant project, poisoned model opinion, superseded security rule and hidden-test exposure.
- Implement deterministic doctor checks with `PASS/FAIL/BLOCKED/SKIP/UNVERIFIED`, specific remediation and non-green unknowns.
- Optional read-only UI projection on top of verified journal data. Reuse existing dashboard components if present; do not create a second dashboard.
- Trace per-role task/attempt, real tool command/evidence and observed usage; never put prompts, secrets or tokens into public traces.

**Outputs:** memory schema, qualification/retrieval tests, doctor, projection contract. **Acceptance:** no policy grant from memory, no untrusted memory in Worker by default, diagnostic status matches evidence, UI never self-approves. **Rollback:** disable memory ingestion/doctor overlay; previous skill unaffected.

## P6 — Measured workflow optimization

**Goal:** adapt the *configuration* of approved workflows by experimenting with candidates, not silently rewriting production safety controls.

**Dependencies:** P1 baseline measurement, P2 provenance where model comparisons are involved, P3 run reproducibility, P4/P5 only if experiment needs their functionality.

**Proposed work:**
- Freeze an Owner-approved task suite and independent oracle. Use unchanged control workflow plus one treatment at a time.
- Candidate levers: cheaper compatible model for bounded Worker tasks, digest/expand, limited context retrieval, review cadence, task decomposition, or approved skill selection.
- Never optimize Owner authority, frozen criteria, independent Tester/Reviewer or containment controls away.
- Keep an explicit multi-objective report: accepted-task rate, false accepts, rework, context/usage, time and confidence. Recognize confounders and missing billing data.
- Store each candidate in a separate branch/workspace. Validate offline and native activation. Give Owner a side-by-side proposal; no self-merge, self-release or scheduled production mutation.

**Outputs:** benchmark dataset, candidate manifests, no-regression gate and comparative report. **Acceptance:** independent evidence plus repeatability; treatment cannot hide an unmet criterion; result must beat the baseline on declared objective without degrading hard safety outcomes. **Rollback:** discard candidate branch; retain recorded evidence.

## P7 — Optional independent-model council room (separate product-adjacent experiment)

**Goal:** collect independent Gemini/DeepSeek/GLM/Grok/etc. opinions on an issue without giving those models repo access or forcing one model to relay every message.

**Prerequisites:** separate Owner approval; threat model for submissions/storage/auth and discussion privacy. Not required for core CouncilFlow correctness.

**Proposed boundaries:** local-only or explicitly hosted *discussion inbox*, fixed issue ID and plan revision, submitter claim distinct from verified route identity, immutable submission timestamp/content fingerprint, challenge/response threads, no secrets, sanitized pasted inputs, explicit closing Owner decision. Import only an Owner-approved final plan into CouncilFlow, and prove source fidelity. No external AI gets direct task execution from simply posting to the board.

**Acceptance:** cannot turn a forged opinion into Owner authorization; forged/replayed submissions rejected or clearly marked unverified; no privileged execution path from text. **Rollback:** read-only export and service shutdown; core skill unchanged.

## Portfolio gates and release discipline

Proposed phase statuses: `NOT_STARTED -> OWNER_AUTHORIZED -> IMPLEMENTING -> EVIDENCE_PENDING -> INDEPENDENTLY_VERIFIED -> OWNER_REVIEW -> PROMOTED`; `BLOCKED/REJECTED/REVERTED` are distinct. Preserve ordinary non-force PR review and release packaging. Never confuse "experiment succeeded" with "native workflow validated in every host."

**Out of scope:** full Agyn Kubernetes deployment, copying Forge wholesale, replacing CouncilFlow's Planner/Manager contract, universal OAuth model proxy, self-updating production main, unsupervised paid model experiments and automatic Slice 2 kickoff.
