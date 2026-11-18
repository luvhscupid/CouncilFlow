# Multi-Agent Evolution Implementation Design

**Status:** Authorized branch implementation design; no live model calls, provider routing, global configuration, OS permission changes, external publication, or release promotion.

## Intent

Implement the compatible parts of the 2026-11-17 evolution plan as optional, offline-capable extensions to the existing CouncilFlow skill. The audience is CouncilFlow maintainers and users who need accurate capability/provenance reporting, recoverable run metadata, and deterministic diagnostics without replacing host-native delegation.

## Goals

- Preserve the Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner workflow and all frozen acceptance/source-fidelity requirements.
- Make model preference distinct from actual host capability and observed model/route identity; unsupported selection inherits the host and reports that fact.
- Add an opt-in local journal with explicit state transitions and fail-closed recovery validation.
- Add deterministic offline checks for task dependencies and phase/evidence health; keep parallel mutation disabled unless real OS isolation is independently proven.
- Reuse current efficiency helpers and structured contracts; keep experimental features disabled by default.
- Keep Codex and Claude package copies synchronized through existing build tooling.

## Non-goals

- No model/provider calls, live A/B evaluation, claims of lower cost, or use of Package D as an authorized trial.
- No credential/configuration inspection or mutation, OAuth reuse, API gateway, permission changes, OS sandbox, server, dashboard, autonomous coding agent, auto-merge, deployment, release, or main-branch changes.
- No weakening of the Owner Charter, frozen plans, role independence, independent Tester/Reviewer checks, or original evidence requirements.
- No import of upstream code; only independent implementations of compatible concepts.

## Constraints

- Python 3.11+ and standard library only for runtime helpers.
- Optional local state; no prompts, model reasoning, secrets, or raw conversations in the journal.
- Unknown capability, route, identity, usage, or spend stays null/unknown and is never treated as passing evidence.
- Existing defaults remain unchanged; optional routing must resolve to inherited host unless explicit documented host support is supplied as evidence.
- Parallel writes remain disabled by default and are not represented as secure based on path declarations or advisory locks.
- Only `evolution/multi-agent-plan-2026-11-17` is modified; `main` remains unchanged.

## Approaches

1. **Schema and read-only capability probe first (selected).** Build validated metadata contracts and a probe that consumes explicit documented capability input, with safe unknown defaults. This is testable offline and does not misrepresent host support.
2. **Add a selector shim in the first slice.** It could select only when a host-specific adapter is available, but no verified selection API is available in this environment; implementing it now risks creating a nonfunctional or misleading route layer.
3. **Skip model capability work.** This avoids the risk but leaves a central plan gap unaddressed despite the ability to build a truthful offline contract.

## Implementation decisions

- The first routing deliverable is a versioned profile/capability schema and a pure resolver. It may return `INHERIT_HOST` or `BLOCKED_UNSUPPORTED`; it does not launch or configure models.
- The experimental journal uses the Python standard library SQLite API outside the installed skill because current product tests forbid SQLite runtime code. It stores metadata/evidence references, not evidence payloads. It is not integrated into runtime or treated as an authorization source.
- Recovery validates current plan revision, attempt identity, candidate and evidence hashes. It never invents role execution or Owner approval.
- DAG validation is a pure offline contract. Scheduling and parallel workspace mutation remain disabled; no worktree isolation is claimed.
- Reviewed memory is a manually curated metadata format with provenance/supersession; no automatic model retrieval or Worker injection is enabled.
- Diagnostics report `PASS`, `FAIL`, `BLOCKED`, `SKIP`, or `UNVERIFIED`, never green for absent evidence.
- P6 remains offline evaluator/manifest work only; live experiment stays blocked. P7 is documented as deferred because it is product-adjacent and separately gated by its own threat model.

## Acceptance

- Offline tests prove schema validation, inherited fallback, unsupported routing behavior, journal compare-and-swap/replay safety, DAG cycle/missing prerequisite handling, memory provenance/supersession checks, and non-green unknown diagnostics.
- Existing helper, contract, release-build and demo tests remain passing.
- Codex and Claude packages contain byte-identical shared runtime files.
- No model calls, user configuration edits, permission changes, or promotion occur.
- Report explicitly distinguishes offline implementation evidence from native host evidence, which remains `UNVERIFIED` unless actually observed.

## Remaining builder decisions

- Pick stable names and file boundaries consistent with existing Python modules.
- Keep persistent state opt-in and ensure default skill behavior performs no database writes.
- Use disposable temporary databases and workspaces in tests, with cleanup guaranteed.
