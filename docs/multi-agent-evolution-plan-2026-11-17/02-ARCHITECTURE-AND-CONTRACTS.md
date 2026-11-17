# 02 — Proposed target architecture and contracts

**Status:** DESIGN_PROPOSAL, not normative. No claims of actual runtime enforcement. Prefer optional scripts/adapters inside the existing Codex/Claude skill packages. Do not add a mandatory server or runtime.

## Fixed invariants

1. Owner -> Planner -> parent Manager -> fresh Worker -> independent Tester -> independent Reviewer -> Manager -> Planner final check -> Owner. Reviewer is a non-mutating three-way evidence comparator and reruns one Tester-declared deterministic command; it is **not** an automatic code repairer or a mandatory UX score.
2. Preserve exact original Owner criteria, original-source provenance and stable criterion IDs. No compact summary, model prompt, cache, experience memory or optimizer can overwrite source bytes.
3. Manager may orchestrate and request routine authorized rework, but does not implement application code, grant privileges or loosen scope. Planner writes plans/checks outcomes, not code.
4. Worker is new per attempt; Tester/Reviewer are independent of it. Only one Worker mutates a workspace. Unrelated tasks can run concurrently **only in actually isolated, separately approved workspaces**, with deterministic serialized promotion.
5. JSON/YAML policies are not authentication or OS security. Host-enforced permissions and Owner authorization prevail; unknown model route != verified route.
6. No new API key, external provider, OAuth-token harvesting, global configuration change, paid call, deployment, auto-merge or release without its own explicit approval.
7. A parser PASS is not native role activation. A successful command digest is not independent Tester or Reviewer acceptance. Missing evidence -> UNKNOWN, UNVERIFIED or BLOCKED, never an inferred PASS.
8. Existing efficiency helpers stay opt-in unless a later approved phase explicitly changes defaults.

## Logical components (implementation boundaries)

```text
User / approved plan
       |
Manager inside host (Codex / Claude Code)
  |-- native role delegation (Planner, Worker, Tester, Reviewer)
  |-- proposed capability router (preferences -> observed host adapter capability)
  |-- proposed local journal / task graph (non-authoritative until tested)
  |-- existing validation / source fidelity / digest / adapters
  |-- optional safe context retrieval (CBM, reviewed lessons)
  |
Host permissions / real workspaces / host-native model access
       |
Candidate + immutable evidence references
       |
Independent Tester -> Reviewer -> Planner final check -> Owner
       |
Optional dashboard: read-only projection of verified events
```

**Control versus data:** Owner decisions, plan revisions and approval provenance are control records. Worker files, independent command output, model responses and run traces are data. A dashboard is only a projection; it never becomes the source of authority.

### A. Model capability binding

The Manager selects roles according to task complexity and risk, but selection is bounded by **what the host actually exposes**. Two layers:

- `role_policy`: desired provider/model class, reasoning effort, independence constraints and fallback preferences. No hardcoded universal mapping to Luna/Haiku/Sol.
- `host_adapter_capabilities`: observed provider configuration *without credentials*, host version, native delegation available, explicit model selection supported, independent per-role override supported, supported effort settings, and whether usage can be observed.

Proposed metadata, illustrative only:

```json
{
  "task_class": "bounded_offline_change",
  "role": "worker",
  "preference": "lower_cost_if_qualified",
  "configured_model": null,
  "reported_model": null,
  "effective_upstream_model": null,
  "route_kind": "native_subscription_or_configured",
  "route_verified": false,
  "capability_evidence_ref": null,
  "fallback": "inherit_host_and_label_it"
}
```

**Rules:** Capture actual model identifiers from trustworthy host/provider metadata if available; self-declared agent text never proves upstream identity. A logical role label is not a model ID. Do not rewrite user's xKiro route or Claude settings. Respect native subscription boundaries; do not treat ChatGPT Plus, Claude subscriptions or an OAuth login as a transferable API entitlement. If per-role model selection is unsupported, explicitly use inherited host model and label `ROLE_MODEL_INHERITED`, or block the opt-in experiment rather than pretending routing worked.

### B. Proposed durable run journal

A minimal optional SQLite prototype can coordinate local metadata, not replace frozen source artifacts or act as a trusted Supervisor without separate enforcement work. Prefer a single-writer transaction boundary and compare-and-swap (`run_id`, `revision`, `attempt_id`, `candidate_sha256`) for state transitions. SQLite is a proposal, not an existing capability or permission to add a dependency. If a file journal is tested instead, prove atomicity and crash behavior independently; plain append-only JSONL is diagnostics, **not** a crash-safe authoritative ledger.

States: `PLANNED -> READY -> ASSIGNED -> RUNNING -> CANDIDATE -> TESTING -> REVIEWING -> MANAGER_DECISION -> PLANNER_CHECK -> ACCEPTED`. Alternative terminal states: `BLOCKED`, `REJECTED`, `CANCELLED`. `REWORK_REQUIRED` creates a **new attempt**; do not mutate the already tested candidate in place.

Each transition should store `run_id, task_id, attempt_id, plan_id, plan_revision, original_source_ref, criteria_ids, candidate_ref/hash, actor_instance, host_observed_identity, event_type, parent_event_id, status, monotonic_sequence, evidence_refs, timestamp_if_observed, reason`. Separate desired/actual status; `RUNNING` without a live process/session becomes `RECOVERY_REQUIRED`, not silently `PASSED`.

Essential invariants: no duplicate acceptance, no skipped Tester/Reviewer/Planner; stale attempt cannot replace a newer candidate; inability to validate evidence/hash must fail closed; interrupted validation is resumable from recorded references, not a recollection from a model. On reentry verify repository revision, host permissions and exact candidate/evidence hashes. Retain bounded retries in policy, with actual runtime accounting only after demonstrated.

### C. Dependency graph and workspace coordination

Task graph node: `task_id, scope, prerequisites, acceptance_ids, candidate_input_ref, assigned_role, status, expected_touched_paths, worktree_id, verification_ref`. Edges must be acyclic; blocked prerequisites should stop downstream dispatch. A task that requires an unapproved change remains blocked; no auto-scope expansion.

For future parallel mutating Workers: each gets an **independent Git worktree or equivalent isolated clone** and non-overlapping delegated scope, with host-enforced sandbox boundaries. Predictive path declarations aid scheduling but are not security locks. Before promotion, revalidate base commit, manifest and conflicts; perform serial merge/cherry-pick in trusted Owner-authorized execution. Cross-task integration requires fresh Tester/Reviewer verification on **promoted combined candidate**, not simply union of earlier green reports. Branch/merge promotion remains Owner gated when consequential.

### D. Context and experience handling

Keep four tiers:
1. **Authoritative:** original goal, frozen source bytes, plan, acceptance IDs, security policy, evidence manifests. No lossy compaction.
2. **Operational:** bounded task-specific files, exact candidate and command output refs; the existing digest/expand helper is preferred.
3. **Reviewable memory:** vetted, versioned decision/lesson entries with `kind, provenance, scope, applicability, superseded_at, evidence_refs`.
4. **Disposable:** chat history, speculative thoughts, verbose logs, unverified model opinions.

Context selection by role:
- Planner: goal, frozen constraints, bounded repository navigation and reviewed decisions.
- Manager: state, evidence, budgets, blockers and optional insights.
- Worker: exact bounded objective, permitted files, approved constraints and *necessary* prior lessons only; no inherited Worker conversation and no privileged test oracle.
- Tester: original acceptance, exact candidate, independent oracle and permitted test interfaces.
- Reviewer: original plan, exact candidate, exact Tester report and deterministic rerun command; no implementation authority.

Any summary must cite source references and be reversible to full evidence when uncertainty matters. Codebase Memory indexing helps repository navigation; it is not a reliable meeting transcript or authorization record. Memory write is a reviewed post-run action, not a Worker privilege.

### E. Evidence and telemetry interface

For each observed model call/role, record where available: source (`host|gateway|estimate|unknown`), reported/configured/effective model IDs separately, provider protocol, token scope, input/output/cache counters, wall duration, completed/failed state, retries, quota/cost *only if trustworthy*, redaction outcome and evidence_ref. **Null** is the correct value for unobserved metrics; never treat missing quota or cache as zero or sum cumulative snapshots twice.

Store operational metadata separately from any sensitive transcripts. Raw prompts, reasoning, credentials, API tokens and code snippets should not be placed in shared public logs. A read-only dashboard may project these records but must distinguish `reported` from `verified` and must not enable implicit approvals.

### F. Diagnostic and control surfaces

Propose one optional `council doctor` equivalent only after tests: source integrity, role sequence completeness, native host capability, stale attempt, missing candidate/Tester rerun, package consistency, budget telemetry provenance, permission boundary and schema compatibility. Result category `PASS / FAIL / BLOCKED / SKIP / UNVERIFIED` with stable IDs and documented exit codes. A `SKIP` is never counted as proof of passing a mandatory control. Any read-only dashboard stays separable from skill install.

### G. Independent multi-model council room (later, separate feature)

Optional contribution page receives externally generated, explicitly attributed opinions with source/model **claimed** labels, immutable submission IDs, question/version IDs and challenge links. Other models submit opinions; they gain no repository or command access. Manager/Planner compare disagreements, Owner makes consequential decisions. Do not build a universal MCP gateway or force subscription bridging. The page is a discussion inbox, not an agent-control plane.

## Contract evolution

Existing `message-contract.json` remains authoritative. Any journal/model/graph proposal must begin as **a separate optional, versioned schema** and adapter; preserve original message bytes/hashes and backward compatibility. Each new envelope field needs a clear source of truth, strict validator, unknown/unsupported version behavior, golden fixtures, fuzz/negative cases and a reversible migration story. Do not quietly extend the frozen protocol or rewrite existing reports.

**Success definition:** a user invokes the skill in a supported host; separately observed real roles produce verifiable artifacts; known failures cause controlled rework or explicit blocking; original criteria remain immutable; Owner receives an evidence-based result. Runtime/telemetry conveniences are worthwhile only insofar as they improve that result.
