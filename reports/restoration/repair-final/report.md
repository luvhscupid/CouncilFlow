# Worker repair result — REST-A003

Actual native Worker `/root/restoration_repair_final` repaired B04–B07 under
REST-M015 and unchanged REST-P001 revision 1. This is developer evidence, not
independent acceptance. Only the four assigned files listed below changed;
previous failures, Tester code and working demonstrations were preserved.

## Corrections

- `scripts/contracts.py`: type-check every allowed `changed_files` array,
  including optional Tester/Reviewer evidence metadata; Worker still requires it.
- Reject `accept` with nonempty failed criteria; any supplied failure identity
  must belong to the decision's assigned acceptance identifiers. Existing ordered
  context still rejects identifiers outside the original published plan.
- Validate a root-verified plan is an object with typed matching plan identity,
  positive nonboolean integer revision and nonempty bounded criterion objects.
  Criterion IDs are unique/nonblank; supplied criterion text is nonblank text.
  Preserve project metadata rather than inventing a generic plan-schema engine.
- Require explicit nonempty references for every passed Planner criterion.
  Existing independent-evidence, failed-verification and final-check ordering
  guards are unchanged. References are structure/content-hash checks, not proof
  of semantic truth, sender authentication or filesystem permission.
- `references/communication.md` and `message-contract.json`: document these
  rules and the JSON wrapper for a verbatim referenced Owner-approved prose plan.
- `tests/test_contracts.py`: four permanent regression methods exercise the
  actual reported field/context/evidence failures, including clean CLI errors.

Paths above are relative to `.agents/skills/council-flow/`, except the root test.

## Executed checks

| Command | Exit | Actual result |
|---|---:|---|
| `python3 -m unittest discover -s reports/restoration/verification/final -v` before edits | 1 | Same 7 independent methods failed with 10 failures and 6 errors; `independent-before.txt` retained |
| `python3 -m unittest discover -s tests -v` after edits | 0 | 47 tests PASS, no skips; `contracts-and-skill.txt` |
| `python3 -m unittest discover -s reports/restoration/verification/initial -v` | 0 | Same 8 independent methods PASS; `initial-independent.txt` |
| `python3 -m unittest discover -s reports/restoration/verification/final -v` after edits | 0 | Same 7 independent methods PASS; `independent-after.txt` |
| `python3 -m unittest discover -s demo/structured-flow -v` | 0 | Same 4 fresh-demo methods PASS; `fresh-demo.txt` |
| `git diff --check` | 0 | No whitespace defects |

These 66 methods are developer reruns. The other 37 receipt/CSV checks were not
needlessly repeated by this Worker; the fresh final Tester will independently
rerun the full required suite. No tests were skipped or expected failures changed.
All temporary fixtures used repository-contained directories and were cleaned.

`checks.json` records exact argv/exits and output paths. `preservation.json`
confirms all untouched candidate source hashes, both Tester-file hashes, original
plan hash and immutable input candidate. `candidate-003.json` records new actual
source hashes as the output candidate. No package, commit, global configuration,
permissions, authentication, provider or external project operation occurred.

## Handoff

The terminal JSON job.report replies to actual REST-M015, echoes immutable input
candidate 002 separately from new candidate 003, and is validated against the
installed helper plus supplied real live message context and externally known
Worker binding. Validation does not authenticate native transport.

No open developer finding remains in this bounded repair. Final independent
verification, separate Reviewer, original Planner, traceability/release updates,
ZIP inspection and commit remain Parent responsibilities. Native activation and
custom-role-file selection limitations are not relabeled as passing. Worker
mutations stop after terminal report/context validation; no self-approval.
