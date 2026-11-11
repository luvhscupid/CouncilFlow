# TesterResult — CF-CSV-001

- Role: independent Tester; actual native session `/root/csv_tester`; parent Manager `/root`.
- Contract: revision 1, `reports/csv-summary/contract.json`; SHA-256 `a21ae0c9b09a7c800d31f95fa82d75a414d0f034a7a949e692f2cdc266d977d1` unchanged.
- Implementation author: distinct Worker `/root/csv_worker`, W1, confirmed stopped before this assignment.
- Scope: read/execution; new independent checks and evidence only under `reports/csv-summary/verification/` and this record. No application, developer-test, documentation, contract, historical release, configuration or permission edits.
- Technical disposition: **PASS**. No implementation defect or repair request found. Independent experiential Reviewer and final Planner check remain separate requirements.

## Commands actually executed

| Command | Exit | Observed result |
|---|---:|---|
| `python3 -m unittest discover -s demo/csv-summary -v` | 0 | 15 application tests PASS |
| `python3 -m unittest discover -s reports/csv-summary/verification -v` | 0 | 6 independently authored tests PASS |
| `python3 -m unittest discover -s tests -v` | 0 | 8 existing static checks PASS |
| `python3 -m unittest discover -s demo/receipt -v` | 0 | 11 existing receipt tests PASS |
| `bwrap --unshare-net --ro-bind / / --chdir /workspace/CouncilFlow -- python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity` | 0 | Actual network-disabled sample: `Rows: 3`, `Total amount: 30`, `Total quantity: 6` |

Exact argv, stdout/stderr and exit statuses are in `verification/commands.json`;
individual outputs are `application-tests.txt`, `independent-tests.txt`,
`skill-regression.txt`, `receipt-regression.txt`, and `offline-sample.txt` in that
directory. The deliberately failing starter was not mixed into these passing
suites.

## Independent observations

`verification/test_independent_csv.py` was authored by this Tester from the
unchanged contract after independently examining the final source. Its numeric
oracle uses `Fraction`, independently of the implementation's integer fixed-point
calculation. A deterministic 143-record, two-column input includes maximum-sized
cells, 12-place fractions, tiny values, negative cancellation, signed zero and
137 generated rows. API totals under ambient Decimal precision 1 and actual CLI
totals both match exact rational sums; requested column ordering is retained.

Actual subprocess cases additionally check BOM/UTF-8 non-ASCII descriptors, CRLF,
quoted commas, escaped quotes, multiline descriptors and empty text fields;
normalization and blank/duplicate/control headers; missing/case-mismatched and
duplicate selections; header-only zero totals; empty and BOM-only rejection;
21 bad numeric forms in a late record; ragged and blank records after multiline
data; two strict quote failures; invalid UTF-8; missing and directory paths; help
and required arguments. Invalid cases return 2 with no traceback or partial
summary. Shape/numeric errors identify the correct logical record, file, and
column where applicable; parser errors label physical lines explicitly.

Input bytes are compared before/after successful and failing independent CLI
calls; API preservation is also covered. All generated fixtures use explicitly
repository-contained temporary directories and are cleaned up. Source, contract,
developer tests, sample and both instructions files have identical before/after
digests; see `verification/preserved-before.json` and
`verification/preservation-and-dependencies.json`.

## Original acceptance mapping

| ID | Technical result | Evidence/limit |
|---|---|---|
| A01 | PASS | Runnable help/sample, only standard-library imports by static AST inspection, actual disabled-network execution |
| A02 | PASS | Exact sample and alternative 143-record totals; descriptor text allowed; requested/reversed ordering checked |
| A03 | PASS | Header/selection failures, normalization, case sensitivity, required arguments, header-only zero and empty/BOM-only behavior exercised |
| A04 | PASS | Field widths, blank records, empty/invalid numeric cells and required strict malformed-quote cases exercised |
| A05 | PASS | Separate Fraction oracle covers accepted signed bounded inputs, mixed large/tiny values, negative cancellation, totals beyond individual-cell bounds and low ambient precision; invalid/unsupported numeric forms rejected |
| A06 | PASS | Actual BOM, UTF-8, CRLF, quoted commas/quotes/multiline descriptors and logical counts; invalid UTF-8 rejected |
| A07 | PASS with stated test scope | Actual data/parser/encoding/missing/directory CLI errors have no partial stdout or traceback and correct context. Permission-denial handling is fault-injected in the independently rerun developer suite and supported by the OSError handler; no actual OS permission change/denial experiment is claimed |
| A08 | PASS | Input byte preservation checked on success/failure; actual separate network namespace execution succeeds; imports/read-only file opening also inspected |
| A09 | PASS | 15 application + 6 independent checks pass; existing 8 static and 11 receipt regressions pass; Tester repaired nothing |
| A10 | TECHNICAL PASS; REVIEWER/FINAL PLANNER PENDING | Help/docs inspected and actual CLI cases run; this record does not substitute for the distinct experiential Reviewer or original Planner's final map |

## Findings, limits and disposition

- Open technical defects: none. Repair decisions requested: none. No mandatory
  criterion was weakened or silently reinterpreted.
- Header controls are checked before stripping outer spaces, so raw leading tabs
  and quoted newline controls cannot be normalized away. This preserves the
  contract's explicit control-character ban.
- The native network-disabled command proves that execution works offline; it
  does not prove independent OS isolation for role sessions.
- The Owner-requested repository skill was applied through supplied instructions
  to real native roles. Automatic skill-catalog registration and live custom-role
  file selection remain separately unverified; these checks do not amend the
  earlier release's activation status or claim successful standalone CLI auth.
- Final task acceptance belongs to the Manager after the separate Reviewer and
  original Planner checks. This Tester stops all evidence mutations after this
  result and reports to the Manager only.
