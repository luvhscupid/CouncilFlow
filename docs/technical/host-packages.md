# Host packages

The current release scope is the Codex-native CouncilFlow skill.

| Host | Package | Invocation | Status |
| --- | --- | --- | --- |
| Codex | `.agents/skills/council-flow/` and `.codex/agents/*.toml` (`dist/council-flow.zip`) | `$council-flow <goal>` | Supported native skill and role workflow. Run 01: **NATIVE_ROLE_WORKFLOW_PARTIAL**; E1/E2/E4 UNVERIFIED, other seven checks PASS |

Evidence: [Gate 3 Run 01](../../reports/documentation-release-sync/gate3-run-01.md).
Agent Efficiency helpers are offline-tested and opt-in; live adapter and billing compatibility
remain unverified. Package D remains **DRAFT_NOT_AUTHORIZED**.

## Historical Claude Code package

The plugin source and ZIP are retained from earlier work. The recorded
[calc-001 smoke run](../../reports/documentation-release-sync/claude-calc-001.md)
completed `VERIFIED_ACCEPT` for that candidate with four native delegated roles
and an 11-message sequence. Its effective route, cost and quota were unknown.
Claude Code remains a possible extension under the current project contract.
The [historical plugin instructions](claude-code-plugin.md) describe that prototype.

## Codex specifics

The Codex skill uses native Codex delegation and inherited account and provider
permissions. It needs no API key, subscription, database, server or custom agent runtime.
Role instructions are expected behavior, not independent OS-enforced isolation.

For installation into another repository, see the
[main README](../../README.md#install-in-another-repository).

## Release verification

Package contents and verification commands are in [RELEASE.md](../../RELEASE.md).
