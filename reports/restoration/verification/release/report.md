# Independent TesterResult — final candidate003

- Actual native Tester: `/root/restoration_verifier`; parent Manager `/root`.
- Assignment: REST-M016; plan REST-P001 revision 1; task REST-T001; attempt REST-A003.
- Exact candidate: `reports/restoration/repair-final/candidate-003.json`, SHA-256 `34ae400e38925da3eea65464da16283b5359923a133feb87d371ba2b147df05d`.
- Manager-approved oracle: `reports/restoration/oracle.json`, SHA-256 `797c607e70cab233228fd1e57fa5f6322c557b98ca67da4d28f24ef4904f0615`.
- Technical disposition: **PASS**; no remaining implementation defect or repair requested in this assigned check. No product, developer-test, policy, documentation or prior-evidence repairs were made by Tester.

## Actual independent execution

| Command | Methods | Exit |
|---|---:|---:|
| `python3 -m unittest discover -s tests -v` | 47 | 0 |
| `python3 -m unittest discover -s demo/receipt -v` | 11 | 0 |
| `python3 -m unittest discover -s reports/demo/verification -v` | 5 | 0 |
| `python3 -m unittest discover -s demo/csv-summary -v` | 15 | 0 |
| `python3 -m unittest discover -s reports/csv-summary/verification -v` | 6 | 0 |
| `python3 -m unittest discover -s demo/structured-flow -v` | 4 | 0 |
| `python3 -m unittest discover -s reports/restoration/verification/initial -v` | 8 | 0 |
| `python3 -m unittest discover -s reports/restoration/verification/final -v` | 7 | 0 |

**103 actual methods PASS, 0 unexpected failed suites, 0 skipped tests.** The old intentional starter remains excluded from passing counts. Previously failed independent suites were rerun unchanged and now pass; their earlier 3 failures/9 errors and 10 failures/6 errors remain recorded in their original logs.

Exact commands, counts and exits are in `suite-results.json`; eight individual outputs are adjacent. `program-observations.json` records six actual CLI invocations: receipt sample yields Rp103,000, sum 2 3 -1 yields 4, unrelated -7 12 -3 100 yields 102, malformed/missing input exits 2 without stdout/traceback, and real `bwrap --unshare-net` sum yields 4. No simulated offline result is counted.

## Repaired boundary and real packet checks

B01–B07 now satisfy their independent regressions: malformed sequence/context types reject through controlled errors, optional changed_files types are validated for non-Worker roles, accept cannot declare failed criteria, referenced JSON plan identities/acceptance entries have type guards, and passed Planner results require explicit evidence. Existing prior-Manager final-check and known-failed-verification guards remain working.

The actual fourteen-message prefix through REST-M016 validates with root artifact hashes and Parent-observed sender bindings. Nine executed artificial mutations of these current records/diagnostics reject correctly: causal predecessor, candidate hash, original criterion, Worker authority, external sender origin, attempt identity, event message, event task and forbidden event field. These are negative controls over real packet shapes, not invented sessions or message history. Six actual JSONL prefix events validate with known-message references; they remain optional diagnostics rather than a crash-safe ledger or sender authentication.

`live-boundary-checks.json` records these positive and negative results. A passing final Planner plan.check must reply to the actual Manager accept task.decision; an advisory plan.progress can be sent but should not replace that acceptance anchor.

## Acceptance and preservation

| Requirement | Bounded technical observation |
|---|---|
| C01–C04 | Existing valid five-role/type fixtures pass; actual current role packets and supplied context pass; malformed/authority/candidate/criteria cases reject. Original plan hash unchanged. |
| C05–C06 | Actual restricted YAML policy and semantic invariants pass; four TOMLs retain exact documented string fields. Native custom-role selection remains unverified. |
| C07 | Instructions enforce internal JSON, YAML policy, TOML configuration and optional JSONL while Owner updates remain prose. Separate experiential Reviewer still required. |
| C08 | Initial real failure/rejection/fresh-Worker repair is present in actual context; current four-test demo and prior independent negatives pass unchanged. |
| C09 | This distinct Tester is bound to exact assignment/attempt/candidate and Manager strategy; acceptance still requires separate Reviewer and original Planner. |
| C10–C12 | Stdlib-only helper inspection, all45 original checks plus new checks, actual repaired output, and meaningful bad-packet/context sensitivity pass. |
| R-ACTIVATION | New probe already attempted: discovery passes, genuine explicit invocation remains authentication-blocked. No retry or success claim made here. |
| R-DIAGNOSTICS | Six actual bounded event records plus three event-negative mutations pass the stated file checks. |
| R-TRACEABILITY/R-RELEASE | Existing source/instructions inspected; final traceability/status, Reviewer/Planner, updated ZIP/relocation and commit remain Manager closeout. Not claimed complete by this technical report. |

`preservation-and-inspection.json` confirms every candidate source, original plan/oracle/candidate and selected prior failed logs/snapshots has its exact before/after hash. No files outside this repository were used for fixtures; this check required no new fixture directories. All new files are this assigned evidence area and the terminal JSON packet. AST inspection shows stdlib imports only; no provider, database or other project dependency was introduced. File-role instructions are not OS enforcement and structural checks do not authenticate native senders.

The fresh activation report remains unchanged: HTTP401/systemError after native discovery; custom-role selection unverified. This result is not COUNCILFLOW_FULLY_VERIFIED. Manager should assign separate Reviewer, then obtain original Planner objective mapping and perform release/commit bookkeeping. All Tester writes stop after terminal boundary validation.
