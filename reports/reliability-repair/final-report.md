# CouncilFlow bounded reliability repair

**Engineering repair: verified. Native workflow: unverified.**

- **F1 — PASS.** Reviewer now references the exact earlier Tester message by message ID. With `--root`, the referenced file must contain that exact message and match its SHA-256. This removes the circular self-hash while retaining candidate, attempt, plan and report binding.
- **F2 — PASS.** Tester records the invoked executable path. Reviewer must rerun that exact executable and arguments with the same working directory, candidate and inputs. Exact command binding, exit-code comparison, CRLF-to-LF-only normalization and stdout SHA-256 checks remain enforced.
- **F3 — PASS.** Planner-triggered rework now requires a failed/blocked Planner check, an earlier Manager acceptance of that same candidate, a Manager progress packet, exact preservation of all failed original criteria and the accepted report IDs, then a fresh Worker and attempt.

The skill/contract suite increased from **64/64 passing** to **71/71 passing** with `python -m unittest discover -s tests -v`. Receipt regression stayed **12/12 passing** with `python -m unittest -v` from `demo/receipt`. CSV and structured demos passed 15 and 4 tests. The starter fixture retained its deliberate failure (1 of 2), unchanged. Policy validation passed. Exact before/after commands and counts are in `test-results.json`. Existing Reviewer comparison and model-authored timestamp protections remain covered by passing regression tests.

The new deterministic sequence contains 20 ordered messages across attempts A1 and A2 and passes the real validator with root evidence. It includes immutable candidate snapshots, raw stdout/stderr/exit records, message packets and SHA-256 hashes. Eight negative controls rejected altered Tester references, candidate hashes, command identity, failed criteria, rework bypass, Worker reuse, attempt reuse and accepted-candidate swapping in final progress. The fixture uses synthetic logical role identities; local subprocess results are real, but no separate native agent sessions are claimed.

Historical Gate 3b remains immutable and fails validation. The baseline validator rejected the Reviewer’s Tester report link because it looked for that link in the Tester’s own evidence list. The corrected validator also rejects the historical report because it does not use the new exact message-ID reference. Historical attempt 2 begins with a Worker assignment directly after a failed Planner check, without a Manager rework decision; its Tester recorded `C:\Users\cupid\AppData\Local\Programs\Python\Python312\python.exe` while its Reviewer recorded `python`. These records and hashes were not rewritten.

The original Round 6 workspace and the fixture’s 66 historical evidence files match their recorded hashes. The repair was built in `E:/Saint/PROJECTS/CouncilFlow-round6-reliability-repair`. No Git metadata exists, so no commit was created. The changed-file manifest and unified patch are provided.

Release ZIP: `dist/council-flow-reliability-repair.zip` (16 entries), SHA-256 `f0798e34d9eeb6cd92dcceb75e90b27543712d3a64f0ceaecc9b152d28656db7`. CRC and packaged content hashes passed; see `package-verification.json`.

Native `$council-flow` invocation and E1–E10 observations are **UNVERIFIED**; no authenticated native activation was observed. The new fixture is not a substitute for that status.
