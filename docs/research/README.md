# CouncilFlow research

This directory holds research and planning records. **They are non-normative.** They are not approved features, not frozen contracts, and not independent implementation authority. Reading them does not authorize coding, installation, experiments or spending.

## Documents

- [Token and context efficiency](AI-Agent-Token-and-Context-Efficiency-2026-11-15.md). A closed research record (status CLOSED). It records discussion and agreed research conclusions. It is not normative and not an approved implementation task.
- [Draft efficiency implementation phases](Agent-Efficiency-Implementation-Phases-DRAFT-2026-11-15.md). A draft plan, ready for Owner review. It authorizes no implementation. It turns the research into possible bounded tasks.
- [Model selection and xKiro](Universal-Model-Selector-xKiro-GPT6-Haiku-2026-11-15.md). A closed planning-level consensus record (status CLOSED, non-normative, no implementation authorized). It preserves a proposed model-selector design so it can be recalled later.

## Scope and authority

CouncilFlow is an installable multi-agent workflow skill for existing AI coding environments, currently Codex-native. It is not a standalone AI agent, coding assistant, orchestration platform or runtime, provider, gateway, billing service, or SaaS application. It does not replace the host or its native delegation.

- Codex supports the native skill and role workflow. Gate 3 Run 01 is **NATIVE_ROLE_WORKFLOW_PARTIAL**: E1, E2 and E4 remain UNVERIFIED; the other seven checks passed.
- Claude Code is an installable plugin. One real `/councilflow:run` smoke test completed **VERIFIED_ACCEPT**, with actual native Planner, Worker, Tester and Reviewer sessions and a validated 11-message sequence. This does not establish universal host compatibility. Upstream model identity, effective route, cost and quota remain unknown.
- Agent Efficiency helpers are offline-tested and opt-in. Live adapter and billing compatibility remain unverified; Package D remains **DRAFT_NOT_AUTHORIZED**.
- Current evidence summaries: [Gate 3 Run 01](../../reports/documentation-release-sync/gate3-run-01.md) and [Claude calc-001](../../reports/documentation-release-sync/claude-calc-001.md). These current statuses do not amend the historical research or authorize its proposals.
- The roles use host models, tools, permissions and native delegation. They do not require independent role servers or processes.
- Memory, efficiency, model-selection and xKiro proposals require explicit Owner authorization before implementation, installation, experiments or spending.
- Authorized supporting scripts, utilities, schemas and optional adapters may extend the skill or plugin ecosystem. They must not silently turn CouncilFlow into a standalone platform.

## Controlling sources

These documents are authoritative over this directory:

- [Gate 3 Owner Charter](../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md) and the rest of the [Gate 3 package](../gate3/README.md).
- Existing Owner decisions, frozen specifications and role policies.

Research does not redefine the approved architecture or responsibilities. Historical research and frozen Gate 3 records remain unchanged.

Before proposing changes, read the [root project contract](../../AGENTS.md) and the [current skill](../../.agents/skills/council-flow/SKILL.md).
