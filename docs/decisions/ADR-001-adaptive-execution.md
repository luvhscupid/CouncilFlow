# ADR-001: Adaptive Execution, Authority Separation, and Versioned Project State

Record status: ACCEPTED by the Owner on 2026-11-26. Implementation is authorized
only step by step; see [ADR-001 Owner decisions](ADR-001-owner-decisions.md).

Source: the Owner's message in the CouncilFlow project thread "Plan move to
adaptive execution", sent 2026-11-26T05:02:10Z. The text below reproduces that
message's record. Its tab-separated tables are shown as Markdown tables;
the wording is unchanged.

---

CouncilFlow Architecture Decision Record

Title: Adaptive Execution, Authority Separation, and Versioned Project State
Status: ACCEPTED
Decision date: 26 November 2026
Decision authority: Owner
Implementation status: Not authorized
Default autonomy budget: 5 active unconfirmed decisions
Owner-readable ledger: Generated read-only view

⸻

## 1. Decision summary

CouncilFlow will adopt an adaptive execution architecture.

Tasks do not require a complete, frozen specification before execution. Discovery may continue as new evidence emerges, and requirements may evolve through controlled reassessment.

However, adaptive execution must not create ambiguous authority or multiple competing sources of truth.

CouncilFlow will maintain three distinct project domains:

1. Ledger: What is currently understood, required, assumed, and decided.
2. Plan: What work is being performed, by whom, and in what order.
3. Evidence: What agents have observed, discovered, and verified.

Each domain has one authoritative owner.

The architecture preserves the Owner's final authority while allowing independent work to continue wherever unresolved decisions do not create unacceptable risk.

## 2. Organizational structure and authority

### Executive Office

Executive Director — Owner

The final authority.

Responsibilities:

* Define and change project objectives.
* Approve consequential scope, cost, timeline, and risk decisions.
* Resolve decisions outside delegated authority.
* Inspect the current project state.
* Set and change autonomy limits.
* Provide final acceptance.

### Strategic Planning Division

Chief Strategy Officer — Planner

The sole semantic owner and writer of the requirements ledger.

Responsibilities:

* Conduct iterative discovery.
* Apply Grill Me and Grill With Docs-inspired techniques.
* Identify unknowns and challenge assumptions.
* Research factual questions independently.
* Maintain requirements, assumptions, constraints, decisions, and open items.
* Establish permitted provisional defaults.
* Assess slice readiness.
* Reassess requirements when valid evidence or instructions warrant it.

The Planner does not communicate directly with the Owner.

### Operations and Delivery Division

Chief Operations Officer — Manager

The sole owner of the execution plan.

Responsibilities:

* Decompose work into slices.
* Assign agents and select models.
* Manage sequencing and dependencies.
* Enforce readiness and approval boundaries.
* Coordinate execution and reassessment.
* Operate the Owner communication gateway.
* Reconcile execution plans against new ledger versions.

The Manager cannot modify requirements or override Owner-controlled decisions.

### Engineering and Quality Division

Software Engineer

* Implements assigned work.
* Makes ordinary technical decisions within delegated authority.
* Reports evidence and technical constraints.
* Does not silently promote assumptions into requirements.

QA Engineer

* Tests implementation against applicable ledger entries.
* Maintains test-to-requirement traceability.
* Identifies stale test results after relevant changes.

### Independent Audit Division

Technical Audit Director

* Independently assesses implementation quality.
* Evaluates whether the delivered system satisfies the current project goal.
* Identifies gaps and risks.
* Does not modify requirements or approve Owner-controlled decisions.

## 3. Authoritative project state

### 3.1 Requirements ledger

The Planner is the sole semantic writer.

The ledger is append-only and versioned. Changes create new versions rather than silently overwriting historical decisions.

Supported entry types:

| Type | Meaning |
|---|---|
| Goal | Intended project outcome |
| Requirement | Established behavioral or product requirement |
| Assumption | Provisional interpretation or default |
| Constraint | Restriction from the Owner or established evidence |
| Decision | Authoritative choice and its source |
| Open | Unresolved question and its consequences |

Every entry must support traceability through:

* Unique ID
* Type and content
* Source or evidence IDs
* Status
* Timestamp
* Version introduced
* Superseded entry IDs
* Affected slices

An Assumption never becomes a Requirement silently. Promotion requires Owner confirmation or an explicit pre-approved delegation rule.

### 3.2 Execution plan

The Manager is the sole owner.

The plan records:

* Slices and dependencies
* Assignments
* Model routing
* Execution status
* Sequencing
* Operational decisions
* Ledger version pinned to each slice

A plan change does not automatically modify the ledger.

If a plan conflicts with the ledger, the Manager must request reassessment rather than silently changing requirements.

### 3.3 Evidence

Evidence is recorded independently.

Each record includes:

* Source agent
* Observation or finding
* Supporting artifacts
* Relevant ledger IDs
* Affected slices
* Timestamp
* Reopen Request status

Evidence changes understanding of reality. It does not independently authorize a requirement or decision change.

Hard invariant: Evidence changes our understanding of reality, but only the appropriate authority changes a decision or requirement.

## 4. Owner communication and source preservation

Only the Manager may conduct conversational exchanges with the Owner.

The controller must preserve the Owner's original messages before any agent processes them.

Each message receives an immutable source ID and timestamp.

Agents reference the original record instead of treating summaries as authoritative sources.

Planner question packets contain:

* Question ID
* Exact Owner-facing wording
* Blocking status
* Reversibility classification
* Affected slices
* Permitted default, if applicable
* Reason for asking

The Manager forwards the exact question text.

Owner responses are stored as immutable source records. Planner interpretations remain separate from original responses.

Where supported, the controller validates outbound question text against its stored source packet.

If the underlying execution environment cannot guarantee exact preservation or validation, this limitation must be explicitly documented. Prompt instructions alone do not constitute a transport guarantee.

### Owner-readable project state

The Owner receives a generated, read-only project view.

It exposes:

* Current project goal
* Confirmed requirements
* Provisional assumptions
* Open questions
* Decision history
* Current ledger version
* Slice readiness and execution status
* QA results and audit findings
* Unconfirmed default budget usage

The generated view is not an alternative source of truth. The authoritative ledger remains the underlying record.

A read-only document does not violate the Manager-only conversational boundary.

## 5. Decision authority and autonomy

| Decision class | Authority | Owner unavailable |
|---|---|---|
| Reversible and cheap to revisit | Planner may establish a provisional default | Proceed provisionally |
| Reversible but costly to revisit | Owner approval | Pause affected slice |
| Irreversible or external | Owner approval | Block |
| Security, data integrity, financial or legal | Owner approval | Block |
| Owner-controlled objectives | Owner only | Block |

Examples of cheap, reversible decisions include naming and minor UI defaults.

Examples of costly decisions include database schema choices and major library selections.

Examples of blocking decisions include deleting data, publishing, spending money, external communications, security-boundary changes, and decisions affecting financial or legal obligations.

The Planner may classify a decision within its permitted class but cannot downgrade a decision belonging to a blocking class.

The Manager enforces these boundaries and cannot override them.

### 5.1 Default budget

Owner-approved limit: 5 active unconfirmed decisions per project.

An active unconfirmed decision is a Planner-established provisional default that has not yet received Owner confirmation or rejection.

The budget is shared across the project.

A decision stops consuming budget once confirmed or rejected.

When the budget is exhausted:

* New slices requiring additional unconfirmed defaults pause.
* Existing work that does not depend on additional defaults may continue.
* Blocking decisions remain blocked regardless of remaining budget.

The Owner may change the budget at any time, including setting it to zero.

An unanswered question does not mean approval.

## 6. Discovery and readiness

The Planner is invoked when needed, not kept resident throughout execution.

Invocation triggers:

1. Project intake.
2. Slice readiness assessment.
3. Valid Reopen Request.
4. Owner instruction superseding a Requirement or changing the Goal.

### Readiness states

READY

All required conditions are satisfied. Work can begin.

PROCEED_WITH_ASSUMPTIONS

Remaining uncertainty is covered by permitted, documented provisional defaults. The default budget permits execution, and no blocking decision applies.

BLOCKED

A required approval, critical fact, or decision is missing, or an applicable blocking condition exists.

### Discovery limits

Each slice receives at most two Planner discovery cycles before unresolved readiness escalates to the Owner as a scope question.

The Planner should:

* Research factual unknowns independently.
* Batch independent questions.
* Ask dependent questions sequentially.
* Avoid repeating already resolved questions.
* Prioritize decisions based on consequence and reversibility.

The entire project does not need to be understood before its first slice begins.

## 7. Reopen Requests and event serialization

Any agent may submit evidence and request reassessment.

A valid Reopen Request must:

* Cite at least one ledger entry ID.
* Identify a contradiction or affected assumption.
* Include supporting evidence.
* Identify affected slices.
* Explain the potential consequence.

A request without a ledger reference is not valid for reopening, though the observation may be retained as evidence.

Submitting a request does not modify the ledger.

The Planner decides whether the evidence warrants a ledger change.

The Manager reconciles the execution plan after a new ledger version is published.

### Event ordering

The controller processes events sequentially and records their processing order.

The existing Python/SQLite approach should be preferred if it supports the required transactional behavior.

No message broker or additional infrastructure is required by default.

## 8. Adaptive execution lifecycle

1. Intake: Planner establishes the initial goal, requirements, assumptions, constraints, and open items.
2. Slice planning: Manager proposes execution slices.
3. Readiness: Planner evaluates each slice independently.
4. Execution: Manager delegates work against a pinned ledger version.
5. Evidence collection: Agents record findings and submit valid Reopen Requests.
6. Reassessment: Planner evaluates evidence and updates the ledger when justified.
7. Reconciliation: Manager updates affected plans and pauses only affected work.
8. Verification: QA tests against the applicable ledger version.
9. Audit: Technical Audit evaluates implementation quality and project outcomes.
10. Delivery: Manager presents results and unresolved matters to the Owner for final acceptance.

Unrelated slices may continue while another slice is blocked or undergoing reassessment.

## 9. QA and audit traceability

Every QA test must record:

* Test ID
* Tested behavior
* Ledger IDs covered
* Slice ID
* Pinned ledger version
* Test result
* Supporting evidence or execution artifact
* Timestamp

A QA pass certifies only the tested behavior against its recorded dependencies and ledger version.

When the ledger changes:

* Tests affected by changed entries become stale.
* Tests with unaffected dependencies retain their results.
* Required retesting is limited to affected verification scope.

Technical Audit independently evaluates whether the delivered system satisfies the current Goal.

The Goal is versioned. An Owner-approved goal change triggers reassessment of affected slices and verification work.

## 10. Disagreement resolution

* Evidence determines factual questions about observed system behavior.
* Owner decisions determine Owner-controlled requirements and objectives.
* Planner determines requirements-ledger interpretation within delegated authority.
* Manager determines execution sequencing and operational coordination.

If Planner and Manager disagree about plan compliance, the Manager raises the conflict rather than changing the ledger.

If an Owner-controlled decision is required, the affected slice pauses and the Manager presents the decision to the Owner.

Unaffected work continues.

## 11. Explicit non-goals

The architecture does not require:

* A continuously resident Planner.
* A complete specification before implementation.
* Owner approval for ordinary engineering decisions.
* Automatic promotion of assumptions.
* Silent changes to requirements.
* Unbounded discovery loops.
* Additional agents for every decision.
* A message broker by default.
* Approval gates for unrelated work.
* Direct conversational communication between Planner and Owner.

## 12. Implementation authorization

This architecture decision is accepted.

However, acceptance does not authorize implementation.

Before implementation:

1. Inspect the current CouncilFlow repository and protocol.
2. Inspect the existing Python/SQLite design, including the Council Meeting 001 specification.
3. Identify conflicts between existing behavior and this decision record.
4. Produce a minimal migration plan.
5. Preserve existing working behavior unless a specific architectural conflict is demonstrated.
6. Obtain separate Owner authorization before modifying the repository.

No code changes, migrations, new infrastructure, or implementation work are authorized by this record.

⸻

Final decision: CouncilFlow adopts adaptive execution with a single requirements ledger owner, a separate execution-plan owner, independent evidence records, bounded discovery, controlled autonomy, and versioned verification.

Owner approval: Accepted
Implementation approval: Pending separate authorization
