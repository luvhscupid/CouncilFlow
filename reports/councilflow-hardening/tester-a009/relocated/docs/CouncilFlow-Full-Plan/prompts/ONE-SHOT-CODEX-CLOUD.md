# COUNCILFLOW — ONE-RUN COMPLETION MISSION
## Existing Codex Cloud repo · Preserve real skill · Restore approved communication · Verify actual operation

**OWNER AUTHORIZATION.** You are operating on the existing connected `CouncilFlow` repository, previously reported at `/workspace/CouncilFlow`, baseline commit `d30e906`. This is a single end-to-end engineering assignment. Implement all authorized in-repository work, run tests, repair defects, package and commit; do not stop at planning or request repeated routine approvals.

If this instruction is accompanied by `CouncilFlow-Full-Plan.zip`, read `README.md`, `00-SCOPE-AND-STATUS.md`, `01-PRODUCT-AND-ROLES.md`, `02-PROTOCOL-AND-POLICY.md`, `03-DELIVERY-AND-ACCEPTANCE.md`, `04-SECURITY-AND-LIMITS.md`, `05-OPERATIONS-AND-HANDOFF.md`, and `SOURCE-MANIFEST.md` first. These are supporting references. The current repository and observed host capabilities take precedence on factual implementation details. This prompt is self-contained if those files are inaccessible.

## 1 — Immutable purpose

**Build/finish a usable repository-scoped Codex agent skill named `council-flow`, not a standalone platform.** Its real deliverable is a functional `$council-flow` invocation that coordinates distinct native AI-role sessions to complete an authorized coding task, independently test it, review usability, rework defects, and report truthful evidence to the Owner.

Do not write a new Python/SQLite Supervisor, external AI API client, message broker, web dashboard or another architecture design. Do not import or modify old ACP, Execution Kernel or Codex on Crack projects. Existing CouncilFlow skill code, demo, tests and packaging must be preserved where correct.

Reported baseline: installable skill discovered, receipt demo (Rp103,000) and multiple manual role sessions, but explicit skill invocation NOT verified due to Codex CLI authentication token-refresh error. The earlier communication format was underspecified. Do not assume either issue has since been resolved until you inspect.

## 2 — Authorization and hard boundaries

Owner authorizes reading/modifying files, tests, demo code, skill metadata/references, local validators, YAML policy, Codex role TOML, reports and release ZIP, and committing inside current CouncilFlow repo. No approval needed for in-scope corrective work. No modification outside repo; no global Codex settings, ACL, `icacls`, UAC, takeown, sandbox bypass, credential/token extraction, paid APIs, dependency installation, external publication, deployments, or unapproved filesystem/network capability. No auth circumvention; if direct activation blocked, report it, while finishing independent local work.

Follow native Codex official skill and agent formats actually supported in this environment; do not invent tool names or TOML keys. Existing `SKILL.md` is primary deliverable. User should not need to manually coordinate the agents. Skill markdown alone does not enforce OS permissions. Do not promise isolation, authentication or exact-once execution unsupported by host.

## 3 — Five-role contract, nonnegotiable

Owner: goal/constraints, consequential approvals, required subjective acceptance, receives concise summaries. Never treat the user as debugging worker.

Planner: persistent logical planning context or distinct native Planner session; authors original acceptance criteria, task IDs, scope and final objective check. Does not implement code, delegate or alter permissions. May accept externally approved plan from ChatGPT as input; do not pretend to communicate with it.

Manager: parent Codex coordinator. Selects available permitted models/skills, delegates, tracks evidence, decides rework, escalation, acceptance proposal; **does not implement product code**. Can order ordinary engineering repairs without new Owner approval within fixed objective, authorization/security constraints and available resources. No arbitrary number of retries; avoid repeated unproductive failures.

Worker: fresh native coding subagent each independent attempt. Only mutating application-code role. Receives scoped objective and approved criteria; returns changed files, tests and limitations; cannot approve own output or change requirements.

Tester: fresh independent technical subagent, no code repair. Checks implemented behavior with executed commands and evidence against original criteria. Worker self-tests are insufficient. Cannot rewrite oracle to get a pass.

Reviewer: fresh independent user-experience subagent, no code repair or replacing technical Tester. Evaluates actual interaction where possible, friction, usability, missing requirements; distinguish real interaction, inspection, simulated view. Ratings only advisory.

Flow: Owner → Planner → Manager → fresh Worker → independent Tester → independent Reviewer → Manager (rework loop if needed) → Planner final checklist → Owner. Preserve one writer per workspace; parallel edits only with truly isolated workspaces and serial integration. Do not count a single agent pretending to be all roles as multi-agent execution.

## 4 — Required communication contract

At CouncilFlow-controlled task/report boundaries, use strict **UTF-8 JSON** records. Versioned, per-message-type and role-specific. **YAML** is human-readable Council role/workflow policy. **TOML** remains native Codex agent configuration where the host requires it; do not substitute YAML for Codex TOML. **JSONL** optional diagnostic event export, not a trusted transactional store. **Natural language** concise for the Owner; file/evidence references for large logs. Keep raw internal diagnostic JSON out of normal user chat.

Minimal CouncilFlow SKILL-level envelope (illustrative, not claim of byte-for-byte ACP v0.2.1 compatibility):

```json
{
 "protocol":"council-flow","version":"1.0","message_id":"M0001",
 "message_type":"job.assign","plan_id":"P0001","plan_revision":1,
 "task_id":"T0001","attempt_id":"A0001",
 "sender":{"role":"manager","instance_id":"manager-main"},
 "recipient":{"role":"worker","instance_id":"worker-001"},
 "in_reply_to":null,
 "payload":{"objective":"Implement approved task","scope":["demo/"],"acceptance_ids":["AC1"],"instructions":["Implement the approved task within demo/."]},
 "evidence_refs":[]
}
```

Message types: `plan.publish`, `job.assign`, `job.report`, `task.decision`, `plan.progress`, `plan.check`, `approval.request`, `approval.decision`. Validate legal sender/recipient/type combinations; schema-version and required/extraneous fields; duplicate keys; nonstandard constants; strict JSON numeric types (bool not int); UTF-8; bounding size/depth/IDs; linked plan/task/attempt, causal references where context available; role-specific payloads/evidence. Do NOT claim JSON is authentication, Codex's internal native transport is under skill control, or structurally valid messages imply permissions. Protect plan revision and candidate-specific evidence in all skill-owned records.

YAML must express role permissions/restrictions, resource/rework policy, approval requirements, evidence provenance, session freshness, one-writer rule. Do not grant capabilities via YAML. No unapproved YAML parser dependency; use existing trusted parser or a clearly limited subset. Keep TOML native/valid. Optional JSONL includes bounded redacted event metadata, no credentials or hidden reasoning.

## 5 — Inspect before changing

Inspect current working tree, latest commit, actual `.agents/skills/council-flow/SKILL.md`, reference files, `.codex/agents/*.toml`, tests, demo, package, `reports/final.md`. Run existing suite as baseline. If communication contract already implemented, verify instead of duplicating. Keep changes minimal. Never overwrite manual changes without inspection.

## 6 — Implementation sequence (one authorized execution)

PHASE A Product integrity: ensure skill metadata is discoverable, top-level `SKILL.md` concise, reference files loadable, native Codex custom agent config valid; no global edits. Preserve existing app and tests.

PHASE B Contract: implement/version JSON schema/validator examples for all roles, YAML policy, optional JSONL; integrate instructions in SKILL.md and role reference files so the contract guides real delegation and reporting, not just documentation. Do not add a separate orchestration server.

PHASE C Verification: add tests that detect malformed JSON, duplicate keys, NaN/Infinity, illegal role/message pair, impersonated Owner decision, stale/misbound evidence, missing acceptance IDs, changed plan revision, failed mandatory tests and rework, correct YAML/TOML rules and natural-language owner output. Run full previous tests; existing receipt example must still produce **Rp103,000**. Include independent negative controls against validators.

PHASE D Activation and real benchmark: in an authenticated supported Codex context, actually attempt `$council-flow` activation using the native invocation mechanism. Do not simply read SKILL.md and claim activation. Run a NEW offline coding demonstration (e.g. CSV summarizer with malformed input cases and tests) via real Planner, Manager, Worker, Tester, Reviewer and final Planner check. Distinct roles require actual host evidence (sessions/dispatches, if exposed). Worker writes code; Tester actually runs tests independently; Reviewer independently assesses user experience; Manager reworks mandatory failures with fresh Worker. Record tests, candidate files and evidence. Manual role delegation can be separately documented but DOES NOT satisfy native skill activation.

PHASE E Release: update requirement-to-file/evidence traceability; report actual passed/failed/unverified; package latest skill in `dist/council-flow.zip` and inspect contents for missing files/secrets; commit authorized edits; report path, commit and working tree. Do not claim product has been installed globally or on local PC.

## 7 — Acceptance gates, no shortcuts

- Skill physically present in proper repository path with correct metadata.
- All prior functionality and tests retained, demo runs.
- JSON/YAML/TOML/JSONL separation accurately represented and applied in skill-owned handoffs.
- Five role-specific messages and responsibilities checked; strict invalid-input tests detect real bugs.
- Native Codex discovery observed.
- **Explicit native `$council-flow` invocation actually observed** (not manual instruction replay).
- Real distinct role instances actually observed doing tasks, or honestly `UNVERIFIED`.
- Fresh Worker implements real demo program; separate Tester runs behavior checks; Reviewer reports observations/limits; Manager records correction; Planner checks original stable acceptance IDs.
- User-facing result concise and evidence-grounded; no automatic approvals/fake evidence.
- No changes outside authorized repo, no ACL/password/sandbox bypass, no paid backend.
- ZIP fresh and verified, repository commit produced.

Never mark unsupported or unobserved criteria PASS. If real invocation cannot be demonstrated due to auth/host features, keep its status UNVERIFIED while completing local contract changes.

## 8 — Security and historical source distinctions

Recovered Council 001 v1.0 architecture demands trusted-controller / Worker / verifier separation; **a Codex skill cannot provide the same enforcement**. The original approved Security Annex v1.0-A exact text is missing. The ACP-SPEC v0.1 source is explicitly PROPOSED, not automatically exact frozen ACP v0.2.1. Do not claim formal Annex compliance, reliable authentications, tamper-proof append-only ledgers, process sandbox isolation or autonomous coding safety based only on markdown, JSON and YAML.

Preserve Owner O1 normal Manager rework autonomy, O3 subjective owner sign-off, O4 criteria/scope frozen, O5 isolated parallelism, O8 separate technical/UX signals, approved-skill pinning where host supports it, budgets/authorization bounds. Reuse original source details where accessible but do not import the old project.

## 9 — Report classification and exact finish

Begin final with exactly one:

- `COUNCILFLOW_FULLY_VERIFIED` — ONLY if real native skill invocation and distinct-agent live workflow AND independent actual tests succeed.
- `CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED` — local skill/protocol/integration tests pass but native invocation cannot be observed.
- `PARTIAL — <precise blocker>` — other requirements missing.
- `FAILED — <precise failure>` — cannot deliver working local artifacts.

Include: actual modified files, test commands/counts/failures, receipt regression output, real native role count vs manual, invocation result and exact error if blocked, security limitations, final release ZIP and commit, and one short installation/use command. Save detailed logs under reports, not chat. Do not invent models, costs, sessions, tokens, benchmarks or permissions.

**EXECUTE** inspect → correct → integrate → test → demonstrate → package → commit → report. One run, no approval spam. Preserve working CouncilFlow; no redesign; no unrelated projects; no fake completion.
