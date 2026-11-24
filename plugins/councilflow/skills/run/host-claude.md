# Claude Code host adapter (authoritative over shared wording)

This file is specific to the Claude Code package. `references/`, `policies/` and
`scripts/` are shared with the Codex package and are kept byte-identical to the
canonical copy; they are host-neutral in their contract rules but still contain
Codex wording and `.agents/skills/council-flow/...` example paths. **When shared
text and this file disagree about host mechanics, this file wins.** Contract
rules (JSON packets, source fidelity, independent Tester/Reviewer, deterministic
rerun comparison, rework, honesty about verification) are never overridden.

`CF` means the directory containing this file and `scripts/contracts.py`
(`${CLAUDE_SKILL_DIR}` in `SKILL.md`: the skill directory `skills/run`, not the
plugin root). Resolve it to an absolute path and pass that to every subagent.
CF is inside the plugin install cache: read and execute from it, never write there.

## Mapping

| Shared text | Claude Code meaning |
| --- | --- |
| `$council-flow` | `/councilflow:run` |
| `.agents/skills/council-flow/` (scripts, references, policies) | `CF/` — e.g. `python CF/scripts/contracts.py ...` |
| `.agents/skills/council-flow/scripts/efficiency.py` | `CF/scripts/efficiency.py` (opt-in only) |
| `.agents/skills/council-flow/scripts/planner_contract.py` | `CF/scripts/planner_contract.py` (Manager READY-plan check before Worker launch) |
| `.agents/skills/council-flow/scripts/route.py` | `CF/scripts/route.py` (opt-in routing hint; advice only) |
| `.codex/agents/council-*.toml`, "native TOML" | plugin agents `councilflow:council-planner`, `-worker`, `-tester`, `-reviewer` (Markdown files with YAML frontmatter in the plugin's `agents/`). Their body text is the `developer_instructions` equivalent. |
| "native Codex subagents/transport/permissions", `inherit_native_codex` | Claude Code subagents (Agent tool), transport and permission system |
| `mcp__codex_app__list_projects` example | irrelevant; only the Codebase Memory MCP namespace qualifies, discovered via the tools actually exposed in this session |
| CouncilFlow installation files (installation-only project test) | the plugin directory, and any copy of the shared skill/agents; they do not count as project source |

`roles.yaml` still says `native: toml` and `inherit_native_codex`; it is a
shared, validated policy file and grants no permissions. Read those values using
the table.

## Rules specific to this host

- **Manager = the main session.** Subagents cannot spawn subagents, so only the
  main session delegates. Subagents never delegate or contact each other; the
  Manager hands references/paths directly between them (no Owner courier work).
- **Run artifacts** live in the target repository under
  `.councilflow/runs/<task-id>/`. Packets are UTF-8 JSON referencing evidence by
  path + SHA-256. Run helpers with cwd = the target repository, e.g.
  `python CF/scripts/contracts.py sequence plan.json assign.json --root . ...`.
- **Dispatch requires a validated assignment first.** For Worker, Tester and
  Reviewer alike, the Manager writes and validates the `job.assign` (message
  file, `contracts.py message --root . --expected-sender manager`, plus
  `sequence` once a chain exists) before launching the native subagent. The
  launch prompt carries that assignment's exact `message_id` and path, and the
  subagent's `job.report.in_reply_to` must equal it. A missing or invalid
  assignment stops dispatch. The Manager must not create a backdated assignment
  to repair a report; rejected messages are preserved unchanged as evidence.
- **READY plan check before Worker launch.** Before launching a Worker
  subagent, the main session runs `python CF/scripts/planner_contract.py
  assignment <plan.json> <frozen-criteria.json> <assignment.json>` from the
  target repository. Exit 2 stops the launch. A Planner NEEDS_INFORMATION or
  BLOCKED answer is saved as evidence and taken to the Owner, never dispatched.
- **Routing hints are advice.** If the Owner supplied a route config, the main
  session may run `CF/scripts/route.py`, then accept, ignore or override the
  hint and record the choice. A hint never selects a subagent, model or tool.
- **Every subagent report is persisted as a message file.** A `job.report` that
  exists only in the subagent's chat reply is not a controlled message. The
  Manager saves each report under `messages/` with `python CF/scripts/contracts.py
  save <report.json> --run .councilflow/runs/<task-id> --root .`, which refuses a
  bare report body and anything that fails validation, with
  `in_reply_to` set to its assignment, before any later step. A Reviewer
  comparison requires the Worker's own `job.report` bound to the candidate
  (`candidate_ref` equal to the verified candidate), so a Worker that returned
  `candidate_ref: null` must be reported as BLOCKED, not backfilled.
- **Reviewer comparison references the Tester message exactly.** The Reviewer's
  `comparison.tester_report_ref.artifact_id` must equal the Tester `job.report`'s
  `message_id` (kind `message`), with `path` and `sha256` of that exact file.
  A reference using any other artifact id is a defect, not a valid comparison.
- **Reviewer after Tester is a separate dispatch.** The Tester's validated report
  is the input to a new Manager `job.assign` for the Reviewer (`in_reply_to` =
  Tester report `message_id`, exact `candidate_ref`, Tester report referenced by
  path and SHA-256). Only that assignment, once validated, authorizes launching
  the fresh Reviewer. A Reviewer report without a matching assignment is invalid.
- **Role selection fallback.** If a named plugin agent cannot be launched, give
  the same role instructions (this plugin's agent file body plus
  `CF/references/roles.md`) to a `general-purpose` subagent and disclose the
  fallback. If no subagent can run, report BLOCKED/UNVERIFIED.
- **Permissions** are only what Claude Code actually enforces. Agent `tools`
  lists restrict tool availability, not what an allowed tool may touch; they
  are not a sandbox. No instruction here grants permission or isolation.
- Live delegation, upstream model identity, cost and quota are unknown unless
  actually observed; report them as unknown.
