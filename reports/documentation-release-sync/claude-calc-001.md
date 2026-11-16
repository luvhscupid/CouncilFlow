# Claude Code calc-001: recorded Windows-local smoke evidence

One real `/councilflow:run` smoke test completed **VERIFIED_ACCEPT**.
Existing host records show plugin Agent invocations for native Planner, Worker,
Tester and Reviewer, with separate subagent session logs. The parent host log
records sequence validation `valid: true`, `mode: sequence`, `files: 11`.
The persisted Manager decision M016 accepts the candidate; final Planner M017
passes AC1-AC3. Reviewer M015 records an independent V1 rerun MATCH (exit 0,
LF-normalized stdout SHA-256
`f0b5c2c2211c8d67ed15e75e656c7862d086e9245420892a7de62cd9ec582a06`).
The saved Tester and Reviewer stdout bytes were compared during this inspection.
Earlier rejected/corrected packets remain preserved; 11 is the validated final
sequence length, not the count of all attempted message files.

Limits: Reviewer reran V1 only. The Worker-authored test oracle was not approved
by the Tester or Reviewer. Negative-control observations outside the frozen
acceptance are not universal compatibility evidence. Upstream model identity,
effective route, cost and quota remain unknown. This run does not verify live
Agent Efficiency adapters or billing compatibility. No experiment, application
or model execution was repeated for this summary.

Sources: sibling checkout `CouncilFlow-Claude-Smoke-01`,
`.councilflow/runs/calc-001/`; existing local Claude host logs (private, excluded).
The supplied source path omitted the separator before `.councilflow`.
Selected inspected artifact SHA-256 values:
- `messages/M015.json`: `547db63c2f0cdd4ccf211492438c95e345b2c8007733b2d0b14a220741b78b94`
- `messages/M016.json`: `42150303f4567e3f4b47ba2032177327398d69e3afdf84c60c264aa41f92edb1`
- `messages/M017.json`: `98672a8873b070cbb9908944697f314f6d486c7240b335859f0ecb1dfb86da9c`
