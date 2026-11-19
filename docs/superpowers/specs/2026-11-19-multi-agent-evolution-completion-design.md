# Multi-Agent Evolution Completion Design

**Status:** Proposed execution roadmap on the existing feature branch. It authorizes no model calls, provider changes, host configuration edits, permission changes, merge, product release, or promotion.

## Intent

Plan the remaining work in the 2026-11-17 Multi-Agent Evolution proposal after the offline helpers and 2026-11-19 audit follow-up. The roadmap must let an implementer start each eligible phase with exact scope, prerequisites, tests, and stop conditions, while making external host or Owner decisions visible before that phase starts.

## Goals

- Finish the read-only baseline gaps and reconcile current branch and remote state before designing further work.
- Mature the journal only as far as evidence and supported host APIs allow; never describe a metadata prototype as recovery or authentication.
- Keep offline qualification separable from any live model, host, or parallel-write experiment.
- Define phase entry cards with exact paths, base revision, native host/version, network/spend limits, acceptance, stop triggers, and rollback before consequential work.
- Keep the core CouncilFlow roles, frozen criteria, and serial mutation default unchanged.
- Allow phases to finish `BLOCKED`, `NO_GO`, or `NOT_APPLICABLE` with evidence and no unnecessary code changes.

## Non-goals

- No execution of the phases in this design task.
- No payment, model/provider call, route/configuration change, secret access, permission change, CI activation, merge, product release, or promotion.
- No importing upstream code or adding dependencies before the repository license and dependency case are resolved.
- No claim that path declarations, Git worktrees, structural JSON, or caller identity fields provide security or native-session authentication.
- No dashboard or opinion-board service unless a separate approved need and existing integration point are established.

## Constraints

- Preserve Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner and the Gate 3 Owner Charter.
- Keep `main` unchanged; execute implementation on a feature branch rooted in a freshly recorded main revision.
- Keep all runtime helpers standard-library-only unless a specific dependency is approved and justified.
- Maintain `UNVERIFIED` for unsupported host identity, evidence provenance, routes, usage, spend, or approval claims.
- Do not make P4 parallel mutation available without demonstrated OS-enforced isolation and serialized verified promotion.
- Never treat branch publication as product release or promotion.

## Approaches

1. **One combined release implementation:** build P1–P7 as one large change. Rejected because host, journal, isolation, and product-adjacent work have different prerequisites and independent failure outcomes; this would let one unavailable host gate block offline work and make review difficult.
2. **Dependency-ordered completion program with separately gated work packages (selected):** complete P0 first, then mature the offline foundations, then execute host-dependent work only with a filled phase entry card. Keep P7 separate and optional. This follows the existing phase dependencies and permits a clear `NO_GO` without weakening the core workflow.
3. **Stop at the offline prototype:** retain the current code and do no further preparation. Rejected because the user asked for a thorough implementation plan and the remaining work can be specified now even where execution remains externally gated.

The selected approach creates one master plan for coordination and requires a focused implementation plan/design before any later independent product or host integration is started.

## Phase model and entry rules

Every phase begins with a card containing: phase/work-item ID; exact objective and allowed/forbidden paths; current base SHA and candidate branch; required host and version; required local tools; network permissions; maximum calls and spend (or `0`); data classes and retention; frozen acceptance IDs; independent Tester/Reviewer commands; stop conditions; rollback; and decision owner.

Missing external inputs do not stop unrelated read-only or offline tasks. The affected work item is recorded as `BLOCKED_OWNER_INPUT` or `BLOCKED_HOST_CAPABILITY`, with the exact missing field. A phase can close `NO_GO` or `NOT_APPLICABLE`; it must not fabricate a capability or silently weaken acceptance to avoid a stop.

The user's existing authorization covers the compatible offline implementation on the published feature branch; it does not require asking again before each offline task. The old backlog's `NOT AUTHORIZED` label predates that instruction and remains historical context, not a new veto. No exact paid-call budget, model route, host configuration change, permission change, or public-service scope was supplied, so these are not inferred from the offline authorization.

The separate `docs/development-runs/2026-11-audit-remediation/` slices are not absorbed into this program. P0 handles only the license/source-reuse decision relevant to this roadmap and a current evidence refresh; P1/P2 consume native-host evidence from Slice 03 when available. The unrelated documentation/CI/distribution scope of Slice 02 and the value-measurement scope of Slice 04 remain separately gated. This avoids duplicate ownership while preserving their outputs as dependencies.

The required sequence is:

1. **P0 completion:** refresh the repository baseline, inspect available GitHub branch/PR state, inventory current artifacts and test commands, record the unresolved license question, and correct documentation that conflates branch push with release publication. Code reuse remains disallowed until license status is settled; work that uses only existing code and standard library can proceed.
2. **P1/P2 readiness:** preserve current offline `NOT_APPROVED` result. Separately document exact native host, supported interfaces, route identity, test task, call/spend cap, stop control, and approval needed for any live qualification. If the host exposes no documented capability API, close the routing adapter work as `UNSUPPORTED` and keep inheritance behavior.
3. **P3 journal foundation:** design event/attempt identity, actor claim fields, state transitions, artifact reference semantics, and retention before code. Extend the SQLite prototype behind tests. General evidence references stay opaque; a specific candidate-artifact descriptor can be byte-checked only under an explicit root. Local hashes can be recomputed only for regular in-root files; actor/session authentication remains unverified unless a supported native host attestation API exists. Recovery is report-only, fails closed on absent/stale evidence, and never dispatches or replays writes. Legacy v1 databases are preserved and readable for export, not silently migrated.
4. **P4 isolation:** remains dependent on stable P3 identities and a real isolation mechanism. Prove a worker cannot read or modify a sibling workspace using OS-enforced controls; Git worktree separation alone is insufficient. If no supported sandbox can be established, retain serial mutation and close the isolation item blocked.
5. **P5 memory/diagnostics:** build on stable P3 evidence semantics and P1 provenance limits. Keep lessons as caller-claimed metadata and outside Worker context by default. Add adversarial retrieval/poisoning tests before any opt-in retrieval. Preserve doctor schema v1 behavior; schema v2 may check explicit executable bytes under a root and structurally validate a host reference, but it never executes a caller path or discovers/authenticates a host. Mark host identity unverified and missing required references blocked.
6. **P6 optimization:** depends on an approved P1 baseline, P2 route provenance when comparing models, reproducible P3 attempts, and P4/P5 only where the experiment uses those capabilities. Freeze task bytes, oracle, retries, route, budget, and objective before a paired run. No candidate is promoted automatically.
7. **P7 opinion board:** optional, separate design and authorization. It is not a prerequisite for core completion and is not bundled with P3–P6.

## Success criteria

- The completion plan is executable task-by-task without unresolved file/API/test choices for offline work.
- Every external dependency is mapped to a specific phase card field and a fail-closed status.
- Current branch facts and known P0 gaps are recorded from evidence.
- Each phase has measurable entry, exit, `NO_GO`/blocked, and rollback outcomes.
- No text implies that unimplemented host, recovery, isolation, review, optimization, or board behavior is already available.
- The implementation plan distinguishes the offline path that can proceed from phases that require later Owner/host inputs.

## Decisions fixed for the builder

- Keep the published feature branch and do not merge or modify `main` in the planning or execution phases described here.
- Treat P7 as optional and separately gated.
- Keep live model/spend work at zero unless an explicit phase card provides a numeric ceiling and stop mechanism.
- If license status, host APIs, or enforceable isolation cannot be established, record the limit and proceed only with independent offline tasks.
