# Multi-Agent Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement compatible offline improvements from the evolution proposal as optional CouncilFlow skill extensions while preserving the native host workflow and Owner authority.

**Architecture:** Add pure schemas/helpers to the canonical Codex skill, mirror shared files into the Claude plugin using repository release tooling, and test each helper with standard-library unittest. Durable state is explicitly opt-in; no module launches a model or changes host configuration. Parallel mutation remains disabled until OS isolation is proven.

**Tech Stack:** Python 3.11+, standard library only in product runtime; unittest; JSON; experimental SQLite journal outside the package.

**Spec:** `docs/superpowers/specs/2026-11-18-multi-agent-evolution-design.md`; source proposal `docs/multi-agent-evolution-plan-2026-11-17/`.

## Global Constraints

- Preserve Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner.
- Preserve original plan bytes, criterion IDs, candidate identity, independent Tester/Reviewer and final Planner checks.
- No paid model calls, provider routes, configuration/credential changes, permission changes, publication, release or merge.
- Unknown host capability, model identity, route, usage or spend stays unknown.
- Existing behavior stays unchanged unless an opt-in interface is explicitly invoked.
- Python 3.11+ standard library only; no new runtime dependency.
- Keep shared runtime copies byte-identical in `.agents/skills/council-flow/` and `plugins/councilflow/skills/run/`.

## Review Focus

- Malformed or future-version JSON must fail closed — test invalid/duplicate keys and unknown versions in each schema owner.
- Stale or duplicate journal transitions must never accept a run — test revision mismatch and replay.
- Journal paths are opaque references and never dereferenced — test that traversal-like strings are retained as references only.
- Missing/poisoned memory must not become Worker authority — test untrusted provenance and superseded entries.
- Absent native host capability must never be green or select a guessed model — test unknown capability and inherited fallback.

---

### Task 1: Role preference and capability contract

**Files:** Create canonical `scripts/role_capabilities.py`, tests `tests/test_role_capabilities.py`; mirror to Claude package and document in the skill references.

**Interfaces:** `validate_profile(data: object) -> dict`; `resolve_role(profile: dict, capabilities: dict, role: str) -> dict`; unknown/unsupported selection returns explicit `INHERIT_HOST` or `BLOCKED_UNSUPPORTED` with null model identity.

- [x] Write tests for valid schema, malformed values, unsupported role override and inherited fallback.
- [x] Run focused tests and confirm expected failures.
- [x] Implement strict versioned schema and pure resolution function; caller supplied capability is `UNKNOWN`.
- [x] Run focused tests, existing contract tests and package synchronization check.

### Task 2: Opt-in local journal

**Files:** Create experimental `experiments/multi-agent-evolution/journal.py`, tests `tests/test_journal.py`; update docs only after API stabilized.

**Interfaces:** `Journal(path).create_run(...)`, `.transition(run_id, expected_revision, new_state, payload, event_id=None)`, `.get_run(run_id)`, `.export(run_id)`. Store metadata and evidence references only; transition is a SQLite transaction with revision compare-and-swap. Keep this prototype under `experiments/multi-agent-evolution/`, outside the installed skill, because current product tests prohibit SQLite runtime code.

- [x] Write tests for valid transitions, stale revision, duplicate event, skipped required role, restricted payload and deterministic export.
- [x] Verify failures before implementing.
- [x] Implement schema-versioned local journal; never auto-create unless the caller explicitly constructs it with a path.
- [x] Verify required transitions and acceptance references; actual artifacts are not dereferenced or independently hash-verified.

### Task 3: Dependency graph validation

**Files:** Create `scripts/task_graph.py`, `tests/test_task_graph.py`.

**Interfaces:** `validate_graph(nodes: list[dict]) -> GraphValidation`; report missing prerequisites, cycles, blocked descendants, and stable topological order. No scheduler or workspace writes.

- [x] Write tests for valid DAG, missing dependency, cycle, blocked parent and stale plan revision.
- [x] Verify expected failures.
- [x] Implement pure graph validation only.
- [x] Verify tests and document that parallel mutation remains disabled.

### Task 4: Reviewed memory records

**Files:** Create `scripts/experience.py`, `tests/test_experience.py`.

**Interfaces:** `validate_entry(entry: object) -> dict`; `select_entries(entries, project_scope) -> list`. Filter caller-claimed review entries by scope and supersession, while returning `review_status: UNVERIFIED`; this is metadata only and is not injected into Worker context.

- [x] Test missing provenance, wrong scope, supersession and deterministic ordering.
- [x] Verify expected failures.
- [x] Implement schema and filtering.
- [x] Verify tests; document manual review and no automatic retrieval/injection.

### Task 5: Deterministic diagnostics

**Files:** Create standalone `scripts/doctor.py`, `tests/test_doctor.py`; do not change default skill behavior.

**Interfaces:** `diagnose(evidence: dict) -> list[dict]`; statuses only `PASS`, `FAIL`, `BLOCKED`, `SKIP`, `UNVERIFIED`. Missing events/capabilities can never yield PASS.

- [x] Test missing native role/session evidence, duplicate JSON keys, and caller-claimed outcomes.
- [x] Verify expected failures.
- [x] Implement deterministic evidence-only diagnostics; unverified claims never pass.
- [x] Verify CLI and unknown-state formatting.

### Task 6: Phase evidence and portfolio report

**Files:** Update `reports/multi-agent-evolution-baseline-2026-11-18.md`; add phase status report and update technical docs. Do not change frozen Gate 3 records.

- [x] Record implemented offline evidence and remaining gates by plan phase.
- [x] Mark P1 live trial, P2 native activation, P4 isolation, P6 live optimization, and P7 separate room as blocked/unverified where actual evidence is absent.
- [x] Run repository tests and release build checks; review candidate file list and hashes (review fixes require one final rerun).

## Deferred by plan gates

- Live P1/P2/P6 model calls and A/B experiments: no explicit spend ceiling/host stop mechanism in the execution context.
- OS-enforced P4 parallel workspace isolation: cannot be established by code declarations alone.
- P7 independent-model council room: optional product-adjacent project requiring its own privacy/authentication threat model and persistence scope.
- External release, merge or promotion to `main`.

### Review follow-up scope (2026-11-19)

**Scope:** resolve the two important review findings and the stale-DAG minor finding without expanding runtime authority.

1. [x] **Memory provenance:** rename the input field to `review_claim`; allow only the literal `owner_reviewed` as a claim, attach `review_status: UNVERIFIED` to all validated/selected entries, and clarify docs that the helper does not authenticate an Owner. Add tests showing claims never become verified.
2. [x] **Tracked package outputs:** retain deterministic `dist/` archives because the repository test suite checks they match source. Clarify the design/status docs that regenerating tracked artifacts is a consistency operation, not release promotion or publication. Keep the generated archives in the branch.
3. [x] **Stale DAG revisions:** mark stale tasks blocked and propagate blocking to descendants. Add tests for stale parent and child; invalid graph continues to return an empty execution order.
4. [x] **Verification:** focused RED/GREEN tests, full `tests/` (264 passed, 1 platform skip), package sync/build checks, and `git diff --check` passed. Commit and push this feature branch.
