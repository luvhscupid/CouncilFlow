# Multi-agent evolution branch status

**Branch:** `evolution/multi-agent-plan-2026-11-17`
**Base:** `5d8eb8686c51c392c0689e04932758ca30a76f2d`
**Scope:** Offline implementation and repository verification only. No live model requests, provider changes, host configuration edits, OS permission changes, merge, release publication, or promotion. The feature branch itself is pushed.

| Plan phase | Status | Result |
| --- | --- | --- |
| P0 baseline | `REFRESHED; LICENSE_UNKNOWN` | Latest refresh below: remote `main` still matches the branch base; feature branch is pushed at the recorded HEAD; no open PRs; remote branches inventoried. Project license remains unresolved. |
| P1 Agent Efficiency | `OFFLINE_QUALIFICATION_COMPLETE; LIVE_BLOCKED_OWNER_INPUT` | Existing efficiency component suite: 76 run, 75 pass, 1 platform skip. Package D: 3 run, 3 pass. Synthetic evaluator returned `CLOSED_NO_BENEFIT` and `NOT_APPROVED; offline analysis only`. No trial or model call was run. |
| P2 capability-aware routing | `NATIVE_OVERRIDE_ARGUMENT_DOCUMENTED; CAPABILITY_QUERY_UNSUPPORTED; EFFECTIVE_ROUTE_UNVERIFIED; INHERIT_HOST` | Pure role preference validation remains offline. Codex CLI documents a generic `--model <MODEL>` override, and the collaboration tool schema accepts per-delegation `model` with `fork_turns="none"`; neither interface documents role-capability discovery or effective-route attestation. Claude CLI is absent. No adapter or selector is added; caller claims remain `UNKNOWN`, effective model remains null, and selection inherits the host. See the P2 handoff plan. |
| P3 local journal prototype | `EXPERIMENTAL_V2_LOCAL_CHECKS; HOST_AUTH_UNVERIFIED` | Schema v2 journal under `experiments/multi-agent-evolution/` remains outside installable runtime. It records attempt/parent identity and can read-only check local event chains and explicitly rooted candidate bytes. V1 remains read-only export. Actor/session and approval claims remain unverified; OS-platform coverage beyond Linux is unverified. No dispatch/replay or durable-user-data path exists. |
| P4 DAG/isolation | `ISOLATION_BLOCKED; SERIAL_MUTATION` | Pure graph validation remains offline and passes 5 focused tests. This environment has `bwrap` and a Codex sandbox CLI, but no worker-specific sandbox policy/state or cross-workspace deny evidence was available; unrestricted workspace access is not isolation evidence. No scheduler, model worker, or parallel write was started. |
| P5 experience/doctor/observability | `OFFLINE_SCHEMA_V2_COMPLETE; AUTHORITY_UNVERIFIED` | Duplicate experience IDs fail closed; selection remains project/supersession metadata filtering with `review_status: UNVERIFIED`. Doctor schema v1 output remains stable; v2 hashes rooted executable bytes without executing them and marks caller host records `UNVERIFIED`. No Worker-context injection or dashboard exists. |
| P6 workflow optimization | `OFFLINE_FIXTURE_ONLY; LIVE_BLOCKED_OWNER_INPUT` | Evaluator tests pass 3/3 and the fixture remains descriptive only. No approved phase card, host/route, frozen task/oracle set, independent verifier bindings, complete telemetry/retention, all-role numeric budgets, enforced stop control, or effect/reliability decision rule exists. No live call or promotion was performed. |
| P7 opinion board | `NOT_APPLICABLE_TO_CORE; SEPARATE_PROJECT_REQUIRED` | Threat review recorded below. No board service or runtime was added; a separate user need and design authorization are prerequisites. |

## Verification

- `python -B -m unittest discover -s tests -v`: **262 tests passed, 1 platform skip** before the 2026-11-19 review follow-up; see the follow-up plan for final rerun evidence.
- `python -B -m unittest discover -s experiments/agent-efficiency -v`: **3 passed**.
- `python -B tools/build_release.py`: package built with source-byte and CRC checks passing.
- `python -B tools/build_claude_plugin.py sync`, `check`, and `build`: shared runtime synchronized; package built.
- Synthetic evaluator ran offline only and explicitly returned `NOT_APPROVED; offline analysis only`.

## Limits

The product helpers are deterministic local code, not a trusted supervisor or authentication layer. The journal prototype is not included in product bundles. Capability/profile data is caller-supplied; it cannot prove actual host route or model identity. The journal checks local event/attempt chains and explicitly rooted candidate bytes, but it does not authenticate actors or approvals, validate opaque evidence references, or establish cross-platform crash recovery. The DAG helper does not enforce workspace separation. No evidence here establishes live Codex or Claude activation, model cost, quota, billing, or workflow improvement.

## 2026-11-19 review follow-up

- Experience entries use `review_claim`; every validated entry is labeled `review_status: UNVERIFIED`.
- Stale plan revisions block the affected task and descendants.
- Tracked ZIP regeneration is documented as package consistency, not release promotion.
- Follow-up verification: **264 tests passed, 1 platform skip**; Claude shared runtime sync, both package builds, `git diff --check`, and independent review passed.

## 2026-11-19 Anti-Slop audit follow-up

- Doctor statuses now distinguish local schema/digest checks (`PASS`), missing required data (`BLOCKED`), malformed evidence or digest mismatch (`FAIL`), unconfigured optional dashboard (`SKIP`), and native-session/caller claims (`UNVERIFIED`).
- Public validators reject boolean-as-integer and other malformed JSON values with controlled `ValueError`s.
- Journal guarantees are scoped to the tested local SQLite prototype. Tests inspect persisted schema metadata, reject unsupported versions, reopen for stable export, and validate complete/malformed acceptance metadata.
- Experience review remains caller-claimed; the helper never authenticates the claimed reviewer.
- Final follow-up verification: `python -B -m unittest discover -s tests -v` — **277 passed, 1 platform skip**; `python -B -m unittest discover -s experiments/agent-efficiency -v` — **3 passed**. Claude runtime `sync` and `check`, both package builds, and `git diff --check` passed. The final independent review found two P2 edge cases (unhashable DAG status and FIFO source reference); both were reproduced with regression tests, fixed, and re-reviewed. No unresolved P1/P2 findings remained.

## 2026-11-19 completion-plan P0 refresh

- Worktree: `evolution/multi-agent-plan-2026-11-17`; clean before this refresh at `54388d0eb643012d65bff26cfa388aabab5e99ba`.
- Base: `origin/main` is `5d8eb8686c51c392c0689e04932758ca30a76f2d`; `git merge-base HEAD origin/main` returns that SHA. Remote `main` remains unchanged.
- Feature branch: local HEAD and `git ls-remote` both report `54388d0eb643012d65bff26cfa388aabab5e99ba`; previous tracking ref was `54bcc1485bb323fd1c2ecb29d1d40f47a0b5a9f9`. The local commits ahead of the old tracking ref are `a76b20a`, `317eee0`, and `54388d0`; all are now on origin.
- GitHub inventory (authenticated `gh` CLI, 2026-11-19): open PR list is empty. Remote branch names were inventoried; additional branches exist, but this refresh did not merge or select their changes. No branch is incorporated based only on its name.
- License: no root `LICENSE` is tracked. Audit-remediation Slice 02 remains proposed and not authorized; no license is inferred. Existing-code/standard-library work may proceed, while external-source reuse and distribution decisions remain blocked on an Owner license decision.
- Commands documented in `RELEASE.md`: seven maintained unittest suites plus the separate Agent Efficiency suite; package checks/builders are `tools/build_claude_plugin.py sync|check|build` and `tools/build_release.py`. In this environment, focused package/release tests ran: 22 passed. Repository runtime: Linux x86_64, Python 3.12.14; Codex CLI is present, Claude CLI is absent. No host model request or configuration change was made.
- Audit-remediation Slice 02 is kept separate. Slice 03 has no completed run evidence: its record remains `NOT AUTHORIZED`; no host evidence is available to this plan from it.
- Execution boundary: zero live calls/spend, no provider or host configuration changes, no permissions changes, no merge, release, or promotion. Branch-only commits/pushes are within the existing authorization.

## 2026-11-19 completion-plan P2 host capability result

- Current environment observation: Codex CLI `0.167.0-alpha.4`; `claude` executable absent. `codex --help` exposes a generic `--model <MODEL>` override but does not document a role-capability registry, query API, or authenticated effective-route result. This is insufficient for the pure profile/capability contract to claim native capability or route verification.
- Focused `tests.test_role_capabilities`: 7 passed. Caller-supplied capabilities remain unverified; unobserved capability resolves to inherited host behavior with null effective model. Claude mirror check passed and canonical/Claude files are byte-identical.
- P2 closes `UNSUPPORTED_HOST_CAPABILITY_QUERY` for this environment. No adapter, model override, native smoke, or model request was run. A future host-specific adapter requires documented capability semantics and its own approved subplan/card.

## 2026-11-19 completion-plan independent-review remediation

- Codex package builder now excludes `tests/test_journal.py`, whose experimental source is deliberately outside the standalone archive. Release tests assert the exclusion; the portable-release workflow continues to extract the ZIP and run test discovery against that clean tree.
- Journal acceptance now binds to the exact candidate descriptor from the same attempt; attempt IDs cannot be reused after rework. `reconcile` derives run state and integrity from one SQLite read snapshot and returns `UNAVAILABLE` with `JOURNAL_UNAVAILABLE` for unreadable storage. Persisted plan metadata and duplicate JSON keys are validated.
- Doctor and journal artifact reads retain and revalidate every directory descriptor through the read, reject linked evidence roots, and report `UNVERIFIED` where descriptor-relative no-follow reads are unsupported. Doctor evidence-file CLI reads reject links, FIFOs, non-regular files, and changed files; stdin `-` remains supported.
- P2's separate handoff records the available delegation override argument and its `fork_turns="none"` constraint, while keeping capability query and effective route unknown. No override or native model request was run.
- Focused release/journal/doctor tests: **49 passed** on Linux/Python 3.12. Full-suite and package results are recorded in the closeout after the final rerun. Windows behavior remains `UNVERIFIED`.

## 2026-11-19 completion-plan P3 journal v2

- Journal schema v2 remains under the experimental directory and uses disposable test databases. Events bind exact integer run/attempt revisions, attempt identity, causal parent, actor claim, criteria reference, optional candidate path/digest, terminal reason and approval reference. Acceptance requires the existing Tester/Reviewer/Manager/Planner references plus a rooted candidate descriptor and approval reference.
- `Journal.open_readonly` exports legacy v1 without modifying its bytes; normal v2 open refuses v1 with a migration-free error. `verify_run` checks event/state/attempt consistency and in-root regular-file hashes; `reconcile` reads only and never writes, resets or dispatches. Actor and approval checks explicitly remain `UNVERIFIED`.
- Linux/Python 3.12 focused journal tests: **16 passed**. Full suite: **284 passed, 1 platform skip**. Coverage includes stale revisions, bool/unhashable state rejection, attempt transitions, event replay/parent chain, v1 preservation, digest mismatch, missing/traversal/symlink/FIFO artifacts, corruption, insert/update/commit rollback and read-only reconciliation. Windows behavior and cross-platform durability are `UNVERIFIED`; package checks confirmed no runtime ZIP contains the journal.

## 2026-11-19 completion-plan P4 isolation qualification

- Focused DAG tests: **5 passed**. `codex sandbox --help` documents a sandbox command with an opaque sandbox-state input; no authorized, concrete worker-A/worker-B policy or state was available. `bwrap` is installed, but its presence alone demonstrates no access boundary.
- This execution environment exposes a shared workspace with unrestricted filesystem permissions. No sandbox-deny probes were run, no worker processes were started, and no directory promotion was attempted.
- Required deny evidence remains `NOT RUN`: direct sibling-path read/write; symlink/reparse traversal; inherited process handle; and stale/conflicting promotion. P4 closes `ISOLATION_BLOCKED`; serial mutation remains in force. A sandbox policy/version and an approved isolated test harness are prerequisites to reopen it.

## 2026-11-19 completion-plan P5 offline evidence boundary

- Experience tests reject duplicate IDs, malformed review claims, wrong-project and superseded entries. Returned entries keep `review_status: UNVERIFIED`, and selection does not mutate source records or create Worker context.
- Doctor schema v1 preserves its output structure; artifact hashes now use no-follow regular-file reads. Schema v2 adds nullable executable-artifact and native-host fields, validates executable bytes without invoking them, and keeps host references `UNVERIFIED`.
- Focused P5 tests: **25 passed**. Full tests: **294 passed, 1 platform skip**. Canonical/Claude copies are synchronized; package check/build results are recorded with the final P5 run.

## 2026-11-19 completion-plan P6 live preflight

- `python -B -m unittest discover -s experiments/agent-efficiency -v`: **3 passed**; the existing fixture still reports its descriptive `CLOSED_NO_BENEFIT` result and `NOT_APPROVED; offline analysis only` status.
- No phase card is approved and no host/route, oracle hashes, independent Tester/Reviewer bindings, complete telemetry/retention, numeric all-role call/quota/cost/time ceilings, enforced stop operator, or effect/reliability decision rule is supplied. P2 host capability query is also unsupported in this environment.
- P6 closes `BLOCKED_OWNER_INPUT`. No fixtures were created, no live call was made, and no candidate was promoted. Evidence remains metadata-only; no prompts, private conversations, or credentials were stored.

## 2026-11-19 completion-plan P7 separate-project decision

P7 is `NOT_APPLICABLE` to the core evolution completion. An opinion board would create a new durable, multi-author input surface with no identified user need or existing integration point. A separate project would need to resolve these threats before any prototype:

| Threat | Required boundary before design approval |
| --- | --- |
| Forged or replayed submissions | Treat author/model/session labels as claims; bind each proposal to a unique nonce and exact plan revision; use supported host attestation if authorship must be verified. |
| Poisoned instructions | Import submissions as inert proposals; never execute embedded commands or inject text into Worker context automatically. |
| Stale plan revisions | Bind proposal and any patch to the frozen plan SHA and current base; reject mismatches rather than rebase silently. |
| Secret-bearing inputs | Define allowed data classes and redaction before ingestion; do not accept credentials, private conversations, or unrestricted prompts by default. |
| Retention and deletion | Specify storage owner, retention window, deletion, backup expiry, access control and incident handling before durable storage. |
| Attribution | Keep identity and contribution labels unverified unless the native host provides independently checkable evidence. |
| Owner-approved imports | Require an explicit Owner decision on exact files/diff, source/license review, and independent Tester/Reviewer checks before manual application; no automatic repository access or import. |

No repository access, execution, provider credentials, durable storage, or import authority is added. Reopen P7 only under a separate product request with privacy, identity, retention, and import-control decisions.

## 2026-11-19 completion-plan whole-program closeout

- All phases have explicit outcomes: P0 refreshed with license unresolved; P1 offline-qualified/live blocked; P2 capability query unsupported in this environment; P3 local experimental journal v2 complete with host authentication unverified; P4 isolation blocked and serial; P5 offline schema v2 complete; P6 live optimization blocked on Owner inputs; P7 not applicable to the core program.
- Verification on this candidate: `python -B -m unittest discover -s tests -v` — **294 passed, 1 platform skip**; `python -B -m unittest discover -s experiments/agent-efficiency -v` — **3 passed**. Codex release build CRC/source-byte checks and Claude sync/check/build passed; package consistency tests passed. Canonical/Claude runtime copies were checked; neither archive includes the experimental journal.
- Base SHA and branch ancestry remain `5d8eb8686c51c392c0689e04932758ca30a76f2d`; the feature candidate before this closeout record was `906b8f93a441d77d88b9ab8c3a48a0edaa49966c`. Changes are confined to the feature branch. The generated ZIPs are repository consistency artifacts, not a product release; no merge or promotion occurred.
- All work stayed offline: zero live model calls/spend, no provider/host configuration or permission changes, no parallel workers, and no durable user-data journal.

## 2026-11-19 completion-plan P1 live gate

- Compared `PROTOCOL.md`, `RUNBOOK.md`, `protocol.draft.json`, `test_evaluate.py`, and the implementation status. The recorded offline qualification remains unchanged; the evaluator test suite passes 3 tests (exact rerun recorded in this execution's commit history/verification log).
- No approved phase card exists. Missing Owner inputs include the selected host/route, frozen task/oracle hashes, real Tester/Reviewer bindings and commands, telemetry/retention, numeric all-role call/quota/cost/time bounds, enforceable stop control, effect/reliability rules, and explicit authorization.
- Readiness stays `DRAFT_NOT_AUTHORIZED`; no live call or feasibility fixture run was made. Offline evaluator outputs remain descriptive and cannot authorize execution or promotion.
