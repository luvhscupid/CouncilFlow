# ADR-001 Owner decisions and implementation authorization

Decisions by the Owner (cupid) in the CouncilFlow project thread on 2026-11-26.
Times are UTC. These answer the open questions found while planning the migration
to [ADR-001](ADR-001-adaptive-execution.md).

| ID | Question | Owner decision | When |
|---|---|---|---|
| D1 | Amend the Owner Charter? | Yes. Planner no longer talks to the Owner; Manager is the only gateway. Criteria are no longer frozen once; requirements may change through versioned ledger reassessment. | 05:15, confirmed 05:20 |
| D2 | Who writes Worker instructions? | The Planner writes them; the Manager assigns them. The Planner may recommend a model and reasoning level per task, based on task and risk (example: `model: Haiku 5.5, reasoning: medium`). The Manager assigns with the recommended model, or uses another if it is unavailable. | 05:15 |
| D3 | May the Planner research on its own? | Yes, read-only factual research (documents, web, repository reads), no edits. | 05:15 |
| D4 | Reviewer scope | The Reviewer adds an assessment of whether the delivered system meets the current Goal. The independent deterministic rerun stays mandatory. | 05:15 |
| D5 | Storage | Plain files are the permanent, authoritative record. Codebase Memory MCP is the recommended lookup layer over those files wherever it is available; lookups are confirmed against the files. Cloud sessions, where it is not available, use plain files only. No SQLite. | 05:15, settled 05:20 |
| D6 | Sequencing | Start after PR 21 merges. (PR 21 merged as b0a007f.) | 05:15 |

## Model recommendation (D2) and the per-role model split

The per-role model split approved on 2026-11-26 (in `docs/plans/lifegrid-findings.md`
on the lifegrid branch) is each role's default. A Planner recommendation refines it
per task. The Manager's order of choice: Planner recommendation, then role default,
then the host's inherited model. The Manager records which one it used and why.
The Reviewer never runs on Haiku, and the Planner does not choose its own model.

## Implementation authorization

Migration steps M0 to M8 are listed in the project's migration plan
(`plans/adaptive-execution-migration-plan.md` in the project files).

| Step | Scope | Status |
|---|---|---|
| M0 | Record ADR-001, these decisions and the Charter amendment (docs only) | Authorized 2026-11-26 06:51 |
| M1 to M8 | Project state files, Planner/Manager/Tester/Reviewer contract changes, dashboard view, validation | **Not authorized.** Each needs a separate Owner go-ahead. |
