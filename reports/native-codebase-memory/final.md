# Native Codebase Memory integration review

Date: 2026-11-12 (Asia/Bangkok).
Repository: `luvhscupid/CouncilFlow`, working directory
`E:\Saint\PROJECTS\CouncilFlow-cf-recall`, branch `codex/cf-recall`.
Base/HEAD: `1bed72b79b3e91c206b7274db064256797b76ec2`.
Changes remain uncommitted; no push or merge was performed.

## Implementation

The existing CouncilFlow instruction skill now directs Manager to run the
native Codebase Memory lifecycle before Planner and after implementation/rework
once Worker stops editing. It uses exposed MCP capabilities directly, without
a custom memory engine or a separate Owner command.

Changed product/documentation files:

- `.agents/skills/council-flow/SKILL.md`: mandatory automatic lifecycle pointer.
- `.agents/skills/council-flow/references/workflow.md`: pre-Planner acquisition
  and post-Worker synchronization within the existing role sequence.
- `.agents/skills/council-flow/references/codebase-memory.md`: local empty-project
  gate, exact repository identity, first index, freshness, bounded graph context,
  coverage/source fallback, fresh-agent handoff, and resulting-source updates.
- `README.md`: ordinary invocation and complete-folder installation guidance.
- `tests/test_codebase_memory_integration.py`: nine static instruction/removal
  checks; these do not simulate or certify live MCP execution.

Removed the prior untracked custom assets: `.agents/skills/cf-recall/`,
`scripts/recall.py`, `references/recall.md` within the CouncilFlow skill,
`tests/test_recall.py`, and their specifically identified recall bytecode.
No custom recall manifest existed. The tracked `.codex-runtime/` ignore entry
predates recall and was preserved. Removed untracked assets do not appear as
deletions in a patch against HEAD because they were never committed.

The schema, validator, role policy, native TOMLs, frozen Gate 3 and full-plan
documents, historical release classifications, original contract tests, and
validation scenarios are unchanged. Index findings remain navigation evidence;
independent Tester, Reviewer rerun, and final Planner acceptance remain required.

## Availability actually observed

- This session's tool inventory exposes no Codebase Memory graph/index tools.
- `codex mcp list --json` reports `codebase-memory-mcp` enabled. Its reported
  authentication status is `unsupported`; that is not an authentication failure.
- `list_mcp_resources({server: "codebase-memory-mcp"})` and
  `list_mcp_resource_templates({server: "codebase-memory-mcp"})` each failed at
  startup: `MCP startup failed: handshaking with MCP server failed: connection
  closed: initialize response`.
- No project listing, index status, graph query, indexing, or coverage operation
  succeeded. No server installation, replacement, configuration change, or
  permission bypass was attempted. Direct source inspection supported this work.

Live automatic MCP use is **UNVERIFIED**. The reference uses tool names only as
conditional examples when those tools are exposed, and requires reading their
actual input/output schemas. A configured server alone is insufficient evidence.

## Independent verification

The execution record is [verification.json](verification.json). All commands
used `C:\Users\cupid\AppData\Local\Programs\Python\Python312\python.exe`
from the working directory above. Every listed suite exited 0 with zero skips:

| Command arguments | Methods |
| --- | ---: |
| `-m unittest discover -s tests -p test_codebase_memory_integration.py -v` | 9 |
| `-m unittest discover -s tests -v` | 80 |
| `-m unittest discover -s demo/receipt -v` | 12 |
| `-m unittest discover -s demo/csv-summary -v` | 15 |
| `-m unittest discover -s demo/structured-flow -v` | 4 |

The focused nine tests are included in the 80 root tests: 111 distinct methods
passed across root and current demo suites. The deliberately incomplete starter
fixture was checked by the existing root static test; it was not represented as
a passing application. `git diff --check` and protected-file comparisons passed.

Independent review found an initially ambiguous parent-index identity rule.
A fresh repair Worker required exact resolved repository-root equality and
strengthened the regression check. The Tester reran focused/full suites on the
corrected candidate, preserving earlier runs under `pre_correction`; demo and
policy checks retain their actual executions with unchanged input hashes.
Final candidate hashes remained unchanged during independent checks.

Reviewer independently reran the Tester's exact policy command and compared
exit 0 and CRLF-to-LF-only normalized stdout SHA-256:
`e00d2405ad16b1c98fe682dbb1308d86f9bb86c5a475c71371f9e969ccb018a7`.
See [review.json](review.json) for the separate review evidence.

## Acceptance limits and export

Static checks cover all requested lifecycle branches: empty/installation-only
zero-call gate, missing index, indexed context, changed-source freshness/update,
missing/unreachable MCP fallback, bounded fresh-agent context, preserved
verification/authority, and installation documentation. Actual automatic graph
execution for those branches remains UNVERIFIED because initialization failed.
No new native `$council-flow` activation or full controlled five-role workflow
run is claimed by these engineering checks.

`cf-recall-review.patch` is regenerated against HEAD with all final tracked and
untracked product, test, and evidence files, excluding the export itself. It
replaces the earlier custom recall review export. Review the patch before any
separately authorized commit, push, or merge.
