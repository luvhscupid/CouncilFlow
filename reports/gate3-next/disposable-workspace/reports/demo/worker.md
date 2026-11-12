# WorkerResult — CF-DEMO-001, W002

- Role: Worker; actual native agent identifier `/root/demo_worker`.
- Request: parent Manager WorkerRequest W002; immutable contract `reports/contracts/demo.json` revision 1, SHA-256 `88cb907ee1371763744fa7a14ad00830e1a383742baa2273b1c8814a1bd48891`.
- Objective: complete the offline receipt calculator after the Manager rejected the preserved starter's Rp73,000 result.
- Acceptance: original D01–D10 retained unchanged. This report is developer evidence, not approval or independent verification.
- Implementation status: IMPLEMENTED; independent Tester/Reviewer/Planner disposition remains pending.

## Changed implementation files

- `demo/receipt/receipt_calculator.py`: importable ProductEntry API; repeated `--item NAME QUANTITY UNIT_PRICE UNIT` CLI; exact bounded Decimal multiplication and summation; rupiah formatting without fractional truncation; concise validation errors.
- `demo/receipt/test_receipt_calculator.py`: 11 unittest methods covering real multi-item calculation, alternative data, exact fractions, low ambient Decimal precision, invalid/nonfinite/negative values, zeros, labels, CLI output/errors/help.
- `demo/README.md`: finished demo commands, numeric bounds, examples, API and baseline distinction.
- `README.md`: actual finished application and test commands.
- `.gitignore`: Manager-authorized build Tester repair excludes `reports/runtime/`, preventing native CLI temporary home/schema/system assets/auth paths from staging or packaging. `git check-ignore` confirmed representative runtime paths are ignored.
- Developer evidence under `reports/demo/worker/` and this report only. No starter, contract, skill, global setting, other project, or existing installation was changed.

## Behavior and numerical limits

Accepted quantity and unit price inputs have at most 18 integer and 12 fractional digits. Unsupported bounds are rejected explicitly. Text inputs are plain decimals; currency/grouping symbols and exponent notation are rejected. API accepts strings, integers, and Decimal values; binary floats and booleans are rejected. Products and sums use sufficient local Decimal precision to retain all accepted digits regardless of ambient precision. Zero is accepted. Fractional rupiah remain visible. The CLI requires a nonblank unit; the API permits its documented default empty unit.

## Actual developer commands and observations

| Command | Exit | Observed result | Evidence |
|---|---:|---|---|
| `python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v` (final) | 0 | 11 tests PASS | `worker/tests.txt` |
| `python3 -m unittest discover -s tests -v` | 0 | 8 static checks PASS; not live runtime certification | `worker/static-regression.txt` |
| `python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg` | 0 | Rp60,000 + Rp43,000; Total = Rp103,000 | `worker/sample.json` |
| `python3 demo/receipt/receipt_calculator.py --item tea 3 12500 box --item sugar 1.5 14000 kg` | 0 | Total = Rp58,500 | `worker/different.json` |
| `python3 demo/receipt/receipt_calculator.py --item tiny 0.123456789012 0.234567890123 each` | 0 | Total = Rp0.028958998519905209728476 | `worker/fraction.json` |
| `python3 demo/receipt/receipt_calculator.py --item rice -2 30000 kg` | 2 | Item-specific quantity error; no traceback | `worker/negative.json` |
| `python3 demo/receipt/receipt_calculator.py --item rice 2 NaN kg` | 2 | Plain-decimal price error; no traceback | `worker/invalid-price.json` |
| `python3 demo/receipt/receipt_calculator.py --help` | 0 | Syntax, numeric convention, bounds, unit, example | `worker/help.json` |
| `bwrap --ro-bind / / --unshare-net --chdir /workspace/CouncilFlow -- python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg` | 0 | Same correct sample with a separate network namespace | `worker/offline.json` |

The first developer test run had 1 failure among 11 tests because a manually typed fractional golden expectation was wrong. It is retained in `worker/tests-first-run.txt`. An independent integer oracle (`123456789012 * 234567890123`, scaled by 10^24) confirmed `0.028958998519905209728476`; the expectation was corrected without changing application arithmetic or acceptance criteria. Evidence: `worker/fraction-oracle.txt`. This was developer-side test correction before independent verification, not a waiver of a mandatory result.

## Preservation, findings, and disposition

- `demo/starter/` was read but not edited. Its meaningful failing baseline remains intact. Current starter and unchanged contract digests are recorded in `worker/preserved-hashes.txt` for subsequent independent comparison.
- No implementation blocker found in developer checks. Independent verification and experiential review are still required.
- Native skill discovery is observed by the Manager. Successful explicit skill invocation remains UNVERIFIED because the separate CLI's inherited authentication could not be refreshed. This real native Worker demonstration does not turn manual parent workflow execution into invocation proof.
- Repair decisions: fix starter quantity multiplication and complete required behavior in the separate final demo; apply accepted runtime-ignore finding; correct a wrong developer-test oracle using independent integer arithmetic.
- Final disposition: READY_FOR_INDEPENDENT_TESTER, not self-approved. Worker mutations stop after this result is saved.
