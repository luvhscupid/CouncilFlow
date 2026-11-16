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
- **Role selection fallback.** If a named plugin agent cannot be launched, give
  the same role instructions (this plugin's agent file body plus
  `CF/references/roles.md`) to a `general-purpose` subagent and disclose the
  fallback. If no subagent can run, report BLOCKED/UNVERIFIED.
- **Permissions** are only what Claude Code actually enforces. Agent `tools`
  lists restrict tool availability, not what an allowed tool may touch; they
  are not a sandbox. No instruction here grants permission or isolation.
- Live delegation, upstream model identity, cost and quota are unknown unless
  actually observed; report them as unknown.
