# Multi-agent evolution branch status

**Branch:** `evolution/multi-agent-plan-2026-11-17`
**Base:** `5d8eb8686c51c392c0689e04932758ca30a76f2d`
**Scope:** Offline implementation and repository verification only. No live model requests, provider changes, host configuration edits, OS permission changes, merge, or publication.

| Plan phase | Status | Result |
| --- | --- | --- |
| P0 baseline | `PARTIAL_READ_ONLY` | Baseline inventory at `reports/multi-agent-evolution-baseline-2026-11-18.md`; remote `main` matched the branch base. Open PRs/other remote branches were not inventoried, the project license remains unresolved, and independent reconstruction of every inventory item is pending. |
| P1 Agent Efficiency | `OFFLINE_QUALIFICATION_COMPLETE; LIVE_BLOCKED` | Existing efficiency component suite: 76 run, 75 pass, 1 platform skip. Package D: 3 run, 3 pass. Synthetic evaluator returned `CLOSED_NO_BENEFIT` and `NOT_APPROVED; offline analysis only`. No trial or model call was run. |
| P2 capability-aware routing | `PARTIAL_OFFLINE` | Added versioned role preference validation and caller-reported capability metadata. Caller claims remain `UNKNOWN`; no host adapter or selector was enabled; effective model remains null and selection inherits host. Native capability is unverified. |
| P3 local journal prototype | `EXPERIMENTAL_PROTOTYPE` | SQLite journal under `experiments/multi-agent-evolution/` (outside installable runtime due existing dependency guard). It implements schema versioning, state transitions, transaction/CAS revision checks, duplicate event rejection, payload allowlisting and required acceptance-reference fields. It does not verify reference targets, attempt identity, evidence bytes or artifact hashes, authenticate approvals/native sessions, or provide demonstrated cross-platform crash recovery. |
| P4 DAG/isolation | `PARTIAL_OFFLINE; ISOLATION_BLOCKED` | Added pure dependency validation for cycles, missing prerequisites, stale plan revision and blocked descendants. It does not schedule tasks or enable parallel writes; OS isolation has not been tested. |
| P5 experience/doctor/observability | `PARTIAL_OFFLINE` | Added a scoped experience-entry validator for caller-claimed review metadata; returned entries remain `UNVERIFIED`. The doctor validates its schema, checks referenced bytes against declared digests, and labels native-host claims `UNVERIFIED`. No automatic Worker memory injection or dashboard exists. |
| P6 workflow optimization | `OFFLINE_FIXTURE_ONLY; LIVE_BLOCKED` | Existing synthetic evaluator was exercised and found no benefit under its fixture. No benchmark corpus, candidate promotion or live optimization was performed. |
| P7 opinion board | `DEFERRED` | No service was added. It remains an optional separate project requiring its own privacy, identity and storage design. |

## Verification

- `python -B -m unittest discover -s tests -v`: **262 tests passed, 1 platform skip** before the 2026-11-19 review follow-up; see the follow-up plan for final rerun evidence.
- `python -B -m unittest discover -s experiments/agent-efficiency -v`: **3 passed**.
- `python -B tools/build_release.py`: package built with source-byte and CRC checks passing.
- `python -B tools/build_claude_plugin.py sync`, `check`, and `build`: shared runtime synchronized; package built.
- Synthetic evaluator ran offline only and explicitly returned `NOT_APPROVED; offline analysis only`.

## Limits

The product helpers are deterministic local code, not a trusted supervisor or authentication layer. The journal prototype is not included in product bundles. Capability/profile data is caller-supplied; it cannot prove actual host route or model identity. The journal does not inspect evidence references or establish attempt identity, artifact hashes, authenticated approvals, native sessions, or cross-platform crash recovery. The DAG helper does not enforce workspace separation. No evidence here establishes live Codex or Claude activation, model cost, quota, billing, or workflow improvement.

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
