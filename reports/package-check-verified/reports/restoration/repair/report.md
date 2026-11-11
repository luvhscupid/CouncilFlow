# WorkerResult — REST-A002 repair

- Native Worker instance: `/root/restoration_repair`, fresh and distinct from `/root/restoration_worker`.
- Request: validated REST-M012, replying to Manager's REST-M011 rework decision after separate Tester failure.
- Original plan REST-P001 revision 1 and all acceptance criteria are unchanged.
- Input candidate: REST-CANDIDATE-001-FINAL, SHA-256 `72ba379287b19146c19912fa9b8bef778aa321606d726ad960fc8882ee73410f`.
- Output: immutable `candidate-002.json`, with current source hashes and a separate passing demo source snapshot.
- Developer disposition: repairs implemented and developer checks PASS. This is not independent testing, Reviewer approval, native activation success or final task acceptance.

## Repairs made

1. `scripts/contracts.py`: supplied expected-sender bindings must be a bounded dictionary, even when a wrong supplied type is falsey. Binding message IDs and actor records are validated before use. Each sequence message is fully validated before its identity is used for a dictionary lookup. This converts proven non-object/bad-identity/binding failures into controlled `ContractError` or concise CLI JSON errors instead of `AttributeError` tracebacks or silent acceptance. Related malformed Owner-provenance context collections are also rejected explicitly; no new approval authority is granted.
2. `tests/test_contracts.py`: four focused regression methods were added for non-object/bad-ID sequence entries, malformed and falsey actor maps/entries, wrong Owner-provenance context types, and actual CLI error behavior. No existing developer or Tester assertion was removed or weakened.
3. `demo/structured-flow/sum_values.py`: sums all parsed signed ASCII operands rather than returning the first. The unchanged original mandatory command `2 3 -1` now prints `4`; different operands calculate actual sums. Existing argument validation remains intact.
4. `demo/structured-flow/README.md`: describes the current working demo and links the preserved initial failure/rework history rather than presenting the repaired result as unfinished.

No policy, native TOML, prior packet/report, original receipt/CSV app, required demo test, isolated Tester test, global configuration, credential, permission or dependency was changed. No package or commit was created by this Worker.

## Actual checks

| Command | Exit | Observed result | Evidence |
|---|---:|---|---|
| Initial independent suite before repair | 1 | 8 methods; 3 failures and 9 errors, reproducing the reported defects | `independent-before.txt` |
| `python3 -m unittest discover -s tests -v` | 0 | 43 tests PASS: 8 existing static + 35 focused contracts | `contracts-and-skill.txt` |
| `python3 -m unittest discover -s reports/restoration/verification/initial -v` | 0 | The same 8 separate Tester methods now PASS, without editing them | `independent-after.txt` |
| `python3 -m unittest discover -s demo/structured-flow -v` | 0 | All 4 unchanged mandatory demo tests PASS | `fresh-demo.txt` |
| Receipt and independent receipt suites | 0 | 11 + 5 tests PASS | `receipt.txt`, `receipt-independent.txt` |
| CSV and independent CSV suites | 0 | 15 + 6 tests PASS | `csv.txt`, `csv-independent.txt` |
| `python3 demo/structured-flow/sum_values.py 2 3 -1` | 0 | `4` | `regressions.json` |
| `python3 demo/structured-flow/sum_values.py -8 5 +4 0` | 0 | `1` | `regressions.json` |
| `python3 demo/structured-flow/sum_values.py -3` | 0 | `-3` | `regressions.json` |
| Invalid value `1.2` | 2 | Actionable error; no stdout/traceback | `regressions.json` |
| Receipt sample | 0 | `Total = Rp103,000` | `regressions.json` |
| Actual `bwrap --unshare-net` demo sample | 0 | `4` with network namespace disabled | `regressions.json` |

All 92 tests in the listed passing suites passed, with no skips. This count is
43 + 8 + 4 + 11 + 5 + 15 + 6; it does not include the before-repair failed run or
pretend that the intentional old starter is a passing final suite. Exact argv,
output and exit observations for regressions/demo checks are in `regressions.json`.
The first failed independent run remains preserved; no failure history was erased.

Fixtures use explicit in-repository directories and clean up. The original plan,
unchanged demo test and isolated Tester test digests are recorded in preservation
evidence. No new native activation attempt occurred; the known authentication
blocker and custom-role-selection limitation are unchanged.

The final JSON report is checked against the installed helper, externally known
Worker identity from REST-M012, and the complete supplied live causal sequence.
These checks validate controlled records and evidence hashes; they do not
authenticate opaque native transport or create an OS sandbox. Final independent
Tester, separate Reviewer, Planner acceptance, packaging and commit remain the
parent Manager's responsibilities. All Worker mutations stop after handoff.
