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

The shared CouncilFlow references and scripts are copied byte-identically from
the canonical Codex skill. Apply this mapping when they say otherwise:

| Shared text says | In this package |
| --- | --- |
| `$council-flow` | `/councilflow:run` |
| `.agents/skills/council-flow/` | `${CLAUDE_SKILL_DIR}` = `CF` below (read-only install cache; do not write there) |
| `.codex/agents/council-*.toml` | plugin agents `councilflow:council-planner`, `-worker`, `-tester`, `-reviewer` |
| `inherit_native_codex` | inherit Claude Code's actual permissions |

`CF` = `${CLAUDE_SKILL_DIR}`. Contract helper: `python "${CLAUDE_SKILL_DIR}/scripts/contracts.py"`.
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

Read `CF/references/communication.md`, `roles.md`, `workflow.md`,
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
3. **Manager** (you): accept the plan; validate packets with `contracts.py`
   (`message`, `sequence`, `--require-criteria-fidelity`); send `job.assign`
   to a fresh Worker.
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
