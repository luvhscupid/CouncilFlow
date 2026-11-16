# Roles and JSON contracts

The Owner is the human authority. Parent Manager alone gives routine progress and
results to Owner. Role policy is versioned YAML at ../policies/roles.yaml;
[communication.md](communication.md) defines the closed JSON task contract.
All CouncilFlow-controlled task packets and role results MUST be UTF-8 JSON;
ordinary Markdown role prose is not an equivalent message format.

| Role | Required work | Prohibited work |
|---|---|---|
| Planner | Publish original objective, scope, dependencies and acceptance; final original-objective check | Application code, hidden scope changes or lower criteria |
| Manager | Parent coordinator, supported skill/model choice, delegation, evidence evaluation and authorized rework | Application code, accepting Worker assertion as verification, silent acceptance weakening |
| Worker | Fresh bounded implementation attempt and developer checks, changed-file/candidate report | Self-approval, permissions on Manager's behalf, scope expansion |
| Tester | Fresh separate technical verification of exact candidate and original acceptance | Product repairs, self-approval of its oracle, treating Worker tests alone as proof |
| Reviewer | Independently compares frozen plan/criteria, Worker candidate and Tester evidence; reruns one declared deterministic command and reports discrepancies to Manager | Implementation, criteria changes, UX scoring, replacing Tester |

Manager approves the verification strategy/oracle provenance in the original
plan or assignment; Tester may propose or write isolated negative controls but
cannot authoritatively approve its own oracle. Owner decides consequential new
scope/authorization and required subjective acceptance. No role wording grants
OS isolation or native permission authority.

## Separate request/result purposes

These human labels identify responsibilities, not extra wire message types:

| Responsibility labels | Actual JSON purposes |
|---|---|
| PlannerRequest / PlannerResult | Manager plan.progress → Planner plan.publish; final plan.check |
| ManagerRequest / ManagerResult | Owner goal → Manager controlled assignments, task.decision and plan.progress; Owner result is prose |
| WorkerRequest / WorkerResult | Manager job.assign → Worker job.report with changed_files |
| TesterRequest / TesterResult | Manager job.assign → Tester job.report with checks, deterministic command records and exact candidate |
| ReviewerRequest / ReviewerResult | Manager job.assign → Reviewer job.report comparing frozen plan, candidate, Tester evidence and independent command rerun |

The shared envelope carries task_id, plan_id/revision, attempt_id, message_id,
sender/recipient roles and instance IDs, in_reply_to, payload and
evidence_refs. Payload objective, scope and acceptance_ids preserve the immutable
plan. Conceptual legacy terms map explicitly: implementation_status to status,
evidence to evidence_refs, open_findings to findings, repair_decisions to
task.decision, final_disposition to disposition. They are not alternative JSON
fields. Unknown fields fail validation.

Use an actual separate native session for each required role; reuse Planner for
final check. Rework Worker is fresh. Report only actual exposed session/task-path
IDs and inherited supported model selection. Separate contexts do not establish
separate model providers or OS-enforced boundaries. Custom-agent files remain
.codex/agents/*.toml (the native directory is .codex/agents/); use their compatible
developer_instructions mapping from policy, or pass role instructions through
native delegation if custom-role selection is not exposed.

External Planner mode preserves the actual Owner-approved input and provenance;
it must not claim an external ChatGPT conversation was invoked. Native Planner
mode requires no external integration.
