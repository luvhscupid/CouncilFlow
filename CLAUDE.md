# CouncilFlow project contract

CouncilFlow is an installable multi-agent workflow **skill** for existing AI
coding environments. The current implementation is Codex-native; Claude Code
support is a possible extension, not a verified existing feature. Packaging as a
plugin is possible where the host supports plugins.

CouncilFlow uses the host's existing models, tools, permissions and native agent
delegation. Planner, Manager, Worker, Tester and Reviewer are workflow
responsibilities executed through those capabilities, not independent servers
or processes. Preserve the approved architecture and role responsibilities:
Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner.

CouncilFlow is not a standalone AI agent or coding assistant, an independent
orchestration platform or runtime, a replacement for Codex/Claude Code or native
delegation, or a separate provider, gateway, billing service or SaaS application.
Specifically authorized scripts, deterministic utilities, schemas and optional
adapters may support the skill; a skill/plugin extension must not silently
become a standalone platform.

Before changing workflow or roles, read `.agents/skills/council-flow/SKILL.md`
and the controlling `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`,
as amended by `docs/decisions/CHARTER-AMENDMENT-001.md` (ADR-001, accepted
2026-11-26; its implementation steps each need separate Owner authorization).
Existing Owner decisions, frozen specifications and role policies retain their
authority. This identity contract does not authorize simplifying, discarding or
changing them. Manager coordinates rather than implements; Reviewer compares
Worker output, Tester evidence and the original frozen Owner plan, including
the required independent deterministic command rerun.

Treat `docs/research/` as non-normative proposals. Memory, token efficiency,
model selection and xKiro research do not independently authorize implementation,
installation, experiments or spending. Preserve historical research and frozen
Gate 3 records; implement extensions only within explicit Owner authorization.

For structural codebase exploration, use the installed `codebase-memory` skill.
Verify exact project/root mapping and relevant coverage; project instructions
and direct source checks remain authoritative over graph interpretations.
Preserve unrelated local edits and Git safeguards; report only observed results.
