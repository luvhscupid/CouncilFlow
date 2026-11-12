# 00 — Project scope, authority, baseline

## Objective

Build and maintain **CouncilFlow**, a reusable Codex skill, similar in purpose to a coding-team workflow organizer but based on the Owner's five-role architecture. A normal request such as `$council-flow Build an offline expense tracker` must cause real task planning, bounded delegation, implementation, independent technical testing, experiential review, repair as needed, final objective check and an evidence-based user-facing result.

The product is a **skill** installed in Codex; no standalone Python/SQLite orchestration engine, paid provider gateway, web dashboard, or independent AI-service subscription is required.

## Reported existing repository state

- Location (reported in Codex Cloud): `/workspace/CouncilFlow`.
- Commit (reported): `d30e906`.
- Reported artifacts: `.agents/skills/council-flow/SKILL.md`, `.codex/agents/*.toml`, release ZIP, receipt demonstration, tests, `reports/final.md`.
- Reported build checks: 11 app tests + 5 behavior tests + 8 static checks; independent execution **not verified in this bundle**.
- Reported demo: Rp103,000 receipt total; real role sessions claimed, but skill instructions applied manually.
- Skill discovery reportedly passed; **explicit native `$council-flow` invocation remains UNVERIFIED**, CLI token refresh failed.
- The follow-up communication contract restoration prompt has been written, but there is no confirmed result in this conversation yet. DO NOT assume it has been executed.

## Preserve vs. adapt

Preserve: Owner/Planner/Manager/Worker/Tester/Reviewer responsibilities; fresh Worker/Tester/Reviewer; Manager handles in-scope rework; independent evidence; no scope/criteria weakening without Owner decision; subjectivity requires Owner signoff; security and tool permissions remain external to model-generated content.

Adapt for Codex Skill: the original Council 001 design includes trusted controller, immutable store, restricted verifier and SQLite; **a markdown Codex skill cannot enforce those features by itself**. Do not claim or silently reconstruct all ACP runtime guarantees. The skill may express policies and use Codex native safeguards, but should mark host-enforcement limitations.

## Document authority

1. Current Owner request and confirmed decisions: deliver *installable, usable Codex agent skill* and preserve preferred structured communication.
2. Original Council 001 Architecture v1.0 source: foundational architecture/trust model; not equivalent to finished skill specification.
3. Original Council Annex v1.0-A: approved historically, **exact text missing**; compatibility cannot be certified.
4. November 9 ACP-SPEC v0.1: **proposed** source for structured communication and role separation.
5. Current CouncilFlow prompt: operational requirements for the new skill project, not a retroactive claim that the original Council docs explicitly mandated `.agents/skills`.

## No-new-project rule

Use the **existing CouncilFlow** repo. Leave old ACP, Execution Kernel, and Codex on Crack untouched. Never make another new project because native skill invocation or authentication is difficult.
