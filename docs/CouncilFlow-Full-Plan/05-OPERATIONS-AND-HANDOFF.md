# 05 — Codex Cloud usage, installation and handoff

## How to use this bundle

1. Open existing CouncilFlow repository in Codex Cloud, at or after reported commit `d30e906`.
2. Supply/unpack this bundle within the authorized repository context or attach it so Codex can read it. Do not replace the repository source with this documentation archive.
3. Give the agent `prompts/ONE-SHOT-CODEX-CLOUD.md` as its single implementation task. It includes self-contained requirements if the archive is not available.
4. Codex must inspect existing code first, then implement only missing requirements. Its final report must distinguish contract correctness from native activation proof.

## Invocation after actual installation

`$council-flow Build a small offline expense tracker with validation and automated tests.`

That is a target command, **not proof of successful current activation**. Native Codex skill discovery and invocation must be shown in an authenticated session. If Cloud CLI refresh fails, it can still complete local contract work; it must report activation as unverified, not fix credentials via unsupported means.

## Deliverable paths (targets, not verified repository contents)

- `.agents/skills/council-flow/SKILL.md`
- `.agents/skills/council-flow/references/` containing roles, workflow, acceptance, protocol, policy and recovery guides
- `.codex/agents/*.toml` where supported
- `reports/requirements-traceability.md`
- `reports/final.md`
- `dist/council-flow.zip`
- `demo/` and `tests/`

## Communication with the Owner

Short final: completion classification, installed skill path, actual activation result, real agent session count, tests executed, commit and ZIP, one next step. Do not flood with JSON/XML or ask for repeated approval of ordinary repairs.

## Recovery and Git

- Changes to existing CouncilFlow only; never touch old ACP.
- Preserve clean commit checkpoints. Don't fabricate Git hashes.
- Verify ZIP content, no private keys or token leaks.
- If work is blocked, preserve tested source and identify the exact missing host capability/permission.

## Installation acceptance

Repo-scoped installation and successful native skill discovery must be observed. A globally installed skill is optional, not required; no edits to `~/.codex` without Owner authorization. Cloud completion does not automatically install local PC skills.
