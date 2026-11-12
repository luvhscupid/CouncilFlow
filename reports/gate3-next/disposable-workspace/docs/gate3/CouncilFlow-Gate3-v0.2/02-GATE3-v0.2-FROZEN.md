# CouncilFlow Gate 3 — v0.2 (frozen experiment specification)

**Ratification basis:** Council Round 4 draft, GPT exact modifications, Claude Round 5 incorporation, GPT Round 5 confirmations and wording corrections.  
**Evidence state:** READ (specification only). RAN (none). CLAIMED (prior Codex demonstration reports do not constitute this experiment).

## Purpose
Determine whether Codex **natively activates** `$council-flow`, runs distinct role agents with observable evidence, and removes Owner courier work.

This is an observation experiment. It may modify the demo application and its tests in a disposable workspace. It must **not** modify CouncilFlow's skill, role configuration, or policy.

## Setup
- Use an authenticated **local Codex CLI or app** and a trusted project. Record the actual Codex version. Start from the shipped CouncilFlow commit in a disposable worktree or isolated copy. A Cloud run qualifies only with equivalent native activation and host evidence.
- Save the Owner's exact two or three acceptance criteria verbatim to an experiment fixture **outside the installed skill** before invocation. Keep the fixture unchanged for E10 comparison.
- Send **one initial instruction** consisting of `$council-flow` followed by the Owner's frozen task text. **Do not** paste `SKILL.md`. **Do not** explicitly request subagent spawning, and do not issue a subsequent command to force delegation during this experiment.
- After submission the Owner performs **no courier work**. Genuine host permission approvals or explicit decisions requested by the Planner or Manager are allowed and must be logged separately as AUTHORIZATION, not courier interventions.
- The test may change only the designated demo application/tests within the disposable workspace. No skill/config/policy changes, ACL changes, permission bypasses, or other project modifications.

## Evidence classes and rules
- For E1–E6, only **HOST-OBSERVED** evidence (Codex UI, authentic thread/session records, tool executions or logs) can establish PASS. Model self-report is **AGENT-REPORTED**, not sufficient.
- For E7–E10, applicable evidence sources may be **OWNER-LOG**, **SAVED-ARTIFACT**, **DIFF**, and **RECORDED-EXECUTION**. E8 requires recorded executions, not just a Reviewer's claim; E10 requires an actual comparison to the frozen fixture.
- Label each result with its evidence source. If evidence is unavailable, use **UNVERIFIED**, not PASS or assumed FAIL. No visibility is not proof of no activity.
- Every non-PASS result must have exactly one primary class: `AUTH`, `HOST_CAPABILITY_MISSING`, `WORKFLOW_BEHAVIOR`, or `EVIDENCE_INSUFFICIENT`.

## Checks

### E1 — Native discovery and invocation
Record separately (a) listing/picker visibility and (b) direct `$council-flow` selection. **PASS requires host-observed successful native invocation.** Missing picker entry alone does not invalidate working direct invocation.

### E2 — Native delegation trigger
**PASS requires host-observed delegation attributable to the activated skill** without an additional explicit spawning instruction. If invocation succeeds but host evidence positively shows non-delegation, **FAIL (WORKFLOW_BEHAVIOR)**. If causation is not observable, **UNVERIFIED**. Alternative invocation wording requires a subsequent Owner decision, not an instruction added during this experiment.

### E3 — Actual spawns
Record host-observed subagent count, role/agent_type, and thread labels/IDs, without inventing identifiers. The required distinct-role observation is assessed together with E6.

### E4 — Role configuration applied
Check whether intended `council-*` custom-agent TOML settings are actually effective using host-exposed turn/thread settings. **PASS** needs affirmative evidence. **FAIL** needs evidence of a mismatch/non-application. Invisible effective settings = **UNVERIFIED**, not a claim that roles were prompt-only.

### E5 — Independent Tester command
Host evidence shows the Tester executed its commands **in its own Tester thread**, not merely a Worker report copied to Tester.

### E6 — Distinct role threads
Host evidence shows Worker, Tester and Reviewer as **three distinct threads**. A single model adopting three role names is insufficient.

### E7 — Zero Owner courier work
Count courier interventions after initial submission. **PASS requires exactly zero.** Courier work includes the Owner moving any message/output/file content from one agent to another, retyping instructions already available to agents, or being asked to carry data that another agent could hand over. Legitimate host permission prompts and explicit Planner/Manager Owner decisions are logged separately as **AUTHORIZATION**, not courier work. Evidence: OWNER-LOG and available interaction records.

### E8 — Reviewer verification rerun
The Tester identifies which of its commands are deterministic. Reviewer independently re-executes **one** deterministic Tester command and compares its **exit code** and **SHA-256 of normalized stdout** to the Tester-recorded result. Normalization must be documented, identical on both sides, and must not erase meaningful differences. Evidence must contain recorded commands, exit codes, normalized output hashes and the rerun comparison. No comparable deterministic command = `NOT_COMPARABLE` and E8 does **not** PASS.

### E9 — Plain-English Owner interface
Routine **agent-generated** Owner-directed communication comes only from Planner or Manager and uses plain English. Owner is not required to read, interpret, copy or relay raw inter-agent messages. Optional inspection of agent records does not violate E9. Host-generated permission dialogs and genuine explicit Owner decisions are separately permitted/logged.

### E10 — Frozen criteria fidelity
Planner reproduces the Owner's saved mandatory acceptance criteria **verbatim**. PASS requires a direct **DIFF** or equivalent byte-for-byte/line-preserving comparison against the saved fixture. Separately identifiable metadata such as IDs and traceability references may be added; criteria may not be paraphrased, omitted, weakened, or silently augmented.

## Token-usage data (not a gate)
Record the host's actual exposed token usage and its scope (single agent, parent session, or whole experiment). If not exposed, record `UNAVAILABLE`. **No efficiency pass/fail** until a controlled single-agent baseline has been defined.

## Per-check results
Use exactly `PASS`, `FAIL`, `BLOCKED`, or `UNVERIFIED` for each E1–E10. Every non-PASS carries exactly one primary class:
- `AUTH`
- `HOST_CAPABILITY_MISSING`
- `WORKFLOW_BEHAVIOR`
- `EVIDENCE_INSUFFICIENT`

When the underlying observation is `NOT_COMPARABLE` for E8, record E8 as `UNVERIFIED (EVIDENCE_INSUFFICIENT)` unless there is positive evidence of a workflow defect; retain `NOT_COMPARABLE` as the reason, never PASS.

## Run-level outcomes
- **All E1–E10 PASS** → `NATIVE_ROLE_WORKFLOW_OBSERVED`. Only then consider the separately authorized planted-bug evaluation.
- **No FAIL or BLOCKED, at least one UNVERIFIED** → `NATIVE_ROLE_WORKFLOW_PARTIAL`. List all unverified checks. Do not claim full verification.
- **E1 PASS and E2 FAIL** → Skill activates but does not autonomously delegate. Record `WORKFLOW_BEHAVIOR`. Owner decides separately whether to (a) accept different invocation wording, (b) authorize a skill correction, or (c) stop. Not automatically a final product-quality verdict.
- **E4 FAIL** → Report the demonstrated role-configuration mismatch. Owner separately decides whether prompt-defined roles are acceptable. E4 does not retroactively PASS.
- **E4 UNVERIFIED** → No conclusion whether native custom-agent settings applied.
- **E1 FAIL** → Dependent checks BLOCKED; return observations to Owner. A discovery or invocation fix requires separate Owner authorization.
- **Authentication or permission failure** → `BLOCKED (AUTH)`, not a product-quality verdict.
- **Any other mandatory FAIL** → Report the failed check and its class. Do not declare full workflow observed.
- **Any remaining BLOCKED** → Report run as blocked, not partial or fully observed.

## Stop rule
After the authorized attempt, **if E3 does not establish that distinct subagents spawned, stop**. Classify E3 `FAIL` only when the host positively shows the required spawning did not occur; `UNVERIFIED` when host observability is insufficient. Return evidence and classification to Owner before any implementation changes. This rule does not authorize abandoning, deleting, or rebuilding CouncilFlow.

## Explicit exclusions
No build prompt; no new skill features; no design changes; no JSON-boundary-list work; no global settings changes; no ACL escalation; no edits to earlier ACP or Execution Kernel projects; no paid provider APIs; no fabricated host events; no UX-scoring replacement role; no automatically executing follow-up corrections or planted-bug test.
