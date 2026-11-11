# CouncilFlow current delivery

**CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED**

Communication-contract implementation, independent technical verification,
experiential review and the original Planner's final check passed. The corrected
skill is packaged with its supporting files. Successful native explicit invocation
remains UNVERIFIED after a fresh HTTP401/systemError result.

## Changes and product

The product remains `.agents/skills/council-flow/`, an installable instruction
skill using native Codex subagents. JSON task packets now use the Owner's
`council-flow`/`1.0` envelope with unique IDs, roles, task/plan/revision/attempt,
UTC timestamps, causal and candidate references, role-specific payloads and
artifact hashes. No authoritative v0.2.1 project schema was found; no full ACP
Supervisor implementation is claimed.

- `scripts/contracts.py`: strict stdlib JSON validation, supplied-context/origin
  checks, hash/root checks, restricted YAML validation and optional JSONL.
- `policies/roles.yaml`: versioned role/workflow/Owner/evidence/isolation/resource
  policy. Native configuration stays in four `.codex/agents/*.toml` files.
- SKILL and all role references/instructions require the formats at controlled
  boundaries. Owner progress and results remain concise natural language.
- The native transport/authentication and actual permissions are outside this
  helper. YAML and JSON cannot grant authority or an OS sandbox. Infrastructure
  retries3/crash recoveries2 are instructions, not enforced accounting; productive
  engineering rework has no lifetime cap.

Complete skill subfolders, including helper and policy, must be copied when
installing elsewhere. README and RELEASE explain this without a rebuild, package
installation, API key, database, server, external provider or custom supervisor.

## Actual verification

Final independent Tester: **103 methods PASS, 0 unexpected failed suites,
0 skips**. Exact commands/counts/exits are in
`reports/restoration/verification/release/suite-results.json`:

| Suite command (`python3 -m unittest discover -s … -v`) | Tests |
|---|---:|
| `tests` | 47 |
| `demo/receipt` | 11 |
| `reports/demo/verification` | 5 |
| `demo/csv-summary` | 15 |
| `reports/csv-summary/verification` | 6 |
| `demo/structured-flow` | 4 |
| `reports/restoration/verification/initial` | 8 |
| `reports/restoration/verification/final` | 7 |

All45 previously passing checks remain passing. The old starter was separately
executed at baseline: 2 tests, 1 intentional failure, excluded from passing
counts. New real failures were preserved, rejected and repaired by fresh Workers:
initial sum2 versus required4; malformed context errors; optional-field types;
contradictory acceptance; referenced-plan types and missing passed-result evidence.
Earlier failed logs/snapshots remain intact. Actual output checks include receipt
Rp103,000, sum4, unrelated signed values, error paths and disabled-network runs.

The final Tester executed and saved its complete structured report before its
native delivery turn hit a usage limit. On resume, Parent validated the genuine
saved report, all hashes and supplied context; it did not relabel its own work as
Tester or claim successful native final-response delivery. See
`reports/restoration/resume-verification.json`.

Independent Reviewer: eight actual CLI interactions PASS, no blocking usability
finding. Two low-severity release-copy notes are addressed in current README and
RELEASE: current status, static versus dynamic evidence and mandatory Tester
oracle reference. Full review/evidence: `reports/restoration/review/`.

## Live workflow and limits

Actual five AI roles were observed: parent Manager, dedicated Planner, fresh
Workers, independent Testers, and separate Reviewer. Nine workflow sessions
participated (Manager1, Planner1, Workers3, Testers3, Reviewer1), plus a separate
native-activation capability Tester. Real IDs and packets are in
`reports/restoration/messages/`, with accepted causal order and Parent-observed
origin bindings in `live-order.json`/`live-bindings.json`.

Bootstrap packets remain explicitly pre-schema. A real interim Planner subset
map was rejected and preserved, rather than weakening original acceptance.
Optional actual diagnostic exports are bounded JSONL, not a crash-safe ledger.
Synthetic fixtures/mutations are never counted as native agent sessions.

Fresh native corrected discovery passed. Explicit literal `$council-flow` plus
structured skill input was accepted, then the actual native thread entered
systemError with HTTP401 authentication rejection. No completed invoked answer
occurred. Actual IDs, safe outputs and unchanged SKILL hash are in
`reports/restoration/activation/`. Live custom-role-file selection remains
UNVERIFIED; genuine native subagents received the documented role-instruction
fallback. No auth extraction/bypass, new provider/key or repeated identical attempt.

## Deliverables and closeout

- Skill: `/workspace/CouncilFlow/.agents/skills/council-flow/SKILL.md`.
- Archive: `dist/council-flow.zip`, checksum beside it; current integrity,
  complete-file/source-byte and exclusion checks are recorded in
  `reports/restoration/package-verification.json`. The immutable numbered
  archive verification and extracted installation rerun of all103 tests are
  preserved separately; final closeout changes only evidence and release copy,
  with all29 tested product files byte-identical.
- Permanent map: `reports/requirements-traceability.md` separates specified,
  implemented, static, dynamic, native and blocked evidence.
- Original Planner final check: `reports/restoration/planner-final/report.md`
  and `messages/REST-PLAN-FINAL-001.json`, all16 original criteria mapped to
  explicit evidence. The21-message supplied causal sequence and12 optional
  actual events validate with Parent-observed role context; these checks are
  not authentication or new native inference.
- Implementation commit: `3e23bd8872417072377514fdfaff5afc0f23aa8f`.
  The final evidence/archive commit is repository HEAD, reported to the Owner;
  obtain its exact ID with `git log -1 --format=%H`. No push/publication is
  performed. No application repair or Owner decision remains requested.

All communication-restoration criteria pass within their documented scope.
Successful native explicit inference and live custom-role-file selection remain
unverified. R-ACTIVATION in the unchanged plan requires the fresh attempt and
honest reporting; passing that criterion does not pass native activation itself.

In a compatible authenticated Codex session opened at the repository root:

```text
$council-flow Implement the approved coding goal in this repository with independent tests and review.
```

No construction prompt or Owner-authored JSON is needed. Native activation must
remain unverified until a genuine invoked turn and required workflow succeed;
a passing unit count cannot justify COUNCILFLOW_FULLY_VERIFIED.
