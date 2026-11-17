# 04 — Verification, experiments, and resource accounting

**Status:** proposed evaluation framework, NOT an authorization to run trials or use quota. The existing [Agent Efficiency Package D protocol](../../experiments/agent-efficiency/evaluation/PROTOCOL.md) is still `DRAFT_NOT_AUTHORIZED`; this document must not silently override its exact arm definitions or sample counts.

## Core measurement principle

Optimize **useful verified outcome per scarce resource**, not minimum output tokens at any cost. A shorter Worker trace that causes repeated failures or lost evidence is worse. Compare against *real accepted work*, with independent Tester/Reviewer outcomes and original acceptance held constant.

## Acceptance classes

- **S0: Source fidelity:** original input and approved criteria byte/hash identity preserved. Any missing/stale/substituted original fails closed.
- **S1: Native execution:** host logs/session metadata prove actual role invocation and candidate provenance. Instructions or mocks alone do not prove native agents ran.
- **S2: Independent correctness:** Worker output is tested by a fresh separate Tester; deterministic command and full evidence stored; meaningful negative tests are included.
- **S3: Independent review:** Reviewer receives original plan, candidate and *actual* Tester report and reruns a declared command with matching exit and normalized stdout hash, or reports an explicit discrepancy.
- **S4: Governance:** Manager and Planner act within frozen role responsibilities; consequential operations require real Owner permission.
- **S5: Reliability:** repeated requests and failure injection do not create false passing transitions, leak writes across isolated workers or corrupt previous evidence.
- **S6: Efficiency:** observed per-role usage and timeline are accurately attributed and treatment gains do not regress S0-S5.

**S0-S5 are hard gates.** S6 is an optimization objective, not an excuse for a weaker gate.

## Baseline fixtures and comparison method

Start with small, benign offline tasks; do not run tests on main or untrusted workspace with privileged permissions. Reuse existing `demo/` fixtures and existing Package D tasks *only with permission and compatible independence*. Candidates: decimal receipt correction; robust CSV summary; bounded JSONL validation; date-filter edge cases; no-behavior-change refactor; long failing diagnostic log. Every task needs a sealed initial tree, prompt bytes, independent acceptance IDs/oracle, permitted command(s), candidate/output manifest and checksum.

For any A/B block:
1. Choose **one** variable at a time, e.g. digest instruction versus native host output; or explicit Worker model versus inherited model. Never mix router+memory+scheduler changes into one "improvement" score.
2. Keep host, observed route/model when controlled, task inputs, permissions, independent oracles, effort, retry/resource caps, candidate isolation and Tester/Reviewer protocol equivalent.
3. Predeclare task order and counterbalance arm order where possible. Use fresh workspaces, no solution leakage between arms; retain all failed, timed-out and censored runs.
4. Decide *before* the trial how to handle flaky tests, missing metering, provider rate limits, cache interference, native feature absence and unaffordable runs.
5. Report per-task paired differences and the range, not only averages. A pilot can find integration errors but may be too small for a general model superiority claim.
6. Do not mix measured token counts with estimated billing or infer per-run quota from account-level changes. The existing Package D protocol proposes six tasks x two repetitions, 12 pairs / 24 arms, subject to separate approval and budget; it is not a universal requirement for every later experiment.
7. If an arm fails to execute, retain it in the denominator as failed/censored where appropriate; never erase an attempt to improve the result.

## Metrics and provenance

| Measure | Source requirement | Null/unknown handling |
| --- | --- | --- |
| Mandatory criteria met | Independent external oracle, test results, Reviewer check | `UNVERIFIED` if oracle/evidence missing |
| False accept or false reject | Known seeded valid/invalid controls; recorded decisions | Never substitute model confidence |
| Worker rework count | Correlated run+attempt journal, exact candidate IDs | Missing lineage -> `UNKNOWN` |
| End-to-end wall time | Real monotonic timing around defined workflow boundary | Unknown if incomplete clocks/timestamps |
| Input/output/cache token totals | Host or provider usage events, each scope once | Unknown if snapshots cannot be de-duplicated |
| Context relevance | Measured applicable context refs vs distractors; independent outcome | Qualitative notes separate from quantities |
| Cost and subscription quota | Compatible provider/billing records with units and attribution | Unknown, not zero and not guessed from pricing |
| Calls / failures / retries | Host runtime events, not self-report | Distinguish model turn from API call |
| Cache effectiveness | Provider-observed cached input against eligible total | Null if host doesn't expose consistent semantics |
| Integrity of evidence | SHA-256 for source, candidate, artifacts, command outputs | Mismatch -> fail closed |
| Native role independence | Real host session/instance/provenance binding | `NATIVE_ACTIVATION_UNVERIFIED` if not observed |
| User interruptions | Count `COURIER` separately from real `AUTHORIZATION` | Unknown if no intervention log |

### Token accounting rules

Don't add cumulative per-model snapshots to per-message deltas, or assume any model ID reported by a gateway is the actual upstream. Track upstream model, configured route and host-reported identity as separate fields. Cache creation and cache reads remain separate. Client-estimated dollar figures are explicitly estimates. For a task where cheaper models raise failure/retry costs, compare **total** workflow resources through Planner final check, including independent verification, not just Worker prompt tokens.

## Mandatory negative controls by feature

| Feature | Positive control | Required negative control |
| --- | --- | --- |
| Model router | Supported host selects role model, confirms observed identity | Unsupported override, wrong protocol, wrong account/credential, silently inherited model |
| Journal | Replays valid accepted work and pending work exactly as specified | Duplicate completion, stale attempt, power-loss transaction, missing Owner approval, corrupt record |
| Task DAG | Correct dependency scheduling and stable output | Cycle, missing parent, failed prerequisite, simultaneous conflicting claims |
| Workspace isolation | Worker edits only assigned workspace | Junction/symlink escape, shared path, parallel conflicting edit, unauthorized promotion |
| Context digest | Full original output expands and matches hash | Truncated/malformed/bad hash, failing test in omitted middle, timeout, descendant pipe |
| Experience memory | Relevant approved lesson retrieved with source | Cross-project poison, outdated decision, security policy override, missing provenance |
| Reviewer | Exact command rerun and expected normalized stdout hash | Altered stdout, changed exit, reused Worker output, changed candidate, fake Tester report |
| Doctor/dashboard | Missing evidence appears BLOCKED/UNVERIFIED | Empty test discovery, stale UI projection, mock role claimed native |
| Multi-model room | Attributed independent opinions on same issue | Forged identity, malicious embedded command, stale plan revision, unapproved plan publication |

Use synthetic tests to prove the check can fail, plus at least one authorized native observation for real-host claims. Static/pure tests do not establish host enforcement.

## Windows and platform validation

CouncilFlow is used on Windows as well as possibly cloud environments. Every portable feature needs Python 3.11+ checks, PowerShell 5.1-safe commands where user-facing, Windows path/junction/reparse-point concerns, distinct Git index/worktree tests, line-ending/Unicode/UTF-8 handling, and installed-package tests from an external repository. CI may run in an emulator or container but cannot be claimed identical to the user's Windows desktop. Native Codex and Claude Code activation must be measured *separately*.

## Before/after evidence packet (proposed)

```json
{
  "experiment_id": "proposed-only",
  "protocol_version": "draft",
  "baseline_commit": "exact-sha",
  "arm": "A_or_B",
  "task_id": "fixed-task-id",
  "task_input_sha256": "lowercase-64-char-hash",
  "candidate_sha256": null,
  "role_session_evidence": [],
  "tester_report_ref": null,
  "reviewer_rerun_ref": null,
  "original_plan_ref": null,
  "host_and_route_provenance": {
    "configured": null,
    "reported": null,
    "effective": null
  },
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "cache_read_tokens": null,
    "actual_billed_cost": null
  },
  "outcome": "UNVERIFIED",
  "notes": "No experiment has been run by this plan"
}
```

These are conceptual fields, not an enacted schema. A real design must reuse current validated record formats where possible, avoid duplicating existing keys and add versioned compatibility tests.

## Decision criteria

A proposal is `GO_FOR_OWNER_REVIEW` only if all mandatory safety/correctness gates pass and the claimed improvement has traceable evidence. For efficiency, compare accepted outcomes and full workflow resource use: an improvement can be better context allocation, more reliable completion or fewer wasted retries even if raw tokens don't decline.

A safety failure, missing evidence, inconsistent route identity or severe regression returns `NO_GO` even if token use looks favorable. `INCONCLUSIVE` is a valid outcome when pilot size, cache confounding or telemetry limits prevent a robust decision. Every result retains failed attempts and counterevidence.

## What constitutes proof

- **Unit/property test:** a contract behaves on chosen fixtures.
- **Integration test:** components cooperate in a permitted isolated environment.
- **Native host smoke:** real Codex or Claude Code role/session operation is observed.
- **Repeatable comparison:** same predeclared task suite and independently verified oracles across arms.
- **Production claim:** requires much broader evidence than this plan and explicit release/operational approval.

Do not promote a result up these levels merely because the documentation says VERIFIED.
