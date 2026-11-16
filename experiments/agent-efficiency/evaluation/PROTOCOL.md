# Phase 5 paired evaluation draft

**DRAFT_NOT_AUTHORIZED — protocol preparation only.** No trials, quota use,
approval or execution freeze is implied. Toolkit baseline:
`f24d81f87bba3358456a4043b6788fafd4512ecb`. Machine-readable decisions are in
[protocol.draft.json](protocol.draft.json); procedures are in [RUNBOOK.md](RUNBOOK.md).
Historical research remains non-normative. This is one A/B comparison, separate
from the universal model selector and its three-strategy research.

## Comparison and smallest proposed pilot

Use **one Owner-selected host/route/workflow**, initially Codex CLI if its live
access gate can be met. Do not pool Codex and Claude/xKiro results or switch
providers/models during a block. A Claude block needs separate authorization
and its own live compatibility/metering evidence. Neither is live-verified now.

- **A, baseline:** Existing coding workflow, with native tool-output handling.
  No optional digest/expand instructions. Out-of-band recording is identical
  in both arms and is never fed to the coding agent.
- **B, treatment:** Same goal, host, permissions, role responsibilities, tests
  and budget. The agent is explicitly instructed to run only the declared
  task-owned test command through Package B and use its digest/expand interface.
  Full permitted test output remains available. Expansion on incomplete or
  uncertain diagnostics is required. No transparent interception, hooks, model
  selector, cache-policy change or live CouncilFlow integration is introduced.
- This estimates the practical **wrapper plus instruction** effect, including
  expansion overhead. Adapters/recorders measure; they do not optimize on their
  own. Native output may already be truncated in A; document that behavior.
- Proposed feasibility pilot: **6 concrete tasks × 2 independent repetitions =
  12 pairs / 24 arm runs**, fresh sessions and task copies for each arm. At most
  two coding attempts per arm: 48 coding attempts total, plus separately bounded
  verification calls. These counts are proposals, not spending authorization
  or a power calculation. No automatic follow-on experiment.

## Proposed task manifest

Use benign offline Python-standard-library fixtures, outside this workspace.
No production files, credentials or network-dependent tests. These are exact
task specifications for approval, **not implemented/qualified fixtures**.

| ID | Representative work | Mandatory independent oracle |
| --- | --- | --- |
| T01 | Repair decimal receipt rounding | `0.10 × 3 + 0.20` gives exactly `0.50`; reject negative/nonfinite inputs; preserve CLI errors |
| T02 | Repair CSV aggregation | Quoted names, reordered columns and decimal totals work; missing required column fails clearly |
| T03 | Add bounded JSONL validation | Valid UTF-8 records pass; malformed line gets its 1-based index and nonzero exit; no traceback on expected input errors |
| T04 | Add an offline date-range filter | Inclusive bounds, leap-day cases and invalid dates match the frozen examples |
| T05 | Refactor a small grouping utility | Exact output preserved for empty/repeated/Unicode keys; no added dependencies or network access |
| T06 | Repair diagnostic interpretation | Seeded failing test has root cause in the middle of a long deterministic log; correct code repair, not test suppression |

Before freezing, the independent oracle custodian must supply each starting
tree, tests, expected bytes, exact command and SHA-256 manifest. Check each oracle
against a valid control and its seeded defect using local deterministic tests.
Keep hidden tests outside agent-writable trees. T06 is a declared blind-spot
stratum; also retain ordinary short successful logs to avoid failure-only tuning.
No fixture creation, seeded coding run or task qualification is performed here.

## Ordering and environment controls

Each repetition uses the same starting tree/hash in A and B. Proposed order:
repetition 1, odd task IDs AB and even IDs BA; repetition 2 reverses each order.
This counterbalances order but is not randomized sampling. Freeze task order,
prompt bytes and the one permitted arm-specific instruction before running.
Use separate fresh copies without reset/clean/overwrite. Never show one arm's
solution to the other. Do not change tooling after seeing outcomes.

Record OS, Python/CLI/toolkit versions, workspace/prompt/oracle hashes, safe
configured and reported model/route labels, permission profile, thread reuse,
start/end times and cache condition. Use fresh sessions, no resume and no parallel
provider activity in the block where controllable. Do not flush caches or change
credentials. Shared provider caches/quotas remain possible confounders; record
order/time gaps and do not claim cache-state equivalence or causal cache savings.

## Independent acceptance and measurement

Owner must bind real Tester and Reviewer identities and their commands. They
must be independent of the coding Worker and receive the same complete candidate
and full test evidence in both arms. Reviewer checks Worker output, Tester
evidence and the original frozen task criteria, including an independent rerun
of one Tester-declared deterministic command with exit and CRLF-to-LF-only stdout
SHA-256 comparison. No self-approved acceptance. Preserve existing authority;
this protocol does not install or redesign CouncilFlow roles.

Run trusted tests on a detached candidate copy, bind candidate/oracle hashes,
and collect evidence before acceptance. Agents cannot alter the oracle. Failed,
timed-out, abandoned and repaired attempts stay in the denominator; do not drop
an unsuccessful arm or rerun only treatment until it wins. Equal retry limits
apply to A/B. Stop a censored arm at its cap and record failure/censoring.

| Measure | Collection and present limitation |
| --- | --- |
| Accepted tasks / failed attempts | External Tester/Reviewer evidence per arm and attempt, not parser `complete` or agent confidence; not automatic today |
| Model turns / retries | Authoritative host/role counters with scope, if exposed; do not equate Codex `completed_turns` with internal API/model calls. Absent totals are UNKNOWN |
| Input/output/cache counters | Adapters preserve reported scopes. Record every coding/verification call once; do not add incremental, message and cumulative snapshots. Missing or unscoped totals are UNKNOWN |
| Subscription quota | Only attributable, compatible provider records with units/time window and concurrent activity noted. Balance snapshots alone cannot attribute a run; currently UNKNOWN |
| Wall time | Monotonic first-start to final independent disposition, including failures, waits, expansion and verification; record active/operator time separately |
| Tester/Reviewer outcomes | Identity, criterion IDs, exact command/executable, candidate/oracle hashes, exit, normalized output digest and evidence reference |
| Diagnostic blind spots | Independent full-log reader labels seeded failure, what digest exposed, whether/when expanded, eventual detection, repair and extra turns. Record both excerpt misses and unrecovered failures |
| Owner interventions | Operator ledger: count, reason, elapsed time, arm and attempt. Record unknown separately from observed zero |
| Cost per accepted task | Sum reliable costs of **all** coding, failure, retry and verification attempts / accepted tasks per arm. Zero accepted tasks means undefined, not zero. No complete reliable costs means UNKNOWN |

Use [the sidecar template](protocol.draft.json) alongside unmodified RunRecords;
`task_id` and independent evidence do not belong inside the existing RunRecord
schema. Keep permitted evidence private under ignored `.local-runs/` or an
Owner-approved external directory. Do not store private conversations/reasoning.
Adapter expansion returns sanitized metadata; only Package B captures complete
explicitly permitted **test-command** streams. Hashes prove bytes, not approval.

## Proposed thresholds, budgets and uncertainty

All entries require Owner decisions. Proposed minimum worthwhile effect:
**15% lower total wall time per accepted task**, counting every attempt and
verification cost in time, with no observed acceptance degradation or unrecovered
digest-induced diagnostic miss. Economic effect is secondary and only measurable
with reliable complete costs; tokens alone cannot satisfy the primary outcome.

Proposed safety/non-inferiority requirements: zero unauthorized actions, secret
exposures or oracle changes; zero extra accepted-invalid candidates; treatment
acceptance no worse than baseline on paired tasks; no additional Owner
interventions attributable to missing diagnostics. An observed zero is not proof
of a zero population risk. Population reliability/security margins and required
confidence coverage remain **undecided**, not silently set by this draft.

Proposed hard operational bounds: 12 pairs, 24 arm runs, 48 coding attempts,
10 minutes per arm and 240 minutes for the entire pilot including verification.
Maximum **all-role model calls, quota units, monetary exposure and stop mechanism
are null/unapproved**. Operator must stop at the first approved bound; current
scripts cannot enforce a provider spending ceiling. An estimated CLI cost cap,
subscription label or account balance does not establish a hard limit.

Analyze all pairs, acceptance discordances, failures and missingness by task and
order. Report within-task repeats and task-level effects, not 12 independent task
families. Include effect ranges and per-task values. Six purposively selected
tasks are inadequate evidence of general benefit or reliability non-inferiority.
No post-hoc sample-size expansion, threshold tuning or metric switching. This
pilot estimates feasibility/variation only; a confirmatory sample-size/uncertainty
method needs new explicit approval based on the desired effect and precision.

The existing `evaluate.py` is a fixture-oriented descriptive helper, not the
decision authority: its accepted-cost mean omits failed-attempt cost, its normal
intervals ignore task clustering, and it lacks the full sidecar/approval gate.
Do not promote its `provisional_outcome` or accepted-cost fraction into CPAT,
non-inferiority proof or execution authorization. No evaluator code is changed.

## Stops, classifications and readiness

Pause before another call on permission/security breaches, oracle mutation,
unrecoverable digest miss, unknown/unapproved spend exposure, route drift,
unattributable primary outcomes or a reached budget/time/call bound. Keep the
evidence; no automatic fallback, retry-budget enlargement or new provider.

- `CLOSED_NO_BENEFIT`: predeclared observed quality/security/diagnostic constraint
  breach. Preserve a separate operational STOP reason; unsafe runs stay stopped.
- `INCONCLUSIVE`: bound exhausted, missing essential data, insufficient precision
  or feasibility pilot finished without a constraint breach. Even a 15% observed
  improvement does not upgrade this pilot to general benefit evidence.
- `BENEFIT_OBSERVED`: reserved for a separately approved adequately supported
  confirmatory protocol meeting its effect and non-inferiority decision rule.
  **Unavailable as a promotion outcome from this pilot.**

Current readiness blockers: both live adapters unverified; spending/quota bounds
unestablished; task fixtures/oracles not yet sealed; independent verifier bindings
and all-role metering unavailable; native wrapper adherence/expansion telemetry
not observed; analysis and reliability thresholds unapproved. Practical fallback:
offline fixture/pipeline validation only, or separately authorized measurement of
time/acceptance with monetary conclusions explicitly unavailable. Do not call a
missing quota metric zero. Reopening after stopping needs new Owner authority.

**Not currently worthwhile to launch live evaluation.** Resolve access/exposure
and treatment-delivery evidence first. Owner must choose task/oracle set, host
workflow and independent verifiers, order, permissible telemetry/retention,
minimum effect, reliability margins/confidence rule, all-role call/time/quota/cost
bounds and stop mechanism. Only after actual approval may a separate execution
version be finalized, SHA-256-bound to that approval and recorded before any
controlled call. This draft remains unfrozen and DRAFT_NOT_AUTHORIZED.
