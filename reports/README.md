# CouncilFlow reports

Current recorded host outcomes:
[Gate 3 Run 01](documentation-release-sync/gate3-run-01.md) and
[Claude calc-001](documentation-release-sync/claude-calc-001.md).
Their limitations remain unchanged. `documentation-release-sync/package-verification.json` (outside the ZIP)
describes its earlier package. `repository-cleanup/verification.json` (outside the ZIP)
records this maintenance and the rebuilt package.

`demo/verification` and `csv-summary/verification` are maintained executable checks.
`gate3b`, `activation`, `environment`, `native-codebase-memory`, root historical
summaries and other small collections retain their provenance. Uncertain records
were kept. Frozen architecture and Owner records remain under `docs/`.

## Historical collections

The independent local archive is `E:/Saint/BACKUPS/CouncilFlow-Archive`.
It has no remote. `ARCHIVE-MANIFEST.json` maps original repository-relative paths
to exact sizes, SHA-256 values, original Git blobs and the source commit.
`INVENTORY.json` holds the full original inventory and references. Look up an
experiment by its original `reports/<collection>/` path. Each pointer below names
an original outcome record, its hash and the verified archival commit.

| Collection | Historical conclusion |
| --- | --- |
| [councilflow-hardening](councilflow-hardening/README.md) | PARTIAL; formal Gate 3 not run. |
| [councilflow-final-release-audit](councilflow-final-release-audit/README.md) | Controlled-use software audit; native Gate 3 and host limits remain separate. |
| [engineering-recovery](engineering-recovery/README.md) | Local source-fidelity/recovery repairs verified; formal native activation not certified. |
| [councilflow-finalization](councilflow-finalization/README.md) | Consolidation complete; separately governed Gate 3 observation not executed. |
| [package-check-verified](package-check-verified/README.md) | Historical extracted release snapshot, not current installation source. |
| [integration-gate3-efficiency](integration-gate3-efficiency/README.md) | Historical integration Planner check passed; no live adapter/billing certification. |
| [restoration](restoration/README.md) | CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED; recorded invocation hit HTTP 401. |
| [reliability-repair](reliability-repair/README.md) | Engineering repair verified; native workflow unverified at that checkpoint. |
| [gate3-next](gate3-next/README.md) | Preparation drafts/disposable workspaces; no executed Gate 3 result inferred. |
| [gate3-preflight-2026-11-12](gate3-preflight-2026-11-12/README.md) | BLOCKED_WITH_EXACT_PREREQUISITES; preparation only, Gate 3 NOT RUN. |
| [councilflow-e10](councilflow-e10/README.md) | Historical remediation; Gate 3 NOT RUN, E1/E2/E4 host evidence UNVERIFIED. |

The archive includes the entire original reports tree to preserve internal
relationships; copies of retained main records are context snapshots, not
removal instructions. The cleanup ledger records any later classification override.
The complete working-directory backup and all-refs bundle are outside this
repository; their verified location is recorded in the cleanup verification.
Historical Git objects remain in existing history. Checkout reduction is not
Git history compaction or a GitHub compressed-size measurement.
