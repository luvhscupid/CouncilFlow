# CouncilFlow Cloud Handoff

This branch is a development checkpoint, not a production release.

## Implementation status

The verified portable bundle supplies Planner v2 instructions and contract support, the Codex skill and role configuration, bootstrap and remote-update scripts, and dashboard/demo package resources. Five approved Claude/plugin/test overlays are included. Production Worker containment remains unresolved; native delegation shares the host filesystem and enforced isolation has not been verified.

## Checks run

- Verified `council-flow.zip` SHA-256: `ec870612570141f05963229df3f86345fb7a1e3a53011afdb9903da54e6941af`; all 219 archive members match the supplied manifest and extracted content hashes.
- The focused Python suite ran 125 tests: 118 passed, 5 failed, and 2 symlink tests were skipped because Windows denied symlink creation.
- `claude plugin validate plugins/councilflow` passed, with a non-blocking missing-icon warning.

## Known release-test failures

1. `test_current_release_contains_dashboard_sources_and_tests` fails because the inherited `dist/council-flow.zip` does not contain eight dashboard paths: `.agents/skills/council-flow/dashboard/{app.js,index.html,run-reader.js,styles.css}`, `.agents/skills/council-flow/scripts/dashboard.py`, and `demo/dashboard/tests/{auto-connection.test.cjs,run-reader.test.cjs,test_publisher.py}`. These source paths are present in the verified handoff bundle; the failing test reads the existing `dist` archive.
2. `test_release_and_ci_cover_the_documented_suites` has three failing subchecks because `.github/workflows/verify-portable-release.yml` does not invoke `demo/gate3-demo`, `python -m unittest discover -s demo/dashboard/tests -v`, or `node --test demo/dashboard/tests/run-reader.test.cjs demo/dashboard/tests/auto-connection.test.cjs`.
3. The same test method also fails its workflow path assertion for `demo/dashboard/tests/run-reader.test.cjs` (the workflow does not list that test path).

The contaminated worktree contains duplicate dashboard additions, but they were not copied from it: the verified bundle already supplies the dashboard sources and tests. Other contaminated routing, doctor, and experience additions were not included unless present in the verified bundle.

## Next investigation

Determine why the inherited `dist/council-flow.zip` differs from the verified bundle, then rebuild from the handoff tree and compare its file list and hashes with the verified manifest. Separately review whether the three documented demo commands belong in the release workflow and whether their suites are included. Keep the assertions intact while resolving any mismatch.

## Windows-specific verification

Cloud Linux cannot reproduce Windows PowerShell execution of `scripts/bootstrap.ps1` and `scripts/remote-update.ps1`, Windows symlink creation/fallback behavior, Task Scheduler registration semantics, or Codex/Claude discovery on the Windows host. The two skipped symlink tests require a Windows environment with symlink creation permitted.
