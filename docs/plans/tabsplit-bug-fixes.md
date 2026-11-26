# Plan: fix the contract bugs found in the tabsplit-1 run

Date: 2026-11-25. Source of the bugs: the tabsplit-1 run record
(`councilflow-runs/tabsplit-1/RUN-RECORD.md`, section "CouncilFlow bugs found",
bugs 1 to 7). The tabsplit app itself is out of scope; this changes CouncilFlow
only.

Owner authorization: the Owner asked for a plan that covers every listed bug and
for it to be executed right after planning. This plan changes the contract helper
scripts (`contracts.py`, `planner_contract.py`), the skill references that
document them, and the generated Claude plugin copy. It does not change the role
order (Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner
→ Owner), role authority, the Reviewer rerun rule, or any frozen Gate 3 record.
Every change is either a relaxation that only admits packets the old rules
wrongly refused, with the same safety property kept by another check, or a new
clear refusal for a case that used to fail later with a confusing error.

Each bug gets a regression test in `tests/test_tabsplit_regressions.py` that
fails on the current `main` and passes after the fix.

## Bug 1: `task_id` means two things

**Observed.** `planner_contract.py assignment` looks up the plan task by the
envelope `task_id` of the Worker `job.assign`. `contracts.py` requires that same
envelope `task_id` to equal the `plan.publish` `task_id` it replies to (the run's
task). Both pass only when the plan has one task whose id equals the run id. A
plan with tasks `T1` and `T2` can never dispatch.

**Change.** Keep the envelope `task_id` as the run's task id (every causal check
depends on it). Add an optional `plan_task_id` field to the `job.assign` payload
that names the Planner task being dispatched.

- `contracts.py validate_message`: `job.assign` payload may carry `plan_task_id`
  (an identity string). Unknown fields are still refused.
- `contracts.py validate_sequence`, with `--root`: when the published plan file
  has a `tasks` array, `plan_task_id` must name one of those tasks.
- `planner_contract.py assignment`: select the plan task by
  `payload.plan_task_id` when present, otherwise by envelope `task_id` (so
  existing single-task runs keep working).
- Docs: `communication.md`, `workflow.md`, `message-contract.json`.

**Test.** A two-task plan (`T1`, `T2`) with run task id `run-1`: a `job.assign`
with envelope `task_id: run-1` and `plan_task_id: T2` passes both
`planner_contract.py assignment` and `contracts.py sequence`. Before the fix one
of the two always refuses it. A `plan_task_id` that is not in the plan is
refused by both.

## Bug 2: `plan_ref` points at a mutable path

**Observed.** The docs say `plan.json`. A revision overwrites it, which breaks the
hash of every earlier saved packet that references it, and `save` then refuses
every later packet with an `artifact_hash` error that does not say why.

**Change.**
- `contracts.py`: a `plan.publish` for a new revision must use a `plan_ref` path
  and artifact id that no earlier revision of that plan used. Refused with code
  `plan_ref_reused` and a message that says to name plan files per revision.
- Docs (`planner.md`, `workflow.md`, `communication.md`): plan files are named
  per revision, `plan-r<revision>.json`, and are never rewritten.

**Test.** Publish rev 1 at `plan-r1.json`, then rev 2 at the same path: refused
with `plan_ref_reused`. Rev 2 at `plan-r2.json`: accepted, and rev 1's file and
saved packets still verify with `--root`.

## Bug 3: no plan revision is possible in one run folder

**Observed.** `save` refuses any second `plan.publish` with a new revision
("amendments need separately approved context; not inferred"), while SKILL.md,
planner.md and communication.md expect the Planner to republish after a rejected
dispatch. The tabsplit run had to split one task across two run folders.

**Change.** Allow a new revision in the same run when it can only change the
Planner's tasks, not anything the Owner owns:
- its `plan_revision` is higher than every earlier revision of that `plan_id`
  (a lower or repeated revision with different content stays refused);
- the same Planner and Manager actors as the first publication;
- the same `objective`, `scope` and `acceptance_ids` as the first publication
  (criteria and scope changes still need separately approved context, which is
  what the old message was protecting);
- a fresh plan file path and artifact id (bug 2);
- the referenced plan still passes `validate_plan_context`, including frozen
  criteria fidelity when it is required.

A revision `plan.publish` may have `in_reply_to: null` or reply to an earlier
message of the same plan with a lower revision. After a newer revision is
published, a new Worker `job.assign` for an older revision is refused with
`plan_superseded`; reports answering assignments already sent still validate, so
nothing in flight is lost.

**Test.** The tabsplit shape (rev 1 publish, rejected dispatch, rev 2 publish
with only the tasks changed) saves into one run folder. Rev 2 that changes
`acceptance_ids`, `scope` or `objective` is refused. A Worker `job.assign` for rev
1 after rev 2 is published is refused.

## Bug 4: `attempt_id` is silently inherited

**Observed.** A `job.assign` that replies to `plan.publish` must reuse the
publish message's `attempt_id` ("unexpected attempt change"). Nothing says so,
and the planning attempt is not the Worker attempt.

**Change.** The first Worker `job.assign` that replies to a `plan.publish` starts
the implementation attempt and may use any `attempt_id`. Every later link keeps
the attempt unchanged as before (Tester and Reviewer assignments, reports,
decisions), and rework still needs a fresh attempt. Docs say this explicitly.

**Test.** The rejected M006 shape (`plan.publish` with `attempt_id: plan-2`,
Worker `job.assign` with `attempt_id: attempt-1` replying to it) passes. A Tester
`job.assign` that changes the attempt from the Worker report is still refused.

## Bug 5: native planning has no frozen-criteria file

**Observed.** `planner_contract.py assignment` requires a frozen-criteria file.
With native planning (the Owner gave no frozen criteria) the Manager copied the
Planner's own criteria into `frozen-criteria.json`, so the check compared the
plan with itself while looking like a fidelity check.

**Change.** `planner_contract.py assignment` takes either the frozen-criteria file
or an explicit `--planner-generated-criteria` flag, never both and never neither.
With the flag, the plan's own acceptance is used for the structural checks and
the output says so: `{"valid":true,"dispatchable":true,"criteria_source":"planner-generated"}`.
With a file the output says `"criteria_source":"frozen"`. Docs tell the Manager
not to fabricate a frozen-criteria file for native planning.

**Test.** The CLI accepts a native plan with the flag and reports
`planner-generated`; refuses when given both, or neither.

## Bug 6: Worker report with empty `evidence_refs` is rejected

**Observed.** A completed Worker `job.report` with `evidence_refs: []` is refused
("completed report requires evidence references") although its payload already
names the hashed `candidate_ref`. Undocumented.

**Change.** For a Worker report, the hashed output `candidate_ref` counts as the
report's evidence, so `evidence_refs` may be empty. Tester and Reviewer reports
still need nonempty `evidence_refs`, and the error now says which role needs
what. Worker self-report still cannot satisfy acceptance (unchanged
independent-evidence checks).

**Test.** A completed Worker report with empty `evidence_refs` passes; a completed
Tester report with empty `evidence_refs` is still refused.

## Bug 7: `contracts.py` writes `__pycache__` into `.agents/`

**Observed.** Running `contracts.py` imports `planner_contract` and `strict_json`,
which writes `scripts/__pycache__/` inside the installed skill, a path roles are
told not to touch.

**Change.** Every skill script that imports a sibling module sets
`sys.dont_write_bytecode = True` before those imports (`contracts.py`,
`planner_contract.py`, `doctor.py`, `route.py`, `efficiency.py`). The documented
commands also use `python3 -B`.

**Test.** Copy the scripts folder to a temp dir, run `contracts.py message` and
`planner_contract.py assignment` as plain CLI calls without `-B` and with
`PYTHONDONTWRITEBYTECODE` unset, and assert no `__pycache__` appears.

## Friction items

Taken on:
- **No "validate plan" mode.** Add `planner_contract.py plan <plan.json>
  (<frozen-criteria.json> | --planner-generated-criteria)` so the Planner can
  self-check a READY plan before publishing. Small, shares the bug 5 code, and
  would have caught the bug 1 mismatch before dispatch.

Deferred, with reasons:
- **Envelope boilerplate / packet builder script.** Useful, but it is a new tool
  and a design question (what it fills in vs. what roles must state). Separate
  change.
- **`acceptance_id` on checks, Tester coverage of every criterion, one command
  per criterion.** Changes the Tester report contract; needs its own plan and
  probably Owner review against the Gate 3 E-criteria.
- **Structured "passed with weak evidence".** Changes what can pass review; that
  is an acceptance-policy decision for the Owner, not a bug fix.
- **Per-criterion evidence refs in `plan.progress`.** Contract change to a
  Manager packet; separate change.
- **Reviewer `job.assign` cannot carry the Worker report hash or Git commit.**
  Contract change; separate change.
- **NEEDS_INFORMATION / BLOCKED Planner answer shape.** communication.md already
  says it is a plain evidence file with no message type; giving it a schema is a
  contract addition for a separate change.

## Files touched

- `.agents/skills/council-flow/scripts/contracts.py`
- `.agents/skills/council-flow/scripts/planner_contract.py`
- `.agents/skills/council-flow/scripts/{doctor,route,efficiency}.py` (bug 7 only)
- `.agents/skills/council-flow/references/{communication,workflow,planner}.md`,
  `message-contract.json`
- `plugins/councilflow/` regenerated with `tools/build_claude_plugin.py build`
- `dist/` rebuilt with `tools/build_release.py` and `build_claude_plugin.py`
- `tests/test_tabsplit_regressions.py` (new)

## Verification

1. Write `tests/test_tabsplit_regressions.py` first and confirm every bug test
   fails on unmodified `main`.
2. Apply the fixes; the new tests pass.
3. Run the full documented suites (`python -m unittest discover -s tests` and the
   others listed in RELEASE.md).

## Open questions

- Bug 3 allows a revision only when objective, scope and acceptance are
  unchanged. If the Owner wants revisions that change scope inside one run, that
  needs an Owner approval link and is not part of this change.
- Bug 6 treats the Worker's hashed candidate as its evidence. If the Owner wants
  every report, Worker included, to cite a separate evidence file, the
  alternative is to keep the rule and only document it.
- Older run folders that already split revisions across folders stay valid; this
  change does not rewrite them.
