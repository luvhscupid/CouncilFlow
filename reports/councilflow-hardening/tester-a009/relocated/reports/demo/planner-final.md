# Final PlannerResult — CF-DEMO-001

- Type: `PlannerResult`; phase: `final`.
- Actual native Planner session: `/root/demo_planner`, reused from the original demo contract.
- Parent Manager: `/root`.
- Objective: compare the finished offline receipt calculator against every original D01–D10 criterion without changing acceptance.
- Implementation status: final application implemented, independently tested, and experientially reviewed.
- Application disposition: **PASS**.
- Full product disposition: **PARTIAL — successful native explicit skill invocation remains unverified because the separate CLI could not complete authenticated inference**.
- Repairs by this Planner: none. Only these final Planner records were written; no application, test, skill, configuration, or acceptance edits.

## Contract integrity and actual sessions

The original `reports/contracts/demo.json` SHA-256 is unchanged:
`88cb907ee1371763744fa7a14ad00830e1a383742baa2273b1c8814a1bd48891`.
The original build contract is also unchanged:
`9f9acd446921eb92d54ded3de94ebdbdca735da17d90ec54d9966491402619ac`.
The contract's initial `PLANNED_NOT_IMPLEMENTED` status remains historical rather
than being overwritten with a retrospective success assertion.

The native collaboration inventory observed during this final check confirms
distinct actual sessions `/root`, `/root/demo_planner`, `/root/demo_worker`,
`/root/demo_tester`, and `/root/demo_reviewer`. These are the five role sessions,
including the parent Manager. The inventory also exposes distinct completed
Tester, Reviewer, and Worker results. This establishes real separate native
sessions, not independent models/providers or OS-enforced role isolation.
The earlier W001 `/root/skill_worker` is identified separately in durable
Manager/Worker reports and did not implement the final application.

## Original acceptance mapped to evidence

| ID | Final result | Evidence and observation |
| --- | --- | --- |
| D01 | PASS | `demo/receipt/receipt_calculator.py` imports only standard-library modules. `reports/demo/tester.md` records actual network-disabled execution, exit 0; no predecessor import, network service, or package installation needed. |
| D02 | PASS | Tester and Reviewer actual sample records show Rp60,000, Rp43,000, and Rp103,000. This Planner also executed the exact repeated-item command at final check and observed those three amounts, exit 0. |
| D03 | PASS | Independent Tester exercised an unrelated receipt totaling Rp40,905.5625; Reviewer exercised black tea/sugar totaling Rp58,500. Missing-item invocation returns a clear nonzero usage error. |
| D04 | PASS | API inspection confirms Decimal storage/products/totals with explicit local precision. Input bounds are documented and rejected beyond the supported range. The separate Tester's Fraction oracle checked boundary operands, tiny fractions, mixed values, 73 entries, and ambient Decimal precision 2; exact accepted fractions include more than two places. |
| D05 | PASS | Worker suite plus separate Tester checks cover malformed, negative, non-finite, unsupported, and unsafe numeric inputs; zero quantity/price are accepted. Twenty actual invalid CLI cases returned nonzero without traceback or partial receipt. |
| D06 | PASS | Actual sample formatting uses comma thousands; fractional checks include Rp0.02 and Rp0.000000000000000000000001 without silent truncation. Reviewer observed fractional and free-item behavior. |
| D07 | PASS | Independent `/root/demo_tester` reran all 11 application tests and authored/executed 5 separate Fraction-oracle tests; both suites passed. The 8 static checks also passed, and are separately classified as static. |
| D08 | PASS | Separate `/root/demo_reviewer` reports seven actual CLI interactions: help, sample, alternative, fraction/zero, invalid price, negative quantity, and empty input. `demo/README.md` and help explain syntax, units, plain decimal convention, bounds, and tests. No blocking usability finding. |
| D09 | PASS | Starter remains separate and intentionally defective; Tester independently reproduced 2 tests/1 failure, Rp73,000 instead of Rp103,000. Manager explicitly rejected it and assigned correction to fresh W002 `/root/demo_worker`, distinct from W001. Starter hashes match the preserved snapshot; no later implementation repair was required by independent results. |
| D10 | PASS | Role reports, exact commands/exits/outputs, Manager decisions, native identifiers, preserved contracts, and this final map are recorded. Reports explicitly keep successful native invocation UNVERIFIED and do not label the manual real-agent workflow an explicitly activated end-to-end run. |

Primary evidence: `reports/demo/tester.md`, `reports/demo/reviewer.md`,
`reports/demo/worker.md`, their linked raw command/output records,
`reports/manager-execution.md`, and `reports/validation-results.md`.

## Final direct observations

Before writing final records, Git HEAD was
`3da0410abab20f59e9360e04e57f5dc583fe2309` and `git status --short` was empty.
This Planner inspected the final source and executed:

```sh
python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg
```

Exit 0; actual output:

```text
2 kg rice × Rp30,000 = Rp60,000
1 kg onions × Rp43,000 = Rp43,000
Total = Rp103,000
```

Preserved starter hashes observed at this check:

- `demo/starter/receipt_calculator.py`: `a3461d8d2910f6a235e590cef4fd624952cc7fd7c20c882b3d07593baf36e9ab`
- `demo/starter/test_receipt_calculator.py`: `4ac705d92aa070397222259fcef0d9838f7c9d173f0e54675d5686558ed183a8`

No application criterion remains failed or unverified. The required product-level
end-to-end native activation proof remains missing; a correct calculator and real
subagents cannot waive that original requirement. Manager should deliver the
working artifacts with a **PARTIAL** Owner report and the precise authentication
blocker. Final-record commit is the Manager's remaining release bookkeeping.
