# Manager result — Final Gate 3 E10 remediation

## Outcome

The exact-criteria guard and regression coverage are implemented. Independent
Tester attempt 2 passed, and independent Reviewer attempt 2 accepted the exact
deterministic rerun. The release archive was rebuilt from this candidate and
its extracted tests passed.

## E10 source change

Before dispatch, Manager must run sequence validation in explicit criteria
fidelity mode with an externally trusted reference to the Owner-approved
criteria artifact. The validator checks source bytes against the supplied
SHA-256 and compares ordered criterion IDs and text exactly, without
normalization. Missing, stale, duplicated, omitted, reordered, added, or
modified criteria reject the plan. A hash detects stale bytes; it does not
authenticate Owner approval. The current authentic Owner fixture is unavailable,
so only synthetic fixtures were used in tests and this capability remains fail
closed without the source.

The previous CSV E10 failure remains separately recorded in
`historical-e10-failure.md`; no new CSV experiment was run.

## Independent verification

- Tester attempt 2: focused contracts 72 tests, 2 Windows symlink skips; full
  `tests/` suite 93 tests, 2 skips; receipt demo 12 passed; structured-flow demo
  4 passed. No CSV application suite or Gate 3 experiment was run.
- Tester deterministic command: `C:\Users\cupid\AppData\Local\Programs\Python\Python312\python.exe reports/councilflow-e10/tester/run_contracts.py`, exit 0; CRLF-to-LF-only stdout SHA-256
  `dca0c2f5dd970a80b4ff528bdf5e8a6c0d1fca49f0ea7e1eea1a3ac1f49cfd3e`.
- Reviewer attempt 2 independently reran that command; exit and normalized
  stdout hash matched Tester evidence. Reviewer accepted with limitations.
- Attempt 1 remains preserved as failed review evidence: its Tester mislabeled
  the raw CRLF output digest as normalized, and Reviewer rejected the mismatch.

## Host evidence and remaining limits

E1, E2, and E4 are `UNVERIFIED (HOST_CAPABILITY_MISSING)`: this host exposes no
skill activation/load record, no activation-to-delegation causal record, and no
effective child TOML identity. This was inspected once. Requested agent types
and this mission's real subagent dispatches were not used as substitutes.

The draft at `reports/gate3-next/OWNER-TASK-DRAFT.txt` remains unapproved. The
next observation requires the Owner to approve and save the exact task fixture
and criteria sidecar as described in `owner-fixture-handoff.md`, then start a
new authenticated session in the authorized disposable workspace.

## Release

Archive: `dist/council-flow.zip`

SHA-256: `d371923a69e12a3aab47211bba8ada591dea901a651b47cac82f319c169cae57`

Entry count: 115; CRC, required/excluded contents, safe paths, source-byte
mapping, checksum, extracted tests, and package contract examples passed.

Gate 3 remains **NOT RUN**. No `COUNCILFLOW_FULLY_VERIFIED` claim is made.
