---
name: run
description: "Coordinate an ordinary coding goal through a Planner, parent Manager (this session), fresh Worker, independent Tester and independent Reviewer using native Claude Code subagents. Invoke explicitly with /councilflow:run <coding goal> for implementation, repair or refactoring that needs this five-role workflow. Do not use for general questions or pretend unavailable delegation works."
argument-hint: "<coding goal>"
disable-model-invocation: true
---

# CouncilFlow (Claude Code host package)

Invoke as `/councilflow:run <coding goal>`. The goal is: **$ARGUMENTS**
(if empty, ask the Owner for the coding goal and stop).

This is an instruction skill using Claude Code's inherited model, permissions
and budget. It is not a security sandbox, a service, or a new provider route.

## Host mapping (Claude Code)

`CF` = `${CLAUDE_SKILL_DIR}`, the directory of this skill (`skills/run`, not the
plugin root). It is a read-only install cache: execute from it, never write there.
Read `CF/host-claude.md` first: it maps the shared references' Codex wording
(`$council-flow`, `.agents/skills/council-flow/`, `.codex/agents/*.toml`,
`inherit_native_codex`) to this host and wins over shared text on host
mechanics. Shared contract rules are never overridden.

Contract helper: `python "${CLAUDE_SKILL_DIR}/scripts/contracts.py"`.
Efficiency helper (opt-in only): `python "${CLAUDE_SKILL_DIR}/scripts/efficiency.py"`.
Run helpers from the target repository (Python 3.11+, standard library only).
Run artifacts (plans, packets, evidence) go in the target repository under
`.councilflow/runs/<task-id>/` — never inside the plugin directory. Suggest the
Owner keep that directory out of version control.

## Delegation model (verified constraint)

Claude Code subagents cannot spawn other subagents. Therefore **this main
session is the Manager** and delegates directly, using the Agent tool with
`subagent_type`:

`councilflow:council-planner`, `councilflow:council-worker`,
`councilflow:council-tester`, `councilflow:council-reviewer`.

Each call is a fresh, separate context. Pass each agent everything it needs in
the prompt: task/plan/attempt IDs, absolute `CF` path, paths of the JSON packets
and evidence files, the frozen criteria, and the exact candidate. Agents return
their JSON report path plus a short summary. If a named agent is unavailable,
pass the same role instructions (from `CF/references/roles.md` and the agent
file) to a `general-purpose` subagent and disclose the fallback. If no subagent
can be launched, record BLOCKED/UNVERIFIED; never role-play agents yourself.
The Manager never writes application code. Only one Worker mutates a workspace
at a time; parallel Workers require separate git worktrees the Owner authorized.
Only the Manager reports progress to the Owner, in concise natural language.

## Required reading, then execute

Read `CF/host-claude.md`, `CF/references/planner.md`, `CF/references/communication.md`, `roles.md`, `workflow.md`,
`source-fidelity.md`, `acceptance.md`, `recovery.md`, and `CF/policies/roles.yaml`.
All plans, assignments, reports and decisions MUST be UTF-8 JSON under
council-flow 1.0 and validated with `contracts.py` at controlled boundaries.
Codebase Memory: follow `CF/references/codebase-memory.md` (zero MCP calls for
empty/install-only projects; direct inspection when the MCP is unavailable).

1. **Establish scope.** Inspect repository instructions/status and real
   capabilities. Define objective, approved paths, observable acceptance. Bind
   the Owner's goal text verbatim as the original source
   (`contracts.py capture`, see source-fidelity.md). Never invent IDs.
2. **Planner** (`council-planner`): publishes `plan.publish` JSON before any
   implementation, preserving original criteria exactly. A supplied
   Owner-approved plan is preserved unchanged with its provenance.
3. **Manager** (you): accept only a READY plan; validate packets with `contracts.py`
   (`message`, `sequence`, `--require-criteria-fidelity`). Before each Worker
   dispatch, validate the plan and exact selected-task instruction transfer with
   `python "${CLAUDE_SKILL_DIR}/scripts/planner_contract.py" assignment
   <plan.json> <frozen-criteria.json> <assignment.json>`. Do not dispatch a
   non-ready plan or rewrite Planner-authored task instructions.

   **Dispatch lifecycle (every role: Worker, Tester and Reviewer):**
   - The Manager writes each `job.assign` as a UTF-8 JSON file under
     `.councilflow/runs/<task-id>/messages/` with its own `message_id`, and
     `in_reply_to` set to the message it answers (the plan, or the prior report).
   - The Manager validates that file with `contracts.py message --root .
     --expected-sender manager` and, where a chain exists, `contracts.py sequence`.
     Only after both pass does it launch the native subagent.
   - The launch prompt passes the assignment's exact `message_id` and file path.
     The subagent writes its `job.report` with `in_reply_to` equal to that
     `message_id`. It must not invent or reuse another assignment.
   - Dispatch stops if the assignment is missing, invalid, or references a stale
     candidate. The Manager never writes a backdated or manufactured assignment
     afterward to make a report validate.
   - A failed or invalid message stays where it is, or moves unchanged to a
     `rejected/` folder, as evidence. It is never rewritten into a valid one.
4. **Worker** (`council-worker`): implements within scope, runs developer
   checks, returns `job.report` with actual changed files and evidence, then
   stops. Never self-approves.
5. **Tester** (`council-tester`): fresh; independently runs the original
   acceptance on the exact candidate; records executable path, args, cwd,
   candidate/input hashes, exit code and SHA-256 of stdout after CRLF→LF only.
   Does not repair product.
6. **Reviewer** (`council-reviewer`): fresh; compares frozen plan, Worker
   candidate and Tester evidence; independently reruns the Tester-declared
   deterministic command, compares exit code and normalized stdout SHA-256 and
   reports to you. Mismatch fails review; no command = NOT_COMPARABLE and
   cannot pass. No subjective UX scoring.

   **Tester dispatch requires a persisted Worker report.** Before the Tester is
   launched, the Manager must have a validated Worker `job.report` in `messages/`
   whose `in_reply_to` is the Worker assignment and whose `candidate_ref` is
   non-null and equal to the candidate being verified. A Worker report that
   exists only as chat text, or that has `candidate_ref: null`, stops dispatch
   and is reported as BLOCKED. The Manager must not write or edit the Worker's
   report on its behalf.

   **Reviewer dispatch requires its own assignment.** After the Tester's
   `job.report` validates, the Manager first writes a new Reviewer `job.assign`
   with `in_reply_to` set to that Tester report's `message_id`. It carries the
   exact `candidate_ref` and references the Tester report by path and SHA-256.
   Only after `contracts.py message` and `sequence` pass is the fresh Reviewer
   launched with that assignment's `message_id`. Its `job.report` then uses that
   assignment as `in_reply_to`. Sending the Reviewer without this assignment, or
   reusing an earlier one, is a dispatch defect: stop and report it.
7. **Rework**: record `task.decision` (accept/reject/rework/escalate) from
   evidence. In-scope rework uses a fresh Worker under unchanged criteria,
   then affected independent checks (see recovery.md). Never silently change
   mandatory criteria; new scope or authorization belongs to the Owner.
8. **Final Planner check**: send verified `plan.progress` to the Planner,
   which returns `plan.check` against the original criteria. Report genuine
   unmet requirements; never invent approval.

## Evidence and honesty

Report only observed results. Structural validation is not sender
authentication, transport control or OS isolation; agent files and JSON grant no
permissions (Claude Code's permission system is the only enforcement, and agent
`tools` lists restrict tool availability, not what an allowed tool may touch).
Efficiency helpers stay disabled unless the Owner explicitly asks; then follow
`CF/references/efficiency.md` using the `CF` script paths. They capture nothing
automatically and unknown cost/quota/upstream-model fields stay unknown. The
Phase 5 evaluation protocol remains DRAFT_NOT_AUTHORIZED.
Without actual host evidence of invocation and real separate agents, status is
UNVERIFIED — not verified.
