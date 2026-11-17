# Audit findings register and decision rules

**Baseline:** `3bf08cde1ae012d3bf6ef483015ca087bd8f420b`. Independent reviewers: Grok 4.5, DeepSeek-V3.2 and GLM-5.3-Flash. Findings below are consolidated by topic (reviewer IDs overlap). **Observed in source** is distinct from **externally reported reproduction**. These records are planning triage, not completed tests or authorization to fix every item.

| ID | Claim | Confidence at planning | Target |
| --- | --- | --- | --- |
| AR-01 | Claude plugin Tester/Reviewer instructions contain evidence fields absent from closed validator schema | Source mismatch verified; GLM's synthetic rejection not independently repeated | 01 |
| AR-02 | Plugin package test invokes builder writing real `dist/` | Source invocation verified; GLM reported dirty worktree | 01 |
| AR-03 | Committed Claude ZIP does not byte-match clean builder output (entry ordering suspected) | GLM reported pristine rebuild; independent reproduction required | 01 |
| AR-04 | `AGENTS.md` and `CLAUDE.md` inaccurately describe Claude Code as only a possible future feature | Confirmed source/document contradiction | 02 |
| AR-05 | Release CI lacks push-to-`main` trigger and omits some documented coverage | Confirmed from workflow; assess meaningful OS matrix separately | 02 |
| AR-06 | Published live-run summaries refer to supporting logs outside repository | Confirmed source references; ability to publish sanitized proof unknown | 03 |
| AR-07 | No checked-in license; plugin manifest says UNLICENSED | Confirmed repository tree; license choice reserved to Owner | 02 |
| AR-08 | Reviewer rerun evidence may be copied without proving execution | GLM adversarial claim; still requires independent validation and host-provenance analysis | 03 |
| AR-09 | Claude report-file persistence wording could be read as Manager authoring reports | Confirmed wording ambiguity; evaluate before changing roles | 02 |
| AR-10 | CouncilFlow overhead and relative benefit have no controlled baseline | Unmeasured research question, not a demonstrated defect | 04 |
| AR-11 | Codex native discovery/activation/TOML settings remain incompletely observed | Explicitly disclosed current host-evidence gap | 03 |
| AR-12 | Historical Gate 3 gap document includes findings from an older baseline | Already labeled with old SHA; optional clear status banner only | 02 |

## Not accepted as immediate defects

- Role separation and transport are **host-native, instruction-governed** by design. The skill does not promise OS isolation or cryptographic sender authentication. Treat these as disclosed limitations unless an actual claim exceeds evidence.
- The existing `tests/test_workflow_recovery.py` means the statement "no recovery tests" is false; full live interruption coverage remains a separate question.
- The existing current Reviewer instructions mandate comparison and a deterministic rerun, so the old Gate 3 Reviewer-as-UX claim is not a current defect.
- Offline-only, opt-in efficiency helpers are intentionally not production-certified.
- Synthetic hashes, invocation claims or matching command output **do not prove** separate native sessions.

## Decision rules

1. For every proposed fix, distinguish **confirmed defect**, **risk**, **design tradeoff**, and **false positive**.
2. Prioritize the smallest change that meets approved requirements; regression-test negative cases.
3. When changing schema vs. agent instructions, preserve source fidelity and frozen-criteria / Tester / Reviewer protections. Never loosen validation just to make a smoke example pass.
4. New runtime, hook, mandatory transport interception, trust model, role authority or new acceptance requirement requires a separate Owner-approved design decision.
5. No proof-free status promotion. No forced numerical completion percentages. "Unverified" remains valid.
6. License selection, paid tests, publishing sensitive logs, and merges/releases are explicit Owner decisions.

## Provenance of the plan

This register summarizes reviewer reports provided in chat and source checks against the pinned repository snapshot. It does **not** imply the full original audit texts, GLM's temporary reproducer, local Windows backup, or private host logs were imported. Record fresh reproduction and artifact hashes in the applicable slice instead of treating a reviewer quote as a passing regression test.
