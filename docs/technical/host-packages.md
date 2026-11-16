# Host packages

CouncilFlow ships two host packages built from one canonical runtime. Both have offline checks. One real Claude Code smoke run completed
**VERIFIED_ACCEPT**; this does not establish universal host compatibility.
Upstream model identity, effective route, cost and quota remain unknown.

| Host | Package | Invocation | Status |
| --- | --- | --- | --- |
| Codex | `.agents/skills/council-flow/` and `.codex/agents/*.toml` (`dist/council-flow.zip`) | `$council-flow <goal>` | Supported native skill and role workflow. Run 01: **NATIVE_ROLE_WORKFLOW_PARTIAL**; E1/E2/E4 UNVERIFIED, other seven checks PASS |
| Claude Code | `plugins/councilflow/` (`dist/councilflow-claude-plugin.zip`) | `/councilflow:run <goal>` | Installable plugin; one real smoke run **VERIFIED_ACCEPT**, with native Planner, Worker, Tester and Reviewer sessions and an 11-message validated sequence |

Evidence: [Gate 3 Run 01](../../reports/documentation-release-sync/gate3-run-01.md) and
[Claude calc-001](../../reports/documentation-release-sync/claude-calc-001.md).
Agent Efficiency helpers are offline-tested and opt-in; live adapter and billing compatibility
remain unverified. Package D remains **DRAFT_NOT_AUTHORIZED**.

## Shared runtime

The Claude Code plugin reuses the canonical runtime: `references/`, `policies/` and
`scripts/`, including `contracts.py` and the opt-in efficiency helpers. The builder
`tools/build_claude_plugin.py` copies these byte-for-byte from the Codex skill. A test
fails if the copy drifts from the canonical version.

To refresh the copy after editing the Codex skill, run:

```sh
python tools/build_claude_plugin.py sync         # refresh shared runtime
python tools/build_claude_plugin.py build        # writes dist/councilflow-claude-plugin.zip and its .sha256
```

## Claude Code specifics

Claude Code subagents cannot spawn other subagents. The main session therefore acts as the
Manager and directly launches the four plugin agents:
`councilflow:council-planner`, `councilflow:council-worker`,
`councilflow:council-tester` and `councilflow:council-reviewer`.

Agent files and JSON packets are instructions, not a sandbox. Claude Code's permission
system is the only enforcement.

See [Claude Code plugin](claude-code-plugin.md) for loading and use.

## Codex specifics

The Codex skill uses native Codex delegation and inherited account and provider
permissions. It needs no API key, subscription, database, server or custom agent runtime.
Role instructions are expected behavior, not independent OS-enforced isolation.

For installation into another repository, see the
[main README](../../README.md#install-in-another-repository).

## Release verification

Package contents and verification commands are in [RELEASE.md](../../RELEASE.md).
