# 03 — Execution order and objective acceptance gates

## Actual state

Reported CouncilFlow initial implementation: repository-scoped skill built, demo calculator works, five sessions manually used instructions, token-refresh error prevented direct `$council-flow` activation proof. Do not claim this gap closed until observed. Current communication restoration prompt unexecuted/unverified in this bundle.

## Dependency order (one Codex Cloud assignment)

**Gate 0 — Read before editing.** Inspect current repository, git status, SKILL.md, references, agent TOML, tests, demo, reports, existing policies. Check current documented Codex features. Do not assume missing capabilities or silently rebuild.

**Gate 1 — Product intact.** Skill exists under `.agents/skills/council-flow/SKILL.md`, with frontmatter and proper references; native agent definitions remain compatible; the earlier demo/tests pass. Do not replace product with services.

**Gate 2 — Restore protocol.** Schema/versioned JSON, role-specific payloads, YAML role/policy, native TOML compatibility, optional JSONL, concise owner interface. Actually integrate into SKILL.md instructions and role handoffs. Test malformed/duplicate/role spoofing, evidence, rework, plan revision.

**Gate 3 — Real activation.** Attempt native `$council-flow` discovery/invocation in an authorized authenticated Codex session. This is NOT satisfied by reading SKILL.md or manually replaying its prompt. If blocked by token refresh, report exact error with honest `NATIVE_ACTIVATION_UNVERIFIED`, preserve completed work, do not bypass auth.

**Gate 4 — Live coding demonstration.** A real Worker edits a test application, Tester independently runs meaningful behavioral tests, Reviewer independently evaluates UX, Manager reworks if failing, Planner compares final evidence with the original plan. Use new demo task (offline CSV summarizer), not only the existing receipt demo, for activation evidence.

**Gate 5 — Release.** Tests green, ZIP contains actual updated skill, manifest verified, commit to repository, owner-facing succinct report with links and outstanding limitations. Do not publish private project or modify global install without approval.

## Acceptance matrix

| ID | Mandatory requirement | Evidence necessary | If unsupported |
|---|---|---|---|
| A01 | Skill metadata/file exists | Repository file + valid frontmatter check | FAIL |
| A02 | Native skill discovery | Actual host discovery output | UNVERIFIED |
| A03 | Explicit `$council-flow` invocation | Native invocation evidence, not copied instructions | UNVERIFIED |
| A04 | Planner criteria stable | Plan ID/revision + acceptance IDs | FAIL |
| A05 | Manager coordinates without coding | Actual role dispatch trace | UNVERIFIED |
| A06 | Real fresh Worker implements | Host session or dispatch evidence + changed files | UNVERIFIED |
| A07 | Independent Tester runs executable checks | Distinct session + command outputs | UNVERIFIED |
| A08 | Independent Reviewer evaluates | Distinct session + scenario limits | UNVERIFIED |
| A09 | Mandatory failures cause rework/block | Recorded failed check → decision → fresh attempt | UNVERIFIED |
| A10 | Planner final objective check | Original requirements compared to final evidence | FAIL |
| A11 | JSON contract validated | Strict negative/positive tests | FAIL |
| A12 | YAML policy and native TOML present | File checks; config validation if host supports | FAIL |
| A13 | Optional diagnostics do not leak secrets | Sample JSONL checks/redaction tests | FAIL if implemented unsafely |
| A14 | Normal Owner summary concise and true | Final text matches observed evidence | FAIL |
| A15 | Existing code/tests preserved | Full tests incl receipt demo | FAIL |
| A16 | No old ACP/ACL/global/paid dependency | Repo diff, commands, packaging inventory | FAIL |
| A17 | ZIP installable and complete | Inspect archive and test install/discovery | UNVERIFIED until real install |

## Prohibit success inflation

Use exactly: `COUNCILFLOW_FULLY_VERIFIED` only when native invocation AND true distinct agent role proof AND working code/test demonstration pass; `CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED` if all local contract checks pass but invocation is blocked; otherwise `PARTIAL — exact blocker` or `FAILED — exact failure`.

Static tests validate files, not real delegation. Manual role sessions validate instructions, not native skill invocation. Do not average statuses into 'complete'.

## What to report

Repository path and commit; source changes; exact tests/commands/counts; observed real session roles and host outputs; actual program output; faults and recovery; native skill invocation result; installation and usage instructions; remaining gaps. Identify missing original Council Security Annex explicitly as unavailable if assessing its compliance.
