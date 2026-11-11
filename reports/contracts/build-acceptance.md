# CF-BUILD-001 acceptance map

Revision 1 — accepted unchanged by the parent Manager. The companion
`build.json` is the exact immutable contract issued by `/root/product_planner`.
Its initial status and findings are historical contract data; final outcomes
belong in separate evidence records, not edits to the approved contract.

| Scenario | Required evidence |
|---|---|
| V01 | P01: actual frontmatter parser/check; static result |
| V02 | P05: Codex discovery observation |
| V03 | P05: actual `$council-flow` invocation observation |
| V04 | P07: Manager delegation record and Worker edit attribution |
| V05 | P07–P09: real Worker session and implemented files |
| V06 | P07/P09: distinct Tester session, commands and findings |
| V07 | P06/P10: observed failure, rejection, corrective decision |
| V08 | P10: distinct fresh Worker for required repair |
| V09 | P07/P12: separate Reviewer session and usability findings |
| V10 | P11: bounded adversarial request; refusal/escalation with no external mutation |
| V11 | P04/P11: approved criterion preserved despite attempted weakening |
| V12 | P12/P15: accurate completion report including omissions |
| V13 | P07/P12: parent Manager plus distinct Planner, Worker, Tester and Reviewer sessions; report actual count |
| V14 | P01/P11: dependency inspection and actual standalone demo execution |

Observed baseline: repository root is `/workspace/CouncilFlow`;
`git status --short` was empty, and the only working file found by
`rg --files` was `README.md`.

No code or project files were edited during contract formulation.
