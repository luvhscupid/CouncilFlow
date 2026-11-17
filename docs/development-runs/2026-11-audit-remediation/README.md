# CouncilFlow audit remediation | run index

**Status:** DOCS-ONLY PLAN; implementation not started in this branch.  
**Snapshot:** `3bf08cde1ae012d3bf6ef483015ca087bd8f420b` (2026-11-16).  
**Owner:** Human CouncilFlow Owner; all consequential scope, release and merge decisions require Owner authorization.  
**Source:** Independent reports by Grok 4.5, DeepSeek-V3.2, and GLM-5.3-Flash supplied in conversation 2026-11-17; reports themselves are not reproduced or independently archived here.

This is a **non-normative development roadmap**, not a change to the skill, approved Owner Charter, frozen specifications, gate criteria, permissions, or release claims. If it disagrees with controlling material, **the Owner Charter and frozen approved specification win**. Existing historical reports remain immutable. The objective is to make successive coding runs reproducible, reviewable, and easy to resume without relying on chat memory.

## Where to start

1. Read [findings register](00-findings-and-decisions.md), then the appropriate slice below.
2. Read the controlling [Owner Charter](../../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md), the installed [SKILL.md](../../../.agents/skills/council-flow/SKILL.md), and [RELEASE.md](../../../RELEASE.md) before implementation.
3. Before a run: check Git SHA, branch, dirty files, and installed host capabilities. Work in a dedicated task branch. Do **not** assume this planning branch contains any implementation.
4. After a run: update only the slice's evidence/status and this index, with actual test commands, results, remaining risks, commit SHA, and Owner decision. Do not change a status based on an agent assertion alone.

## Sequential slices

| Slice | File | Status | Prerequisite | Exit gate |
| --- | --- | --- | --- | --- |
| 01 | [Claude contract + package reproducibility](01-contract-and-release.md) | ENGINEERING ACCEPTED BY OWNER; NATIVE WORKFLOW UNVERIFIED | Owner review | Engineering gates pass; native Planner/Tester/Reviewer session provenance unverified |
| 02 | [Documentation, CI and distribution hygiene](02-docs-ci-and-distribution.md) | PROPOSED; NOT AUTHORIZED | Owner review of Slice 01 | Accurate host docs, main-triggered CI, package checks, explicit license decision |
| 03 | [Native-host verification and evidence](03-native-host-verification.md) | PROPOSED; NOT AUTHORIZED | Stable release from Slices 01-02; host access | Genuine session evidence and honest E1/E2/E4 outcomes, shareable sanitized proof |
| 04 | [Value measurement and next design decision](04-value-and-roadmap.md) | PROPOSED; NOT AUTHORIZED | Representative functional host runs; Owner-approved study | Reproducible comparison and explicit keep/change/defer decisions |

**Slices are proposed work packages, not standing authorization.** Do not automatically chain to the next slice. In particular, do not implement a new mandatory transport interceptor or standalone runtime solely because a reviewer suggested one.

## Stable handoff record

When resuming in Codex, Claude Code, or another session, capture these fields in the current slice under `## Run record`:

- Starting Git SHA, working branch, active skill snapshot, host/version and model/route if actually observed
- Authorized scope, changed files, commands and results with independent supporting references
- PASS / FAIL / BLOCKED / UNVERIFIED for each acceptance criterion; do not equate static tests with native delegation proof
- Remaining defects, possible regressions, risks, next action, Owner approval/decision
- Whether code was committed and whether any push/PR/merge occurred (default **no**)

A run must leave the project safely resumable even if interrupted. No fabricated Tester/Reviewer agents, backdated messages, or invented evidence. Explicitly report inability to activate native agents and perform only work permitted by the Owner and host.

## Non-goals

No broad architectural rewrite, new provider integration, paid experiment, efficiency-helper activation, historical archive rewrite, unapproved release, or claim of guaranteed agent independence. This plan is not proof of completed work.
