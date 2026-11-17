# 06 — Proposed execution backlog, dependency map and acceptance

**Status:** READY_FOR_OWNER_REVIEW, **NOT AUTHORIZED TO EXECUTE**. Tickets are work definitions, not a request for an agent to start coding. This backlog is intended for later one-shot Codex/Claude tasks only after Owner chooses a slice and freezes acceptance.

## Work item format

Each future issue/PR should record: `work_id, phase, scope, allowed paths, forbidden paths, prerequisites, baseline_sha, original_owner_source_ref, acceptance_ids, required native host, external/network permissions, model/spend policy, artifacts, independent verification, rollback, Owner decision`. Work may be split further by the Manager while retaining exact approval and criteria. Any hard authorization or scope change returns to Owner.

## Phase 0: baseline (read-only)

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-R00 | Reconcile latest GitHub main, branch/PR and release state | Exact current SHA, branch differences, overlaps, status; no edits |
| CF-R01 | Map existing Agent Efficiency, model-selector research, skill routing, journaling, dashboard | Per-feature `exists/partial/missing/conflict` table with source paths |
| CF-R02 | Freeze non-secret baseline evidence and current native limitations | Current Codex and Claude smoke status with evidence and UNKNOWN fields |
| CF-R03 | License/source audit for conceptual reuse | Traceable pinned links, no unreviewed source copy |

**Exit gate:** independent reviewers can recreate the baseline inventory from commit SHA and cited artifacts.

## Phase 1: existing Agent Efficiency

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-E10 | Re-run existing fixture/contract tests in isolated checkout | Exact commands, result count and failure evidence; no regression of source fidelity |
| CF-E11 | Verify installed opt-in paths and digest/expand negative controls | Byte-preserved expansion, timeout/incomplete flag, hash mismatch detection |
| CF-E12 | Qualify one host adapter with actual permitted event shape | No credential access, model route provenance labeled, unsupported event fails clearly |
| CF-E13 | Prepare frozen A/B manifest by adapting *existing Package D draft* | Same task/oracles/route/retries; Owner signature and spending gate required before execution |
| CF-E14 | Run authorized pilot only if CF-E13 explicitly approved | All arms preserved, failures included, independent outcomes, no invented quota |
| CF-E15 | Submit keep/revise/reject decision | Outcome/quality and evidence utility versus resource use, with limitations |

**Do not** change default route, activate hooks, auto-enable efficiency or implement a new recorder. Latest draft [Package D](../../experiments/agent-efficiency/evaluation/PROTOCOL.md) is authoritative for its own proposed experiment only after separate approval.

## Phase 2: host model routing

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-M20 | Version role preference + capability/provenance schema | Logical name, configured/reported/effective separate; missing fields null |
| CF-M21 | Probe documented native host capabilities read-only | Capability result matches host evidence; no secret/config mutation |
| CF-M22 | Build disabled-by-default selection adapter | Unsupported role override labels inherited or blocks; existing behavior unchanged |
| CF-M23 | Test identity, route and fallback edge cases | Wrong API protocol, model unavailable, stale fallback, no per-role capability |
| CF-M24 | Benchmark cheaper Worker/Tester candidate on safe tasks | Accepted outcome and full workflow budget versus same-route baseline |
| CF-M25 | Independent promotion review | Owner sees supported role matrix; no hardcoded "cheap model always sufficient" |

**Exit gate:** zero unsupported claims of per-role autonomy; evidenced model and route identity or explicit UNKNOWN.

## Phase 3: durable recovery

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-J30 | Formalize run/attempt/transition schema proposal | Original source refs unchanged; versioned events and state transitions |
| CF-J31 | Implement separate opt-in transactional store prototype | Atomic transition and replay tests in disposable workspace |
| CF-J32 | Build recovery reconciler | Detect stale agent, missing candidate, mismatched original hash, schema error |
| CF-J33 | Crash and concurrency fault-injection suite | Invalid replay/duplicate/stale promotion never becomes accepted |
| CF-J34 | Handoff across interrupted native sessions, if permitted | Observed result with fresh host evidence; no model "I remember" substitution |
| CF-J35 | Review portability/security and choose backend | Explicit Windows/Linux behavior and rollback path |

**Exit gate:** no missing/replayed evidence accepted; no silent permission, scope or Owner decision changes.

## Phase 4: dependency and isolated concurrency

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-G40 | Minimal DAG with stable prerequisites/criteria | Reject cycles, missing dependencies, stale plan revision |
| CF-G41 | Disposable separate workspaces and scope manifest | Real host/OS isolation evidence; not advisory locks as proof |
| CF-G42 | Serialized promotion on trusted current base | Conflicts and stale bases fail; no auto-merge |
| CF-G43 | Integration retest after candidate combination | Original criteria independently verified against combined hash |
| CF-G44 | Parallel-versus-serial benefit study | Net quality and wall time include conflict/rework costs |

**Exit gate:** non-mutation of sibling workspace and no false PASS under simultaneous edit controls. Otherwise retain serial Worker mode.

## Phase 5: memory and observability

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-O50 | Reviewed experience entry schema with provenance | Success/failure/insight tags, evidence, project scope, supersession |
| CF-O51 | Adversarial retrieval tests | Stale/poisoned lessons do not gain authority or enter Worker context by default |
| CF-O52 | Deterministic doctor diagnostic catalogue | Missing role, evidence, schema, executable or native host -> explicit blocking status |
| CF-O53 | Read-only projection into existing dashboard if available | No duplicate runtime, UI reflects journal and clearly labels unverified |
| CF-O54 | Privacy/retention gate | Public traces free of prompts/credentials/secrets; safe metadata only |

**Exit gate:** fewer manual investigations with no new misleading confidence, credential exposure or loss of evidence.

## Phase 6: candidate workflow optimizer

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-X60 | Freeze benchmark corpus and independent oracles | Task hashes, controlled strata, negative cases, bounded budget |
| CF-X61 | Define candidate configuration and approved search limits | No candidate changes frozen criteria, role independence or security |
| CF-X62 | Evaluate one change at a time against unchanged baseline | Paired outcomes including failed attempts and unknown metering |
| CF-X63 | Independent replay / Reviewer comparison | Reproducible accept/reject and no self-validation |
| CF-X64 | Owner promotion decision via PR | No self-merge, no spontaneous scheduled changes or spending |

**Exit gate:** objective improvement under hard constraints, or `INCONCLUSIVE/NO_GO` and no production changes.

## Phase 7: optional independent-opinion board

| ID | Work item | Acceptance |
| --- | --- | --- |
| CF-C70 | Threat model and input/output data contract | Claims separated from verified model identity, no trusted instructions |
| CF-C71 | Minimal local/submission-only prototype | No repo access, process execution, model gateway or implicit plan publication |
| CF-C72 | Challenge and attribution tests | Same issue/plan IDs, append-only references, forged/stale content visibly rejected |
| CF-C73 | Owner-controlled final plan import | Exactly approved source gets source-fidelity provenance; no AI self-authorization |

**Exit gate:** outside submissions can inform decisions without crossing CouncilFlow's Owner/Manager execution boundary.

## Non-regression matrix

Every proposed implementation PR should attach a test matrix covering the impacted invariants. The following are **non-negotiable regression obligations** for all phases that touch them:

| Invariant | Observed check |
| --- | --- |
| Original frozen criteria | Byte/hash fidelity, exact ordered acceptance IDs, no derived-plan substitution |
| Role sequence | Real native agent identity/session evidence; separate Worker/Tester/Reviewer |
| Independent technical acceptance | Actual bounded commands, output evidence and negative controls |
| Reviewer comparison | Exact Tester message, candidate hash, independent command exit/stdout hash |
| Manager + Planner | Correct scoped rework, final criterion mapping, no code writes by Planner/Manager |
| Approval boundary | Explicit Owner input for higher-risk changes, no fabricated signature |
| Artifacts | SHA-256, path traversal/symlink limitations, no stale/corrupt references promoted |
| Runtime resource cap | Stop unauthorised/unknown paid calls; no retries on identical failures with no new evidence |
| Packaging | Codex/Claude share canonical scripts/references and keep executable install paths |
| Security | No global configs, ACLs, hidden tests, secrets, provider changes or unapproved external writes |
| Observability | `UNVERIFIED` is not painted green; missing metrics not zero |
| Portability | Tested Windows path semantics and host-specific native behavior |

## Proposed phase completion packet

```text
Work ID + Owner authorization provenance
HEAD / base revision / candidate SHA-256
Approved frozen plan and acceptance IDs
Allowed files and changed-file manifest
Commands, exact exits and raw evidence refs
Native role/session attribution, or UNVERIFIED
Independent Tester result and negative controls
Independent Reviewer comparison/rerun
Manager decision -> Planner final check
Route/usage observation + UNKNOWN fields
Open limits, rollback action, recommended Owner decision
```

An agent's `COMPLETE` statement does not substitute for this packet. This format is a proposed checklist and must be reconciled against the actual v1.0 message contract before implementation.

## Suggested first separately authorized task

A safe first approval would be **CF-R00 through CF-R03 as read-only work**, producing a source-cited baseline/gap inventory *without* running any models or changing production. Then Owner can decide whether to authorize the already drafted CF-E13/CF-E14 Agent Efficiency evaluation. Do not interpret this suggestion as approval.

**Plan publication ≠ production integration.**
