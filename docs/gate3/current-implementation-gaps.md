# Current implementation compared with the frozen Owner Charter

**Scope: READ / static comparison only. Gate 3 not run.**

Baseline inspected: `8a7a39695b6dd50273f92f0f5b61f92daee00adb`.
The Owner Charter is authoritative over inconsistent older documentation. The
installed skill and role definitions are deliberately preserved as the candidate
to evaluate; this document records discrepancies without correcting behavior.
Line references below refer to that baseline, not to a new execution trace.

## G01 — Reviewer duty conflicts with the Charter

The [Charter](CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md), lines15 and21–22,
requires independent comparison of **Worker output, Tester output and the
Owner's original frozen plan**. Reviewer submits findings to Manager and is not
a mandatory UX scorer; no extra UX role is introduced.

Current definitions instead make experiential/first-use review the central duty:

- [SKILL.md](../../.agents/skills/council-flow/SKILL.md), lines49–51:
  Reviewer “exercises the result as a user.”
- [roles.md](../../.agents/skills/council-flow/references/roles.md), line15:
  “Fresh separate user-experience review.”
- [workflow.md](../../.agents/skills/council-flow/references/workflow.md),
  lines23–25: Reviewer exercises relevant user interaction.
- [roles.yaml](../../.agents/skills/council-flow/policies/roles.yaml), lines31–34:
  “Independent experiential review,” with ability `experience_review`.
- [council-reviewer.toml](../../.codex/agents/council-reviewer.toml), lines2
  and11–18: first-time-user review, usability/friction/errors, optional rubric.

None of those definitions mandates the three-way comparison or receipt of the
specific Tester report. Candidate/acceptance references and general objective
review do not themselves require it. The optional rubric is **not** a mandatory
score today; the substantive conflict is the Reviewer's primary responsibility.
This is a textual mismatch, not an experimentally observed E-check failure.

## G02 — The E8 independent command comparison is not required

Charter line15 and [Gate 3 E8](CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md),
lines47–48, require Tester to declare deterministic commands, then Reviewer to
independently rerun one and compare **both exit code and SHA-256 of normalized
stdout**. The normalization algorithm must be documented, identical on both
sides and preserve meaningful differences. Both executions and the comparison
must be recorded. `NOT_COMPARABLE` cannot pass E8.

[council-tester.toml](../../.codex/agents/council-tester.toml), lines12–17,
requires independent commands/exits/output references but not deterministic
command designation or this normalization/hash record. The Reviewer instructions
above require actual interaction but no Tester-command selection, rerun or
comparison. [communication.md](../../.agents/skills/council-flow/references/communication.md),
lines25–30 and43–51, defines artifact SHA-256 references and ordinary checks;
those are not a required normalized-stdout comparison. The existing
[message contract](../../.agents/skills/council-flow/references/message-contract.json),
lines133–143, requires Reviewer observations, not the E8 execution pair.
General evidence files could carry such records, but current instructions do
not require them. No schema/code alteration is proposed or made by this import.

## G03 — Agent handoffs exist; the zero-courier acceptance rule is missing

Charter lines6 and16 and Gate 3 E7, lines44–45, require exactly **zero** Owner
courier interventions after the initial submission. Moving agent messages,
files or outputs, or retyping available instructions, counts as courier work.
Genuine permissions/explicit decisions are logged separately as AUTHORIZATION.

Current [workflow.md](../../.agents/skills/council-flow/references/workflow.md),
lines12–33 and49–52, assigns internal handoffs to Manager/agents and keeps internal
formats out of ordinary Owner work. Its lines68–69 say the Owner need not author
internal packets. [SKILL.md](../../.agents/skills/council-flow/SKILL.md),
lines71–74, reserves genuine consequential decisions to Owner. These are
consistent foundations; **no inspected instruction requires Owner relay**.

The gap is the absence of an explicit exactly-zero courier criterion, counting
rule and COURIER-versus-AUTHORIZATION intervention record in the operational
workflow. That absence does not prove any courier intervention occurred, nor
does an autonomous-looking transcript establish E7 without the required record.
The frozen blank template contains the required future recording fields; it is
not filled here.

## G04 — Frozen Owner criteria have partial protection, but no E10 comparison

Charter line11 and Gate 3 setup/E10, lines13 and53–54, require the Owner's exact
criteria saved outside the skill before invocation, reproduced verbatim by
Planner, and directly compared by diff or equivalent byte/line-preserving check.
Separate IDs/traceability may be added; mandatory criteria may not be paraphrased,
omitted, weakened or silently augmented.

[workflow.md](../../.agents/skills/council-flow/references/workflow.md), lines9–11,
and [council-planner.toml](../../.codex/agents/council-planner.toml), lines12–17,
already preserve original acceptance and an external approved plan verbatim.
[communication.md](../../.agents/skills/council-flow/references/communication.md),
lines73–81 and94–101, preserves plan artifacts, hashes and acceptance IDs.
Those protections are useful but do not mandate comparison of Planner's criteria
text to the separately saved **Owner fixture**. Native mode still defines
observable acceptance ([SKILL.md](../../.agents/skills/council-flow/SKILL.md),
lines27–33); it does not explicitly distinguish organizing frozen criteria from
adding mandatory requirements. No actual criteria drift is asserted from this
inspection. The example fixture remains illustrative and unfrozen.

## G05 — Final Owner communication is narrower than the Charter's route

The Charter's fixed route ends Manager → Planner → Owner, and only Planner or
Manager may give routine plain-English output (lines6 and9).
[SKILL.md](../../.agents/skills/council-flow/SKILL.md), lines12 and58–61, instead
reserves routine output to Manager and has Manager give the final Owner report.
[council-planner.toml](../../.codex/agents/council-planner.toml), lines9–11,
explicitly directs Planner results to Manager, not routine Owner updates.

This is a final-handoff/leadership distinction from the Charter. Manager-only
plain-English output is still within E9's allowed sender set, so it is **not by
itself an E9 failure**. Raw internal packets remain inappropriate as required
Owner work. No new communication route is implemented here.

## Existing foundations and evidence limits

The fixed nine-step role order is already in workflow.md lines3–4 and roles.yaml
line36. Manager does not code; Worker implements; Tester independently checks;
Reviewer is separate. Structured communication and native-permission limits
are explicit. External Planner mode preserves supplied provenance without
claiming external Council automation. These are inspected instruction features,
not host-observed Gate 3 behavior.

| Gate check | Current material and remaining evidence requirement |
|---|---|
| E1 | Literal invocation/discovery instructions exist. No native invocation is attempted here; earlier discovery/authentication reports are not this experiment. |
| E2 | SKILL instructs delegation. Whether activation itself triggers delegation without an extra spawn instruction requires fresh host evidence. |
| E3 | Instructions call for real native agents. This documentation audit, including its read-only helper review, is not an experiment spawn observation. |
| E4 | Four native TOMLs exist. Parsing, role labels and fallback documentation do not establish effective thread settings or prove prompt-only roles; invisible settings remain unverified. |
| E5 | Tester is instructed to execute independently. Gate evidence must locate commands in its own actual Tester thread. |
| E6 | Separate role contexts are specified. Worker/Tester/Reviewer thread distinction requires host evidence from the authorized run. |
| E7 | Existing internal handoffs are compatible; exact zero-courier counting and authorization separation are the G03 gap. |
| E8 | Three-way comparator and deterministic rerun/comparison are the G01/G02 gaps; recorded executions are required. |
| E9 | Manager-only ordinary prose meets the sender restriction in principle; actual Owner interaction still needs observation. See G05 for the final-route distinction. |
| E10 | Original-plan protection exists, but the saved-Owner-fixture/verbatim comparison is the G04 gap. |

This crosswalk assigns **no Gate 3 outcomes**. All ten rows in the untouched
experiment template remain UNVERIFIED; no run-level outcome is populated.
For a later authorized run, the frozen document alone controls evidence classes,
non-PASS primary classes, `NOT_COMPARABLE`, the E3 stop rule and run outcomes.

Older normal-operation instructions authorize in-scope engineering repairs and
continuation of independent work when a capability is unavailable (recovery.md,
lines6–17 and28–31). Gate 3 is an observation-only exception: no skill/config/policy
corrections, post-invocation spawn prompts or automatic planted-bug follow-up;
stop when E3 does not establish distinct spawning. This import does not exercise
that rule, authorize a run or change ordinary implementation behavior.

Archive hash checks and unchanged-file checks validate this documentation import
only. No Codex activation/authentication attempt, application/test command,
fixture task, controlled baseline, efficiency measurement or Gate 3 experiment
was run. Historical release claims remain historical; they are not E1–E10
evidence for a new run. No implementation correction is included in this commit.
