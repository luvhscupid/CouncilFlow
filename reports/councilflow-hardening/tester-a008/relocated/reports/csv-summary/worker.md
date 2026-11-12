# WorkerResult — CF-CSV-001 W1

- Type: `WorkerResult`; role/session: fresh native Worker `/root/csv_worker`.
- Parent: Manager `/root`; request: approved CF-CSV-001 W1.
- Contract: `reports/csv-summary/contract.json`, revision 1, unchanged SHA-256 `a21ae0c9b09a7c800d31f95fa82d75a414d0f034a7a949e692f2cdc266d977d1`.
- Objective: implement the bounded offline CSV summarizer, validation, sample, instructions and developer tests under original A01–A10.
- Implementation status: IMPLEMENTED; independent Tester, Reviewer and final Planner assessment remain pending. This is developer evidence, not self-approval.

## Changed files

- `demo/csv-summary/csv_summarizer.py`: read-only UTF-8/BOM strict CSV CLI/API, logical record counting, normalized header/selection/shape validation, exact signed decimal totals and contextual errors.
- `demo/csv-summary/sample.csv`: exact Planner-approved sample.
- `demo/csv-summary/README.md`: invocation/output, input conventions and limits, validation behavior, offline/read-only operation, test command and small importable API.
- `demo/csv-summary/test_csv_summarizer.py`: 15 executable behavioral unittest methods, with invalid-case matrices and CLI/API input-preservation checks. Fixtures explicitly live in temporary subdirectories inside this repository's demo and are cleaned on exit.
- `README.md`: one short CSV summarizer link/usage section only.
- Worker evidence in `reports/csv-summary/worker-tests.txt`, `worker-skill-regression.txt`, `worker-receipt-regression.txt`, `worker-checks.json`, and this record.

No skill, custom-agent definition, historical release/report/archive, receipt/starter application, global setting, permission, or external project was modified. No dependencies were installed and no commits or ZIPs were created by this Worker.

## Implementation behavior

The CLI accepts `INPUT --column NAME [--column NAME ...]` and waits until every
record validates before printing its summary. It rejects missing/invalid headers,
duplicate/unknown selections, ragged/blank records, invalid strict CSV quoting,
non-UTF-8 input and invalid numeric cells with clean errors. Numeric errors name
the source, logical record and column; parser errors label physical lines.

Signed plain ASCII decimals are parsed into exact integer units of 10^-12,
after validating the contract's 18 integer/12 fractional digit bounds including
zeros. Integer accumulation avoids both binary floating-point and ambient
Decimal precision. Totals may exceed cell bounds without truncation. Negative
values and zero are valid; output is canonical plain decimal notation.

## Actual developer execution

| Command/check | Exit | Observation/evidence |
|---|---:|---|
| `python3 -m unittest discover -s demo/csv-summary -p 'test_*.py' -v` | 0 | 15 tests PASS, first run; `worker-tests.txt` |
| `python3 -m unittest discover -s tests -v` | 0 | Existing 8 static skill checks PASS; `worker-skill-regression.txt` |
| `python3 -m unittest discover -s demo/receipt -v` | 0 | Existing 11 receipt tests PASS; `worker-receipt-regression.txt` |
| `python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity` | 0 | `Rows: 3`, `Total amount: 30`, `Total quantity: 6` |
| Same sample with reversed selected-column order | 0 | `quantity` total prints before `amount`; correct calculated totals |
| `python3 demo/csv-summary/csv_summarizer.py --help` | 0 | Required input/selection, format, signed numeric limits, offline/read-only and example instructions |
| Sample with `--column missing` | 2 | Source-naming missing-column error; no stdout or traceback |
| `bwrap --ro-bind / / --unshare-net --chdir /workspace/CouncilFlow -- python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity` | 0 | Actual network-disabled execution produces the same correct sample |
| Sample bytes/digest and contract digest before/after; `git diff --check` | 0/PASS | Input unchanged, sample exactly matches contract, contract unchanged, no whitespace issue, no temporary fixture directories left |

Exact command arrays, stdout/stderr, exit statuses and preservation observations
are retained in `worker-checks.json`. All demonstration and test paths stayed
inside `/workspace/CouncilFlow`.

The behavioral suite includes alternative signed/fractional inputs, maximum
accepted cells plus tiny fractions under Decimal precision 2, sums above the
individual-cell magnitude limit, canonical zero, normalized/header-only input,
all required header/selection/shape errors, 19 invalid numeric cases, strict
quote failures, BOM/Unicode/CRLF/quoted commas/escaped quotes/multiline data,
logical error numbering after multiline text, invalid UTF-8, missing/directory
input, API permission-error handling (an injected `PermissionError` using
`unittest.mock`, not an actual OS-denied execution), CLI required arguments and input-byte
preservation on both success and failure. The intentionally failing old starter
was not mixed into the passing suites.

## Findings, decisions and limits

- Open implementation findings from developer checks: none.
- Repair decisions: none; developer tests passed on their first execution. No criteria or expected results were weakened.
- Real native delegation and user-requested direct skill-instruction use are distinct from automatic host skill registration/custom-role selection; this Worker does not change prior UNVERIFIED activation findings.
- Final disposition: READY_FOR_INDEPENDENT_TESTER. Tester/Reviewer/Planner independence and acceptance belong to the Manager's subsequent assignments. All Worker mutations stop after this result.
