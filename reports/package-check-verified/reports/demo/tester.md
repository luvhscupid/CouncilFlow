# Independent TesterResult — CF-DEMO-001

- Actual native Tester identifier: `/root/demo_tester`; parent Manager `/root`.
- Approved contract: `reports/contracts/demo.json`, revision 1, SHA-256 `88cb907ee1371763744fa7a14ad00830e1a383742baa2273b1c8814a1bd48891` (unchanged).
- Implementation author: fresh Worker W002 `/root/demo_worker`, distinct from W001 `/root/skill_worker`; this Tester was assigned after W002 stopped mutations.
- Scope: independent read/execution plus isolated checks/evidence under `reports/demo/verification/` and this report. No application, Worker-test, contract, skill, or configuration edits/repairs.
- Technical disposition: **PASS** for implemented receipt behavior; no mandatory technical defect found. Experiential Reviewer and final Planner checks are still separate responsibilities.

## Actual commands and results

| Command | Exit | Observed output | Evidence |
| --- | ---: | --- | --- |
| `python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v` | 0 | 11 tests ran; OK | `verification/application-tests.txt` |
| `python3 -m unittest discover -s reports/demo/verification -p 'test_*.py' -v` | 0 | 5 independent tests ran; OK | `verification/independent-tests.txt` |
| `bwrap --unshare-net --ro-bind / / --chdir /workspace/CouncilFlow -- python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg` | 0 | rice Rp60,000; onions Rp43,000; Total = Rp103,000 | `verification/offline-output.txt` |
| `python3 -m unittest discover -s demo/starter -p 'test_*.py' -v` | 1 | Preserved baseline: 2 tests, 1 failure; Decimal('73000') != Decimal('103000') | `verification/preserved-starter.txt` |
| `python3 -m unittest discover -s tests -v` | 0 | 8 static skill checks ran; OK | `verification/skill-regression.txt` |
| `git check-ignore reports/runtime/codex-home/auth.json reports/runtime/schema/v2/SkillsListParams.json` | 0 | Both paths returned as ignored | `.gitignore`, `verification/dependency-inspection.json` |
| `sha256sum reports/contracts/demo.json demo/starter/receipt_calculator.py demo/starter/test_receipt_calculator.py` | 0 | Contract unchanged; current starter digests match W002's recorded snapshot | `verification/preserved-hashes.txt` and `worker/preserved-hashes.txt` |

The starter's failure is intentional baseline evidence, explicitly unacceptable as the final application. It is kept separate from all passing final-program suites and was not repaired by the Tester.

## Independent behavioral checks

The Tester authored `verification/test_independent_receipt.py` independently after reading the approved acceptance. It uses Python `Fraction` as a separate exact rational oracle rather than duplicating the implementation's Decimal precision calculation.

- Maximum accepted 18-integer/12-fractional-digit operands, minimum accepted 12-place fractions (result has 24 fractional places), mixed large/small products, and summation all match the independent oracle under ambient Decimal precision 2.
- A deterministic receipt of 73 independently generated products matches exact Fraction line and grand totals.
- API retains Decimal quantity, price, and result types; rejects unsafe binary floats, booleans, unsupported numeric bounds, malformed/currency/grouping/exponent strings, negative values, NaN/sNaN, and infinities; accepts zero quantity and zero price.
- Real subprocess CLI checks verify the exact Owner receipt, an unrelated receipt totaling `Rp40,905.5625`, and an exact tiny receipt totaling `Rp0.000000000000000000000001`.
- Twenty invalid CLI cases cover absent/incomplete entries, blank labels, negative/non-finite/malformed quantity and price, and unsupported precision; each exits nonzero with an error, no traceback, and no partial receipt output.
- Help includes repeated-item argument names, plain decimal convention, and documented input bounds.

Static dependency inspection found only `argparse`, `dataclasses`, `decimal`, `re`, and `typing` imports, all standard library. Actual execution with a separate disabled-network namespace succeeded. Neither check imports predecessor projects. A disabled network namespace demonstrates this execution works offline; it does not establish that role instructions are an independent OS sandbox.

## Original acceptance mapping

| ID | Tester result | Observation |
| --- | --- | --- |
| D01 | PASS | Actual runnable standard-library program; native disabled-network execution succeeded |
| D02 | PASS | Sample line and grand totals exact in tests and real offline output |
| D03 | PASS | Distinct multi-item values calculate correctly; no-items CLI rejected |
| D04 | PASS | Importable API, Decimal types, Fraction oracle at precision bounds and low ambient precision |
| D05 | PASS | Invalid/non-finite/negative values rejected without CLI tracebacks; zero values accepted |
| D06 | PASS | Rupiah thousands convention and exact visible fractional money, including 24 places |
| D07 | PASS | Worker suite independently rerun: 11 pass; separate Tester suite: 5 pass |
| D08 | TECHNICAL PASS; REVIEWER PENDING | Help and instructions inspected and help actually exercised; a separate Reviewer's experiential result is not this Tester's result |
| D09 | PASS | Preserved starter failure reproduced; hashes match recorded fixture snapshot; real W002 differs from W001 |
| D10 | IN PROGRESS | This result records real role/command/output evidence; Reviewer and final Planner records still pending |

## Findings and limits

- No implementation repair is requested by this Tester. The runtime-ignore repair B-01 is present; actual archive/staging contents still require release verification.
- Successful explicit `$council-flow` invocation remains **UNVERIFIED/BLOCKED** by the separate native CLI's authentication/token-refresh rejection. Native discovery and structured-input acceptance do not replace a completed invoked turn. This independent manual native-agent demonstration does not waive V03 or justify a full COMPLETE status.
- Native custom-role-file selection/loading and OS-enforced role isolation were not demonstrated by these tests. This Tester is a genuine separate native session using role instructions supplied by the parent, not a renamed Worker assessment.
- Final disposition for the product belongs to the Manager after independent Reviewer and original-objective Planner checks; no quality threshold or acceptance criterion was changed.
