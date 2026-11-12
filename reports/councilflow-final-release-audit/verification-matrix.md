# Current verification matrix

Windows columns are independent Tester executions. Linux is a separately approved Manager supplemental run on the exact final archive in native /tmp; it is not Tester-thread proof. All command exits below are zero. Counts are run / passed / skipped.

| Suite (`python -m unittest discover -s DIR -v`) | Windows checkout | Windows final extraction | Linux final extraction |
|---|---:|---:|---:|
| tests | 104 / 100 / 4 | 104 / 101 / 3 | 104 / 104 / 0 |
| demo/receipt | 13 / 13 / 0 | 13 / 13 / 0 | 13 / 13 / 0 |
| demo/csv-summary | 15 / 15 / 0 | 15 / 15 / 0 | 15 / 15 / 0 |
| demo/structured-flow | 5 / 5 / 0 | 5 / 5 / 0 | 5 / 5 / 0 |
| reports/demo/verification | 5 / 5 / 0 | 5 / 5 / 0 | 5 / 5 / 0 |
| reports/csv-summary/verification | 6 / 6 / 0 | 6 / 6 / 0 | 6 / 6 / 0 |
| Total | 148 / 144 / 4 | 148 / 145 / 3 | 148 / 148 / 0 |

Windows skips: two original symlink controls need privilege; checkout hardlink control gets WinError5 on E:; directory-link control cannot create symlink/junction in sandbox. Hardlink control actually ran in C: extraction. Native Linux /tmp executed all four link tests. Separately approved Windows junction controls passed inside correct-hash allow, stale-hash reject and outside-root reject. Skips are not security passes and these observations do not establish OS isolation or TOCTOU freedom.

65 supplemental synthetic controls: 63 satisfied, two Windows symlink skips, zero failures. Twelve valid executable mutants killed by relevant regressions; none survived, invalid or skipped. Root-bound JSON examples2 and policy passed. Historical failing suites remain separate as recorded in distribution-audit/historical-suite-results.json.

Exact executable, arguments, working directories, raw stdout/stderr and input hashes are in verification-matrix.json and the immutable Tester execution records. Final archive has117 entries; every CRC/name/source/extracted byte verified.
