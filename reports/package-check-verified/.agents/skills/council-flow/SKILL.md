---
name: council-flow
description: "Coordinate an ordinary coding goal through a Planner, parent Manager, fresh Worker, independent Tester, and independent Reviewer using native Codex subagents. Invoke explicitly with $council-flow for implementation, repair, or refactoring that needs this five-role workflow. Do not use for general questions or pretend unavailable delegation works."
---

# CouncilFlow

Invoke explicitly with $council-flow followed by an ordinary coding goal.
Use native Codex tools, inherited provider/model configuration, actual workspace
permissions and budget. This is an instruction skill, not a security sandbox.
It needs no new key, subscription, database, service or custom supervisor.
Only parent **Manager** gives ordinary progress/results to the Owner.

## Required communication

Read [communication](references/communication.md), [roles](references/roles.md)
and the versioned [YAML policy](policies/roles.yaml).
Agent task assignments, plans, reports and decisions **MUST be UTF-8 JSON**
under council-flow 1.0. Markdown/prose cannot replace those controlled packets.
Keep large evidence in immutable files referenced by identity/path/SHA-256.
YAML is role/workflow policy; native custom-agent configuration remains TOML.
JSONL diagnostics are optional. Owner-facing communication stays concise natural
language; do not expose internal envelopes or long logs by default.

## Execute the goal

1. **Establish scope.** Inspect repository instructions/status and real native
   capabilities. Define the Owner objective, approved paths and observable
   acceptance. Never invent tool names, models, permissions or session IDs.
2. **Planner.** Dedicated native Planner publishes plan.publish JSON before
   implementation. Preserve original plan and mandatory acceptance. External
   mode preserves an Owner-approved supplied plan and provenance unchanged;
   never claim to contact the external ChatGPT conversation.
3. **Manager.** Parent accepts plan and delegates job.assign JSON to a fresh
   Worker. Validate controlled packets before dispatch and results on receipt
   using the installed contracts.py helper, known actor bindings, candidate
   hashes and available ordered context. Native transport itself is not enforced
   by this helper. Pass role instructions to native subagents when custom-role
   selection is unavailable, and disclose that fallback.
4. **Worker.** Implement only bounded work, perform developer checks, return
   job.report JSON with actual candidate/evidence and changed files, then stop
   edits. Worker cannot approve itself. Manager writes no application code.
   One Worker mutates a workspace; parallel implementation requires authorized
   isolated workspaces.
5. **Tester.** Fresh separate native Tester independently executes original
   acceptance and the approved verification strategy on the exact candidate.
   For each suitable deterministic command, record command/arguments, working
   directory, candidate and relevant input identities/hashes, exit code, SHA-256
   of stdout after CRLF-to-LF replacement only, criterion ID and evidence artifact.
   A declaration alone does not prove determinism. Do not repair product or approve
   the oracle.
6. **Reviewer.** Compare the frozen plan and criteria, Worker candidate and
   Tester's recorded technical evidence. Independently rerun one Tester-declared
   deterministic command; capture raw stdout/exit, apply CRLF-to-LF-only
   normalization and SHA-256, and report both results and evidence to Manager.
   Matching proves repeatability only for that command and recorded conditions.
   Mismatches preserve both results and fail review; no command is
   NOT_COMPARABLE and cannot pass E8. Do not implement, alter criteria, or perform
   generalized UX evaluation.
7. **Rework.** Manager records task.decision JSON from evidence: accept, reject,
   rework or escalate. Failed mandatory checks cannot be accepted. Repairs use
   a fresh Worker/attempt under unchanged criteria, then affected independent
   checks. Follow [recovery](references/recovery.md); no lifetime engineering
   repair cap. Infrastructure retry 3/crash recovery 2 are instruction-only
   policy, not runtime accounting.
8. **Final Planner check.** Manager sends verified plan.progress JSON. Planner
   returns plan.check against original acceptance and evidence, not a rewritten
   Worker checklist. Manager gives the Owner concise natural-language results
   using [acceptance](references/acceptance.md).

## Evidence and limits

Follow [workflow](references/workflow.md). Keep real task/plan/attempt/message IDs,
validated causal order, causal references, commands/exits and evidence hashes.
Agent-authored envelopes omit `created_at`; diagnostic timestamp syntax does not
prove trusted clock provenance. Structural
validation is not sender authentication, native-transport control or OS isolation.
Without supplied context, only structure is checked; disclose missing context.
No JSON/YAML declaration grants filesystem, network, execution or approval power.

Ordinary in-scope repair needs no repeated Owner approval. Consequential new
scope/authorization and required subjective decisions belong to the Owner.
Use approval.request only for a concrete necessary decision; record
approval.decision only from actual Owner input/provenance, never AI invention.
Refuse unauthorized external changes without attempting permission bypass.

If native discovery, invocation, a role, test or actual interaction is unavailable,
record UNVERIFIED/BLOCKED. Never simulate agents or upgrade static checks into
live proof. Preserve useful work and report the exact gap. Contract restoration
with blocked activation is CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED;
COUNCILFLOW_FULLY_VERIFIED requires genuine invocation and real required roles.
