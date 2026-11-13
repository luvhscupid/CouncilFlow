# Independent maintenance testing

This is direct engineering verification, not a CouncilFlow self-invocation, formal Gate 3 attempt, or proof of native-role configuration.

## Exact candidate and platform

The release-source inventory plus CI and root Git configuration inputs had SHA-256 `77702c763e5eb0067fdad3dab3a91f66183d8075d5fdad8a95a29f38651a2a1a`. `candidate-before.json` and `candidate-after.json` are equal. Product edits were stopped before this run. The helper SHA-256 was `125b4b0d8064e1e03c4e2c163a00cb38db281733e729c52076f2483cb7a10057`.

Executed on Windows 11, build 26300, Python 3.12.3, using the full executable path recorded in `suite-results.json`. Linux was not executed by this testing agent.

## Regression suites

| Suite | Ran | Passed | Skipped | Failures/errors |
| --- | ---: | ---: | ---: | ---: |
| `tests` | 122 | 120 | 2 | 0 |
| `demo/receipt` | 13 | 13 | 0 | 0 |
| `demo/csv-summary` | 15 | 15 | 0 | 0 |
| `demo/structured-flow` | 5 | 5 | 0 | 0 |
| `reports/demo/verification` | 5 | 5 | 0 | 0 |
| `reports/csv-summary/verification` | 6 | 6 | 0 | 0 |
| Total | 166 | 164 | 2 | 0 |

The two skips are existing file-symlink controls because Windows returned privilege error 1314. Directory-junction and hardlink release controls did execute. Each suite has exact executable, arguments, working directory, counts, exit code, output hashes and raw stdout/stderr evidence in `suite-results.json` and `suite-*.bin`.

## Independent controls

- `verify_source_fidelity.py`: 22 controls, comprising 20 rejected attacks and two accepted unchanged controls. It reads the actual external saved fixture and verifies SHA-256 `e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d`. Attacks include backtick deletion, punctuation, case, meaningful space/tab/newline changes, altered meaning, missing/reordered/duplicate/added criteria, missing/stale original, absent observed provenance, substituted source references, JSON derivative masquerade, mutually consistent altered plan/derivative, contradictory derivative lineage, and original/derivative artifact-ID collision. Exact internal CRLF and tabs survive capture. A real CLI dispatch check passes for unchanged criteria.
- `verify_guard_mutations.py`: two temporary helper mutations were caught by the new regression suite through expected assertion failures: removing raw-source plan comparison, and disabling the explicit rework-dispatch guard. No import/setup failure was counted as mutation detection, and live source bytes remained unchanged.
- `verify_behavioral_oracle.py`: wrong-version and wrong-arithmetic receipt mutants both pass deliberately weakened candidate-owned tests, but pristine baseline tests catch both via named behavioral assertions. Original oracle SHA and mutation before/after snippets are recorded. A real exact-command rerun matches. A retained synthetic corrupted prior-output hash is distinguishable from actual execution evidence.
- `verify_recovery_boundaries.py`: seven synthetic contract controls exercise explicit failed-Tester rework, fresh Worker and attempt, rejection of direct/reused repair, Reviewer mismatch, unmet final criterion and the full Planner-failure recovery regression. Separately, one actual subprocess timeout is recorded blocked; three actual identical exit-73 failures stop at the declared harness bound with a blocked result. None is reported successful.

The pre-fix identity-collision probe is retained in `source-identity-collision-probe.json`; the final independent source control and shipped regression reject that collision. It is historical maintenance failure evidence, not the final candidate result.

## Deterministic command for independent review

`readonly-command-declaration.json` records the exact full Python executable, `-B -c` arguments, working directory, candidate SHA, executable SHA, and input hashes. Its inner command reads only the persistent original fixture and helper, verifies the exact three criteria, and prints `ORIGINAL_CRITERIA_FIDELITY_OK` with LF. Recorded exit code: 0. SHA-256 after CRLF-to-LF-only replacement: `66efbe32da24299975ba2520b4d912958564888120a5e61c7992d33f7998d515`. Reviewer must write its own evidence; this command does not overwrite tester artifacts.

## Limits

Source provenance is a separately supplied caller observation. Neither matching SHA-256 nor an artifact kind authenticates the Owner, makes storage immutable, or enforces native transport. The normal skill/reference instructions mandate source checking before dispatch, rework and final acceptance, but instruction compliance is not an OS security boundary.

Process failures above were actually executed; message transitions are synthetic validator fixtures. The test harness implements its own finite failure loop. This does not establish persistent CouncilFlow retry accounting, native-agent crash recovery, automatic skill activation, effective TOML selection, or E1/E2/E4. Distinct maintenance agents do not establish different model weights. The previous E10 failure remains unchanged.

Package and fresh-checkout verification are coordinated separately by the parent. No product code was edited by this testing agent.
