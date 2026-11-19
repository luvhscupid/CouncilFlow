# Multi-Agent Evolution Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Use the existing feature branch or a clean continuation branch; do not edit `main`.

**Goal:** Complete the remaining compatible Multi-Agent Evolution work in dependency order, and close unsupported or unauthorized phases with evidence rather than guessed capabilities.

**Architecture:** Refresh P0 first, then finish offline work independently of live host phases. Treat P3 journal, P4 isolation, P5 memory/diagnostics, and P6 optimization as separate deliverables with explicit dependency and security gates. P7 remains a separate optional project. A blocked host or Owner input must not block unrelated offline work.

**Tech Stack:** Python 3.11+ and standard library for runtime code; `unittest`; SQLite only in the experimental journal; existing Codex/Claude package builders; native host tools only when a phase card authorizes and documents them.

**Spec:** `docs/superpowers/specs/2026-11-19-multi-agent-evolution-completion-design.md`; controlling context: `docs/superpowers/specs/2026-11-18-multi-agent-evolution-design.md`, `docs/multi-agent-evolution-plan-2026-11-17/`, `docs/development-runs/2026-11-audit-remediation/`, `AGENTS.md`, and the Gate 3 Owner Charter.

## Global Constraints

- Preserve Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner and the frozen Gate 3 Charter.
- Keep `main` unchanged. The last observed `origin/main` was `5d8eb8686c51c392c0689e04932758ca30a76f2d`; last observed feature commit was `317eee01187dbefa82b71f77d4574b1144b9e08b`. Recheck both before execution.
- No live model/provider calls, route changes, spending, secret access, permission changes, product release, merge, or promotion without a completed phase card and required authorization. Existing authorization covers pushes to the feature branch only.
- Missing native evidence, unsupported APIs, caller identity, route, usage, and spend remain `UNVERIFIED`, `UNKNOWN`, or `BLOCKED`; no test fixture or report may upgrade them.
- Keep parallel mutation disabled until OS-enforced isolation is demonstrated. Git worktrees or path declarations alone are not isolation evidence.
- No new runtime dependencies or imported upstream source until the license and dependency checks pass.
- Keep runtime package copies byte-identical; regenerate tracked ZIPs only as package consistency artifacts.
- Existing user authorization covers compatible offline implementation on this published feature branch; do not ask again for that scoped work or let the older backlog's `NOT AUTHORIZED` label veto it. That authorization provides no numeric live-call budget and does not imply permission to change host configuration, permissions, or establish an external service.
- Every phase card records scope/paths, base SHA, host/version, network and spend limits (zero unless approved), data/retention, acceptance, independent Tester/Reviewer commands, stop conditions, rollback, and decision owner.

## Review Focus

- Stale `origin/main`, stale feature base, or an unreviewed overlapping branch: refresh refs and stop before combining changes.
- Claimed host routes or native roles without evidence: keep status unknown; never configure or infer a route.
- Corrupt, stale, replayed, or unreadable journal evidence: block recovery and retain the original database and artifacts.
- Path escape, symlink, FIFO, reparse point, or concurrent edit in evidence/workspaces: fail or block before reading or mutating.
- Live evaluation without a frozen oracle, bound, stop mechanism, and independent verifiers: do not start a call.

## Completed at Plan Baseline

- Feature branch `evolution/multi-agent-plan-2026-11-17` is published at `317eee01187dbefa82b71f77d4574b1144b9e08b`; `origin/main` was `5d8eb8686c51c392c0689e04932758ca30a76f2d`; the working tree was clean when this plan was written.
- Offline Tasks 1–6 in `docs/superpowers/plans/2026-11-18-multi-agent-evolution.md` are implemented.
- The 2026-11-19 Anti-Slop follow-up A–E is committed, reviewed, and pushed. Recorded checks: full tests 277 passed / 1 platform skip; Agent Efficiency 3 passed; package synchronization/builds and `git diff --check` passed.
- P1 offline qualification is complete. P1 live, P2 native routing, P3 recovery, P4 isolation, P5 broader observability, P6 live optimization, and P7 remain as scoped below.
- Do not repeat completed implementation or verification unless source changes, branch drift, or host changes invalidate the recorded evidence.

## Files and Responsibilities

- Preserve `reports/multi-agent-evolution-baseline-2026-11-18.md` as historical; modify `reports/multi-agent-evolution-status-2026-11-18.md` only for later observed evidence and gaps.
- Modify `experiments/multi-agent-evolution/journal.py` and `tests/test_journal.py` for the experimental state store; keep it outside installable runtime unless a separate design and authorization says otherwise.
- Modify `.agents/skills/council-flow/scripts/role_capabilities.py`, `task_graph.py`, `experience.py`, `doctor.py` and their matching tests only for the named helper deliverables; mirror package files with `python -B tools/build_claude_plugin.py sync`.
- Add phase-specific files only when an entry card defines their contract; do not create a scheduler, dashboard, provider service, or opinion-board service speculatively.
- Rebuild `dist/council-flow.zip`, its manifest/sidecar, and the Claude archive only through the existing builders and only when package sources changed.

---

### Task 1: Refresh baseline and remove execution ambiguity

**Files:**
- Preserve as historical: `reports/multi-agent-evolution-baseline-2026-11-18.md`
- Modify: `reports/multi-agent-evolution-status-2026-11-18.md`
- Modify: `docs/superpowers/plans/2026-11-18-multi-agent-evolution.md`
- Read: `docs/development-runs/2026-11-audit-remediation/README.md` and the applicable Slice 02/Slice 03 status files

**Interfaces:** Produce an evidence record with current local/remote HEADs, branch ancestry and dirty state; available PR/overlap evidence; current tests/build commands; license status; exact status of P0–P7; and an execution card template. Do not absorb unrelated audit-remediation scope.

- [x] **Step 1: Record current evidence.** Capture `git status -sb`, `git rev-parse HEAD origin/main`, `git ls-remote origin refs/heads/main refs/heads/evolution/multi-agent-plan-2026-11-17`, current test/build commands, and GitHub PR/branch inventory only if an authenticated supported interface is available. Do not change the historical baseline report.
- [x] **Step 2: Update current status.** Add a dated P0 refresh to the status report with raw evidence references. Change “no publication” to “no release publication or promotion; feature branch pushed” where applicable. Record unavailable open-PR/license facts as unknown. Treat audit-remediation Slice 02 as separate scope; use Slice 03 artifacts as host evidence if present.
- [x] **Step 3: Verify.** Re-run Git queries; compare every current status claim with evidence. `git diff --check` must pass. No code tests are required for a report-only update.
- [x] **Step 4: Commit.** `docs: refresh evolution completion baseline`.

**Exit:** current base/branch status and work boundaries are reproducible. An unresolved license is not a blocker for code using only existing sources and standard library; it blocks reuse of external code/dependencies and distribution decisions.

### Task 2: Record the P1 live gate without repeating offline work

**Files:**
- Read: `experiments/agent-efficiency/evaluation/PROTOCOL.md`, `RUNBOOK.md`, `protocol.draft.json`, `experiments/agent-efficiency/test_evaluate.py`
- Modify only if evidence changes: `experiments/agent-efficiency/IMPLEMENTATION-STATUS.md`, `reports/multi-agent-evolution-status-2026-11-18.md`

**Interfaces:** P1 offline status is already `OFFLINE_QUALIFICATION_COMPLETE`; refresh it only if protocol/source evidence changes. Live readiness is an approved phase card, not a code-level boolean. This task adds no readiness service or live call.

- [x] **Step 1: Compare recorded offline evidence.** Check the protocol, runbook, draft JSON, evaluator, and status report. Re-run offline suites only if relevant sources changed.
- [x] **Step 2: Record live blockers.** A pilot card must supply one host/route, frozen tasks/oracles, independent Tester and Reviewer bindings, permitted telemetry/retention, numeric all-role call/time/quota/cost bounds, reliable stop control, target effect/quality rules, and explicit authorization. Missing any field yields `BLOCKED_OWNER_INPUT`; the plan does not fill these values by assumption.
- [x] **Step 3: Keep live readiness closed.** Keep the protocol `DRAFT_NOT_AUTHORIZED` until actual authorization exists. No live calls are performed in this plan.
- [x] **Step 4: Commit.** `docs: record P1 live gate`.

**Exit:** offline qualification is current and repeatable; live P1 either has a complete approved card or is explicitly closed `BLOCKED`/`NOT_APPROVED`. A live pilot is not part of the default execution path.

### Task 3: Probe P2 host capability and hand off supported APIs

**Files:**
- Read: host-version documentation and evidence from the current Codex/Claude environment; `plugins/councilflow/skills/run/scripts/role_capabilities.py`; `tests/test_role_capabilities.py`
- Modify if and only if supported API is documented: canonical `.agents/skills/council-flow/scripts/role_capabilities.py`, focused tests, Claude mirror, relevant technical/status docs

**Interfaces:** Keep `validate_profile(data)` and `resolve_role(profile, capabilities, role)` pure and offline. This plan defines no native adapter signature. If documentation proves a supported API exists, write and approve a host-specific subplan with exact signature, errors, and tests before implementation. If not, close P2 as `UNSUPPORTED` with inherited routing.

- [x] **Step 1: Check existing host-support tests.** Confirm `test_unobserved_capability_is_not_supported` and `test_caller_supplied_capability_cannot_be_promoted_to_verified` cover `UNKNOWN`/`INHERIT_HOST` and cannot create `effective_model` or `route_verified` claims; add a regression only if an actual gap is found.
- [x] **Step 2: Run focused tests.** `python -B -m unittest tests.test_role_capabilities -v`.
- [x] **Step 3: Inspect supported host API.** Record host name/version and source documentation. If no explicit selection API exists, make no adapter; record `UNSUPPORTED` and proceed to independent work. If it exists, record its exact documented parameters/errors before implementation.
- [x] **Step 4: If supported, stop at a design handoff.** Record the API evidence and create a separate implementation subplan; do not invent an adapter signature in this cross-host plan.
- [x] **Step 5: Verify.** Focused tests, Claude `sync`/`check`, package/runtime equality, and a native smoke only if a later card authorizes it. Native smoke must retain sanitized evidence and actual host/version.
- [x] **Step 6: Commit.** `docs: record P2 host capability result`.

**Exit:** route remains inherited and P2 is `UNSUPPORTED`, or the documented API is recorded in a separate `DESIGN_READY` host-specific plan. This task does not implement the adapter. No API is inferred from a host label.

### Task 4: Define and test the P3 journal v2 recovery contract

**Files:**
- Modify: `experiments/multi-agent-evolution/journal.py`
- Modify: `tests/test_journal.py`
- Modify: `docs/superpowers/specs/2026-11-18-multi-agent-evolution-design.md`, `docs/technical/multi-agent-evolution.md`, status report

**Interfaces:** Preserve `Journal(path).create_run(...)`, `.transition(...)`, `.get_run(...)`, `.export(...)`. Each v2 event adds `attempt_id: non-empty str`, `attempt_revision: exact int`, `parent_event_id: str|null`, `actor_claim: {role: non-empty str, identity: non-empty str, session_ref: non-empty str}`, `criteria_ref: non-empty str`, optional `candidate_artifact: {path: relative str, sha256: lowercase 64-character hex}`, `terminal_reason: str|null`, and `approval_ref: str|null`; the event allowlist rejects unknown fields and required terminal fields are checked by state. Booleans are invalid for integer fields. An explicit transition from `REWORK_REQUIRED` to `READY` starts a new attempt and increments `attempt_revision`; other transitions retain the attempt identity. Add `Journal.open_readonly(path: Path) -> Journal` for legacy v1 export only; mutation through this instance raises `JournalError`. Add `Journal.verify_run(run_id: str, evidence_root: Path) -> dict` returning `{"integrity_status": "PASS|FAIL|BLOCKED|UNVERIFIED", "checks": [{"name": str, "status": str, "detail": str}]}` and `Journal.reconcile(run_id: str, evidence_root: Path) -> dict` returning `{"run_id": str, "recovery_status": "COMPLETE_RECORD|RECOVERY_REQUIRED|BLOCKED|UNVERIFIED", "last_verified_revision": int|null, "reason_codes": [str]}`. `COMPLETE_RECORD` means the stored terminal state and rooted artifact integrity are locally consistent; it does not authenticate the actor, approval, or native execution. Reason codes include `REVISION_GAP`, `DUPLICATE_EVENT`, `MISSING_CANDIDATE`, `DIGEST_MISMATCH`, `UNVERIFIED_ACTOR`, and `UNVERIFIED_APPROVAL`. Reconcile is read-only and never dispatches or changes a run. General `evidence_refs` remain opaque strings; only the explicit candidate artifact descriptor is read, relative to a caller-supplied root. Actor/session fields are claims and remain `UNVERIFIED` without supported host attestation.

- [x] **Step 1: Add failing contract tests.** Cover exact integer revisions (booleans rejected), malformed/unhashable state and payload types, monotonic run/attempt revisions, unique event IDs and causal parent identity, valid/invalid transitions, and v1 database preservation/read-only export with v2 refusal (no implicit migration). Verify acceptance requires all fields; candidate bytes are hashed under explicit root; digest mismatch fails; absent/corrupt candidate blocks; absolute/traversal/symlink escape/FIFO references are never read outside a regular in-root file; actor/approval claims remain unverified; recovery never replays writes or manufactures approvals.
- [x] **Step 2: Run tests red.** `python -B -m unittest tests.test_journal -v`. Confirm each new behavior fails for the stated reason; do not change an expected result to match implementation.
- [x] **Step 3: Implement schema and APIs.** Keep SQLite transactions/CAS and allowlists. Add a documented v2 schema; preserve v1 files and provide read-only export, but reject v1 mutation/open as v2 with an actionable error. `verify_run` reports local artifact integrity only; `reconcile` returns `RECOVERY_REQUIRED` for interrupted/uncertain state and performs no dispatch or write replay.
- [x] **Step 4: Add fault tests.** Exercise duplicate/reordered events, crash points around event insert/state update/commit, competing revisions from separate connections, invalid export/import, event-chain inconsistency, and reopen/export stability. Use deterministic injection rather than timing sleeps.
- [x] **Step 5: Verify.** Run journal tests plus full tests. Cross-platform claims require actual Windows/Linux CI evidence; otherwise label the untested platform `UNVERIFIED`. Confirm journal stays outside both runtime bundles.
- [x] **Step 6: Update docs and commit.** State exact local checks and the continuing limits on host authentication, cross-platform durability, and approval provenance. Commit `feat: add fail-closed local journal reconciliation`.

**Exit:** local file integrity and event consistency are reproducible; recovery never silently resets or dispatches; identity and approval claims are not promoted. If atomic recovery/portability cannot be shown, keep P3 `EXPERIMENTAL` and do not make it a runtime prerequisite.

### Task 5: Qualify P4 isolation without enabling unproven parallel writes

**Files:**
- Modify only the pure graph helper if a test reveals a defect: `.agents/skills/council-flow/scripts/task_graph.py`, `tests/test_task_graph.py`
- Add an isolated harness only after the actual OS mechanism is identified and approved; document in `docs/technical/multi-agent-evolution.md` and status report

**Interfaces:** `validate_graph(nodes, plan_revision)` remains a pure validator. A workspace launcher is outside the current helper and must not be added until a documented OS sandbox API and rollback design exist.

- [ ] **Step 1: Add isolation controls.** Define tests where worker A attempts read/write through direct path, symlink/reparse path, inherited process handle, and concurrent/stale-base promotion into worker B's workspace. Require the OS sandbox, not application path checks, to deny access.
- [ ] **Step 2: Verify the baseline.** Run graph tests and confirm the existing environment's declared/actual permissions. No model agents or mutating tasks are started.
- [ ] **Step 3: Decide by evidence.** If a host/OS sandbox provides enforceable deny controls, implement a disabled-by-default adapter plus conflict, stale-base, failed-promotion, and rollback tests. If not, record `ISOLATION_BLOCKED` and make no scheduler or parallel mutation feature.
- [ ] **Step 4: Verify promotion semantics.** Any combined candidate gets a fresh independent Tester/Reviewer pass against original criteria. Conflicted, stale, or partial promotion must leave trusted source untouched.
- [ ] **Step 5: Commit.** `feat: add isolated workspace qualification` or `docs: keep P4 parallel writes blocked`.

**Exit:** demonstrated cross-workspace deny and serialized promotion, or an explicit `ISOLATION_BLOCKED` result with serial mode retained.

### Task 6: Complete P5 memory/doctor evidence tests without granting memory authority

**Files:**
- Modify if needed: `.agents/skills/council-flow/scripts/experience.py`, `doctor.py`, `tests/test_experience.py`, `tests/test_doctor.py`
- Modify: matching `plugins/councilflow/skills/run/scripts/` mirrors, `docs/technical/multi-agent-evolution.md`, status report

**Interfaces:** Every experience entry keeps `review_status: UNVERIFIED`. `select_entries` remains metadata filtering only. Doctor schema v1 keeps its current result contract unchanged. Schema v2 adds nullable `executable_artifact: {path: str, sha256: lowercase 64-character hex}` and `native_host: {name: non-empty str, version: non-empty str, evidence_ref: non-empty str}` objects; both fields must be present in v2, with `null` meaning absent evidence. V2 emits checks named `executable_integrity` and `native_host`; the first can `PASS` only when regular-file bytes under the configured root match the declared digest, and the second stays `UNVERIFIED` for a valid caller record. It does not execute the path or discover/authenticate a host. Null/absent evidence is `BLOCKED`, malformed records or digest mismatch are `FAIL`; unknown schema versions fail.

- [ ] **Step 1: Add adversarial fixtures.** Test poisoned/stale/superseded/wrong-project entries, duplicate IDs, malformed review claims, and proof that returned entries never gain verification or enter Worker context. Test v1 doctor output remains unchanged, v2 accepts nullable executable/host records but reports absent records `BLOCKED`, malformed records/unknown versions fail, duplicate keys fail, source and executable digest mismatch fail, and symlink/FIFO evidence never gets read. No test launches a caller-specified executable.
- [ ] **Step 2: Run tests red.** `python -B -m unittest tests.test_experience tests.test_doctor -v`.
- [ ] **Step 3: Implement only rooted byte checks and structural host-reference checks.** Do not add executable invocation or host discovery. Do not create a dashboard. If a dashboard becomes an actual available integration, prepare a separate read-only projection proposal with privacy/retention data; never make it an authorization source.
- [ ] **Step 4: Verify.** Focused tests, package sync/check, full tests, package rebuild, and diff review. All entries and native claims remain visibly unverified.
- [ ] **Step 5: Commit.** `test: harden P5 memory and doctor boundaries` or a scoped implementation commit if actual changes are required.

**Exit:** poisoning and missing-evidence cases fail closed; no memory is auto-injected and no dashboard/runtime is invented.

### Task 7: Execute P6 only after P1–P3 evidence gates are complete

**Files:**
- Read: `experiments/agent-efficiency/evaluation/PROTOCOL.md`, `RUNBOOK.md`, `protocol.draft.json`
- New run artifacts: only in ignored `.local-runs/` or an explicitly approved external directory
- Modify evaluator only under a separately tested contract: `experiments/agent-efficiency/evaluate.py`, `test_evaluate.py`

**Interfaces:** Each candidate is a frozen manifest compared to an unchanged baseline. The evaluation result includes failed/censored attempts, independent Tester/Reviewer outcomes, unknown measures, and a written `CLOSED_NO_BENEFIT`, `INCONCLUSIVE`, or `BENEFIT_OBSERVED` only under a separately approved confirmatory protocol; no automatic promotion.

- [ ] **Step 1: Preflight checklist.** Compare the proposed phase card against required task/oracle hashes, verifier bindings, route, telemetry, budget, stop mechanism, retention, effect threshold, and reliability rule. Do not add a readiness service; any missing value means no live run.
- [ ] **Step 2: Run existing evaluator tests.** `python -B -m unittest discover -s experiments/agent-efficiency -v`; correct no failure by weakening controls.
- [ ] **Step 3: Seal the experiment.** Only after a phase card is explicitly approved, freeze task copies/oracles, order, retries, host/route, candidate, output manifests, all-role call/time/quota/cost ceilings, stop operator, independent verifiers, and analysis rules before the first call. Use no production repository as a task fixture.
- [ ] **Step 4: Run one authorized block.** Preserve every failed, timed-out, abandoned, repaired, and censored attempt. Stop at first bound or safety breach. Do not enlarge budgets or retry a failed route without new approval.
- [ ] **Step 5: Analyze and review.** Report uncertainty and missing telemetry; do not claim benefit from the six-task feasibility pilot or use `evaluate.py` output as authorization. Require independent replay and Owner decision before a new proposal.
- [ ] **Step 6: Commit evidence metadata only.** Keep prompts, credentials, and private conversations out of the repository. Publish no model call data without an explicit retention/sharing decision.

**Exit:** an approved feasibility pilot yields `INCONCLUSIVE` or `CLOSED_NO_BENEFIT`. `BENEFIT_OBSERVED` is unavailable unless a separate confirmatory protocol is approved and completed. No production configuration changes.

### Task 8: Decide whether P7 warrants a separate project

**Files:** create a separate design only if required; do not modify CouncilFlow runtime in this task.

**Interfaces:** The board has no repository access, process execution, provider credentials, or authority to import plans. Submitter/model identity is a claim until independently evidenced.

- [ ] **Step 1: Threat model.** Define forged/replayed submissions, poisoned instructions, stale plan revisions, secret-bearing inputs, retention deletion, attribution, and Owner-approved import controls.
- [ ] **Step 2: Make an explicit outcome.** Either `NOT_APPLICABLE` with rationale or a separate authorized prototype spec. No service is built as part of P0–P6.
- [ ] **Step 3: Commit decision.** `docs: record P7 separate-project decision` only if a durable decision is needed.

**Exit:** P7 remains optional and cannot block the core phase program.

### Task 9: Whole-program verification and closeout

**Files:** status report and any phase evidence docs; generated artifacts only if source packages changed.

- [ ] **Step 1: Run** `python -B -m unittest discover -s tests -v` and `python -B -m unittest discover -s experiments/agent-efficiency -v`.
- [ ] **Step 2: Run** `python -B tools/build_claude_plugin.py sync`, `check`, and `build`; run `python -B tools/build_release.py` if release sources changed. Then run `git diff --check` and inspect staged/generated ZIP contents.
- [ ] **Step 3: Verify** canonical/Claude runtime file equality; list changed files; compare current base/candidate hashes; record exact pass/fail/skip counts and phase status. Fresh independent Reviewer checks P0–P6 claims and unresolved risk list.
- [ ] **Step 4: Close every phase** as `COMPLETE`, `BLOCKED_*`, `NO_GO`, or `NOT_APPLICABLE`; do not leave an implied green state. Any final commit or push updates only the feature branch. No merge/release occurs under this plan.
- [ ] **Step 5: Commit and publish the plan's execution evidence** on the feature branch only. Do not merge or release.

## Execution order and parallelism

Execute Tasks 1–4 sequentially. Task 5 depends on Task 4. Task 6 depends on stable P3/P1 evidence semantics. Task 7 depends on P1 and P2, and on P3–P5 only when its design uses them. Task 8 is separate and may be omitted. Task 9 closes the selected scope. Do not parallelize tasks that modify shared package files or the same reports.

## Preflight fields that cannot be guessed

The following are deliberately not fabricated in this plan. Fill them once for the relevant phase; absent values block only that phase:

- **Any native host task:** host and version, supported adapter documentation, access method, exact allowed commands, sanitized evidence location, and operator available to observe failures.
- **Any model trial:** route/model, task/oracle set, independent verifiers, complete all-role calls/quota/cost/time bounds, telemetry retention, effect/reliability rule, and stop mechanism. Current protocol does not authorize a trial.
- **Any durable user data:** selected storage path, backup, retention/deletion, migration compatibility, encryption/permissions owner, and recovery owner. Until approved, tests use disposable temporary databases only.
- **Any parallel mutation:** OS sandbox mechanism/version, actual deny test, workspace layout, rollback, and serialized merge/promotion owner. Until demonstrated, only serial mutation is allowed.
- **Any external source/dependency or distribution decision:** license outcome, source version/hash, maintenance/security case, and distribution approval.

These are real external constraints. The plan prevents surprise blockers by listing them before work, but cannot guarantee access, API support, spend authorization, or OS isolation that is not available in the eventual execution environment.
