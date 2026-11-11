# Independent TesterResult — REST-T001 / REST-A001

Native session `/root/restoration_tester_initial`, separate from implementation
Worker `/root/restoration_worker`. Original plan REST-P001 revision 1 and Manager
strategy `reports/restoration/oracle.json` were read unchanged. Assigned candidate
is `REST-CANDIDATE-001-FINAL`, manifest SHA-256
`72ba379287b19146c19912fa9b8bef778aa321606d726ad960fc8882ee73410f`.
This Tester does not repair implementation, developer tests or policy.

**Technical disposition: FAILED — mandatory fresh demo failure and two concrete
controlled-validation defects require fresh-Worker rework.**

## Actual execution

`commands.json` records command arrays, exits and output references. Independently
rerun suites passed: 39 root checks (8 preserved static plus 31 focused contract),
11 receipt, 5 independent receipt, 15 CSV and 6 independent CSV: 76 passing tests,
including all 45 previously passing checks. The receipt CLI actually printed
Rp60,000 + Rp43,000 = Rp103,000, exit 0.

The new demo separately ran 4 tests with 1 mandatory failure, exit 1. Its actual
`sum_values.py 2 3 -1` invocation exits 0 but prints `2`, not required `4`.
This is the deliberately incomplete fresh candidate, not the historical starter
or an acceptable completed implementation. Evidence: `fresh-demo.txt` and
`commands.json`. The old intentionally failing starter was not mixed into passing
regression counts.

The Tester authored and ran 8 additional independent test methods. Five passed;
three methods expose the boundary defects below through parameterized checks.
Unittest output is `FAILED (failures=3, errors=9)` because subcases include both
incorrect acceptance and uncaught exceptions; this is not a passing suite.
Original output is retained in `independent-first.txt`.

## Required rework

- **B01 / C02, C04, C12:** `validate_sequence([[]])`, scalar and other non-object
  message entries raise uncaught `AttributeError` before normal type validation.
  CLI `sequence` on a file containing `[]` prints a traceback instead of a bounded
  structured rejection. Input must be rejected through the validator's controlled
  error path, without attempting `.get` on a non-object.
- **B02 / C02, C04, C12:** malformed context bindings are not type-checked.
  `expected_senders=[1]` and other truthy wrong types raise `AttributeError`;
  `expected_senders=[]` is silently coerced to absence and accepted. Actual CLI
  `--bindings` pointing to `[]` exits 0 and reports valid. Reject wrong binding
  types explicitly; validate supplied actor-map structure rather than silently
  disabling the boundary. Tests are in `test_independent_contracts.py`.
- **B03 / C08:** finish summing all signed operands under the unchanged original
  demo acceptance; do not change the mandatory test or expected result.

Actual API observations/traces are `boundary-probes.json`; actual CLI stdout,
stderr and exits are `cli-boundary-failures.json`. Failed helper source bytes are
preserved in `contracts-candidate001.py`; initial demo bytes already exist in the
Worker's immutable `initial_sum_values.py`. No product repair was made here.

## Verified strengths and acceptance scope

| Criteria | Observation |
|---|---|
| C01 | Positive five-role/all-purpose fixtures pass developer tests; actual current Manager/Planner/Tester assignment packets pass structural and ordered-context checks. Final role loop remains pending. |
| C02 | Strict JSON malformed/duplicate/nonfinite/overflow/UTF-8/bool/unknown/bounds mutations pass, but malformed sequence/bindings defects B01/B02 prevent full PASS. |
| C03 | Invalid roles/decision authority, external expected-origin spoof checks, self-oracle substitution and unauthorized decision mutations rejected. No authentication claim. |
| C04 | Valid actual context and candidate/acceptance/origin mutations behave correctly; wrong context types still fail uncontrolled or are accepted, so overall FAIL. |
| C05 | Real restricted YAML parses/validates; duplicate/tag/anchor/alias/float and authority/resource mutations rejected. This is not a general YAML parser. |
| C06 | Four TOMLs parse with exact documented name/description/developer_instructions fields and strings. Live custom-role selection remains UNVERIFIED. |
| C07 | Skill/policy/role integration inspected; actual Owner-facing experience still needs separate Reviewer. |
| C08 | Actual mandatory failed test observed; reject and send to fresh Worker. Rework cycle not yet completed. |
| C09 | This report is tied to actual assignment, candidate hash and Manager strategy; full acceptance still needs completed repair and separate Reviewer. |
| C10 | Helper AST imports are standard library only; no new provider/database/service dependency found. |
| C11 | All previous 45 checks pass again; actual receipt sample correct. |
| C12 | Real malformed actual-packet mutations and independent negative controls execute; B01/B02 are genuine failures, not example-file success assertions. |

Root-boundary artifact checks rejected digest mismatch, traversal and a symlink
escape from a supplied test subroot; every target remained inside the authorized
repository. Worker-output candidate changes are accepted while Tester/Reviewer
candidate changes, dropped criteria, Worker-only acceptance, nested artifact-ID
changes and passed-Tester/failed-check contradictions are rejected.
Bad UTF-8/surrogates in policy/events are controlled errors. JSONL tests are
explicitly synthetic diagnostics, not real model events or a crash-safe ledger.

## Preservation and limits

`preservation-and-inspection.json` confirms all observed product files, plan,
oracle and candidate manifest unchanged during this assignment, and current
source hashes match the assigned manifest. All fixtures were explicitly created
inside this verification area and cleaned. No permission, dependency, credential,
global configuration or other-project operation was performed.

Fresh activation evidence from the separate probe still shows native discovery
PASS and explicit turn authentication/systemError BLOCKED. That result is not
upgraded by passing static/unit checks or this actual Tester session. Reviewer,
final Planner, updated traceability, package and commit remain pending. Stop all
Tester writes after the final JSON report and boundary-validation output.
