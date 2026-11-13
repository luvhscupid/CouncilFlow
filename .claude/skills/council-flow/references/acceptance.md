# Evidence and acceptance

Define acceptance before implementation. Use stable IDs and observable outputs.
Maintain the unchanged contract and map each criterion to PASS, FAIL, BLOCKED, or
UNVERIFIED, with evidence paths. A command needs its actual invocation, exit
status, and output or concise observed result. A file inspection is static
evidence. A model claim without supporting observation is not proof.

## Validation scenarios

| ID | Scenario | Evidence needed |
| --- | --- | --- |
| V01 | Skill metadata | Static parse of required name and description in actual SKILL.md |
| V02 | Discovery | Claude Code host identifies installed skill in approved discovery location |
| V03 | Explicit invocation | Host activates literal `/council-flow`; path placement or copied prompt alone is insufficient |
| V04 | Manager boundary | Delegation/edit attribution shows Manager coordinated without application-code edits |
| V05 | Worker implementation | Real native Worker identity and changed application files |
| V06 | Independent testing | Distinct real Tester identity, contract, actual tests and findings |
| V07 | Failure handling | Mandatory failure explicitly rejected and repaired or blocked |
| V08 | Fresh Worker rework | Needed repair assigned to a fresh Worker identity |
| V09 | Reviewer independence | Distinct real Reviewer compares frozen criteria, Worker candidate and Tester evidence, then reruns one declared deterministic command |
| V10 | Scope protection | Bounded adversarial request refused/escalated without unauthorized changes |
| V11 | Requirements preserved | Attempted weakening rejected; original mandatory criteria retained |
| V12 | User completion | Final report says what works, what was tested, and remaining gaps |
| V13 | No artificial roles | Actual distinct role sessions counted; no invented five-agent claim |
| V14 | No old-project dependency | Dependency inspection and actual standalone execution; no imported predecessor code |

Static validation may establish format and instruction coverage only. It cannot
pass V02–V13 live behavior. Record static and runtime results separately. Missing
host tools, interaction, or observations are UNVERIFIED, never an implied pass.
An adversarial prompt should be bounded: ask the agent to state its decision on
an out-of-scope request, not actually touch a forbidden file to test protection.

## Final disposition

The Manager requires independent Tester results, Reviewer comparator findings
and an independent rerun, plus the Planner's final acceptance map. Mandatory
failures prevent verified completion.
No score or majority vote can waive a mandatory criterion or Owner authority.
The skill supplies a workflow, not a guarantee of the underlying model's actions.

For this project's full demonstration, COMPLETE requires actual discovery and
invocation, distinct native roles, working tested application, truthful failure
handling, installable package, instructions, and all required evidence. If any
mandatory capability is unverified, use `PARTIAL — <precise missing capability>`.

Keep the Owner report concise: product/skill/ZIP paths; discovery, invocation and
delegation status; implemented behavior and actual test totals; Tester and
Reviewer findings; repairs; passed/failed/unverified acceptance; exact next-task
invocation. Put verbose logs in reports, not the main report. Do not invent token
costs, usage, session IDs, or execution results.

## Restored communication acceptance

The Owner's explicit contract restoration distinguishes task JSON, role/workflow
YAML, Claude Code Markdown, optional JSONL and concise Owner prose. Use communication.md,
policies/roles.yaml and scripts/contracts.py at actual controlled boundaries.
C01–C12 tests cover real invalid mutations, not merely reading valid examples.
Five-role examples are synthetic unless tied to actual native assignments/results.

Reports must identify task, original plan/revision, attempt, candidate/hash,
causal assignment and actual test/review evidence. A Manager accept decision
requires distinct passing Tester and Reviewer records; Worker assertion is
insufficient. Planner checks original mandatory acceptance, never a Worker-edited
checklist. Context-free validation proves only structure. Optional root checking
proves actual referenced file bytes at that check, not evidence semantics.

The current Owner-directed final classifications supersede the prior build's
generic PARTIAL wording for this restoration: CONTRACT_RESTORED —
NATIVE_ACTIVATION_UNVERIFIED when corrected contract work passes but genuine
activation remains blocked; COUNCILFLOW_FULLY_VERIFIED only for actual native
invocation plus required separate roles. Otherwise PARTIAL or FAILED with the
precise remaining failure. Do not rewrite historical reports as new proof.
