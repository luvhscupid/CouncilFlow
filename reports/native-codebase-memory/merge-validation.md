# Final merge validation

Authorized target: `main`, from `codex/cf-recall` in
`E:\Saint\PROJECTS\CouncilFlow-cf-recall`.
Inspected remote/local base: `1bed72b79b3e91c206b7274db064256797b76ec2`.
Earlier reports describe their original execution stages; the initial MCP
failure and later restoration remain distinct historical observations.

## Snapshot Vault integration test

The Owner reported the following completed test observations on 2026-11-12:

- Automatic MCP tool selection observed.
- Independent agent workflow observed.
- AC07 and AC12 remain **UNVERIFIED**.
- Graph coverage was unavailable for the tested Snapshot Vault paths.

This records the Owner's supplied results, not a new independent rerun or
inspection of Snapshot Vault. No Snapshot Vault project files were accessed or
modified as part of this merge. These observations do not establish that all
CouncilFlow or Snapshot Vault acceptance gates are fully verified. Existing
frozen acceptance criteria and historical release classifications are preserved.

## Merge checks

The complete current root and finished-demo regression suites, deterministic
policy validation, candidate identity comparison, custom-recall removal,
protected-file comparison, and source inclusion checks are recorded in
`merge-regression.json`. The deliberate incomplete starter fixture remains
covered by the existing static test, not claimed as a finished passing app.

Only the reviewed CouncilFlow skill, workflow/reference, README, integration
test, and engineering evidence are included. The generated local
`cf-recall-review.patch`, credentials, runtime caches, global MCP configuration,
installed executables, and Snapshot Vault modifications are excluded.

The final remote main identity is checked again before the ordinary non-forced
push. A conflict, failed regression, unexpected change, or changed remote base
blocks the merge/push instead of being overridden.
