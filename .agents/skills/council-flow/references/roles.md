# Roles and compact contracts

The Owner defines goals and authority. The parent Manager alone communicates
routine progress and final results to the Owner. Agent messages are internal
engineering results. Role instructions do not create OS isolation or grant
permissions; the host's actual sandbox and approval mechanisms govern.

| Role | Required work | Prohibited work |
| --- | --- | --- |
| Planner | Define deliverables, work units, dependencies, risks, and observable acceptance before implementation; final requirements-to-outcome check | Application code; lowering criteria; silent scope changes |
| Manager (parent) | Accept contract, choose supported resources/skills, delegate, track evidence/open findings, decide rework/disposition, report | Application code; self-certification from a Worker's claim; changing mandatory criteria |
| Worker (fresh attempt) | Bounded implementation, necessary project files, developer checks, changed-file/result report | Self-approval; scope expansion; permissions on Manager's behalf; criterion weakening |
| Tester (fresh separate agent) | Independently inspect and run behavior/tests; negative controls in an assigned test area where useful; report observed gaps | Implementation repairs; treating Worker tests alone as proof |
| Reviewer (fresh separate agent) | First-use instructions and experience, relevant actual interaction, confusing/missing/unfinished behavior, evidence-backed findings | Code edits; presenting inspection or simulated behavior as actual interaction |

Use an actual separate native session for each required subagent role. Reuse the
Planner for final check; Worker rework uses a fresh session. Tester and Reviewer
are not the Worker or the Manager under a new label. The Manager counts as the
fifth distinct role session. Report actual IDs made available by the host; do not
invent opaque identifiers, model usage, or costs.

## Shared envelope

Use compact JSON or equivalent structured records. Every request/result carries
these fields; use `[]` for no findings and a clear status rather than omissions:

```json
{
  "type": "WorkerRequest",
  "task_id": "T001",
  "role": "Worker",
  "contract_ref": "reports/T001/contract.json",
  "objective": "Complete the approved local feature",
  "scope": ["authorized/project/path/**"],
  "requirements": ["R1"],
  "acceptance": ["A1: observable mandatory behavior"],
  "constraints": ["No unauthorized changes"],
  "implementation_status": "ASSIGNED",
  "evidence": [],
  "open_findings": [],
  "repair_decisions": [],
  "final_disposition": "PENDING"
}
```

The initial Planner request may use `contract_ref: null`; its result creates the
contract. Results add `request_ref`, actual available `agent_id`, changed files,
and command/output references as appropriate. Copy the original acceptance IDs
unchanged; append findings instead of editing criteria. Store the original
contract once; optionally record a standard SHA-256 digest to detect drift.
Owner-approved amendments are new versions with explicit provenance, never
silent replacement.

## Separate request/result types

| Request type → Result type | Required additional content |
| --- | --- |
| PlannerRequest → PlannerResult | Goal, plan mode/provenance → bounded units, dependencies, risks, immutable contract and acceptance IDs. At final check, `phase: final` plus evidence map and unmet IDs |
| ManagerRequest → ManagerResult | Owner request and approved authority → delegation decisions, role IDs, unfinished criteria, accepted/rejected findings, disposition |
| WorkerRequest → WorkerResult | Bounded files/work unit, unchanged acceptance, attempt identity → actual changed files, developer commands/results, limitations; never approval |
| TesterRequest → TesterResult | Contract and produced artifacts, isolated test scope → acceptance-by-acceptance observations, commands/exits, failures, edge cases, unverified behavior; no repairs |
| ReviewerRequest → ReviewerResult | Intended user, instructions, relevant interaction → actual interaction versus inspection, usability findings/severity, optional stated scoring rubric; no edits |

These are record types, not an orchestration API. Use the host's real native
delegation tool and supported arguments after inspecting them. If custom agents
are supported, select `council-planner`, `council-worker`, `council-tester`, or
`council-reviewer`; otherwise pass that role's instructions to a native subagent
and disclose that custom-role-file loading itself was not verified.
