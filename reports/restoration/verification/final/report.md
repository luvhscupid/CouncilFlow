# Independent TesterResult — candidate 002

- Actual native Tester: `/root/restoration_tester_final`, distinct from both Workers and the initial Tester.
- Assignments: REST-M013 and actual additional bounded request REST-M013B; terminal report replies to REST-M013B.
- Candidate: REST-CANDIDATE-002, SHA-256 `7f9624b4ce4c70ad222055341e846fd9aa1ed8a8f7418fb19103544fbce96917`.
- Manager-approved strategy: REST-MANAGER-ORACLE-001; original plan and acceptance unchanged.
- Scope: independent reads/execution and isolated checks/evidence only in this directory; no repairs or other product edits.
- **Disposition: FAILED.** Earlier defects and the sum demo are repaired, but new concrete payload/context/evidence defects require fresh-Worker correction.

## Actual results

All seven assigned suites independently passed, **92 tests, 0 skips**:
43 root skill/contract, 11 receipt, 5 independent receipt, 15 CSV,
6 independent CSV, 4 fresh sum demo, and the same 8 initial independent controls.
The latter now pass unchanged, confirming the earlier malformed sequence and
falsey-binding repairs. Commands/exits/output references are `suite-results.json`
and the seven named logs. All original 45 previously passing checks are included.

Seven actual program interactions also matched expectations: sum sample `4`,
different signed totals `5` and `-11`, missing/invalid-input errors without
tracebacks, actual receipt total `Rp103,000`, and network-disabled sum output `4`.
See `program-observations.json`. The old intentionally failing starter was not
mixed into passing regression counts.

This Tester added seven focused independent methods. Three methods pass; four
expose new defects through parameterized cases. Actual terminal output is
**FAILED (failures=10, errors=6)** in `independent-terminal.txt`. Earlier probe
outputs and earlier five-method failure logs are retained, not relabeled PASS.
All generated sequences/mutations in these tests are artificial controls, never
fabricated native sessions, approval history or real Manager acceptance.

## Required corrections

- **B04 / C02, C12:** `changed_files` is a recognized optional job-report field,
  but only a Worker report checks its type. Actual Tester and artificial Reviewer
  mutations with `42`, `false`, or an object are accepted. Validate its bounded
  string-array type whenever allowed, or reject it for roles where it is not
  supported. Evidence: `role-payload-probes.json`.
- **B05 / C04, C08, C12:** a Manager `accept` decision can explicitly contain
  nonempty `failed_acceptance_ids`, including both an original criterion and an
  unknown identifier, and still validate against an otherwise positive supplied
  context. Reject current failed criteria on acceptance and invalid criterion
  references; do not treat an explicit failure list as a successful decision.
  Evidence: `decision-probes.json`.
- **B06 / C02, C04, C12:** root-verified `plan_ref` file hashes are checked, but
  the decoded plan artifact's context types are not. Non-object plans raise
  `AttributeError`; malformed acceptance entries raise `TypeError`; boolean
  `plan_revision: true` is accepted as revision integer 1. Add small explicit
  plan identity/revision/acceptance type guards with controlled errors, preserving
  the approved plan format. Evidence: `context-evidence-probes.json`.
- **B07 / C09, C12:** a passed final Planner map can provide empty evidence arrays
  for every passed criterion and no outer evidence reference. A prior valid
  Manager decision exists in this artificial control, so the validator currently
  admits the uncited map. Require explicit usable evidence references for passed
  results to support the requested criterion-to-evidence traceability; structural
  references still cannot prove the evidence's semantic truth. The independent
  negative expectation is preserved for Manager evaluation and repair.

Two related controls already reject correctly: a passed Planner check before
Manager acceptance fails `final_check_context`, and omitting a previously known
failed Tester report for the same candidate from acceptance `report_ids` fails
`failed_verification`. Do not weaken these working guards.

## Verified positives and limits

The actual current controlled eight-message prefix passes ordered context,
root artifact hashes and Parent-provided origin bindings. Causal, valid-but-wrong
candidate, authority, acceptance-list and expected-origin mutations reject.
Six actual diagnostic events pass with known-message references; altered message
or task IDs, unknown fields and duplicate event IDs reject. These are live
controlled-file observations, not native transport authentication or a crash-safe
event ledger. `live-input-order.json` freezes the assigned prefix so later
legitimate Manager progress cannot silently change these test inputs.

Restricted YAML role/Owner/retry/permission invariants and current native TOML
documented shapes are covered by the passing suites. Native custom-role-file
selection remains UNVERIFIED. Current activation evidence still reports fresh
discovery PASS and actual invoked native authentication/systemError BLOCKED; no
new authentication attempt or status upgrade occurred here.

Before/after hashes of all candidate source files, original plan, oracle,
candidate manifest and earlier Tester code match. `preservation-and-inspection.json`
records this plus standard-library-only imports. Failed helper bytes are saved
as `contracts-candidate002.py`. Every temporary fixture was created explicitly
inside this verification directory and cleaned. No product, developer test,
policy, prior evidence, permission, dependency, account or global configuration
was changed. Reviewer, final Planner, traceability/release update, packaging and
commit remain Parent-coordinated after required repair. All Tester writes stop
after terminal message/context validation.
