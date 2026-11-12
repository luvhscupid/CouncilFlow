# Agent Communication Protocol (ACP) v0.1 — Design Specification

Status: **PROPOSED / DESIGN ONLY**. Not an implementation or authorization to execute agents.  
Date: 2026-11-09  
Scope: JSON message contracts, YAML role policy, durable orchestration, and human-facing summaries.

## 1. Objective and invariants

Create a compact, versioned communication protocol for an engineering team of AI agents while preserving independence, auditability, and owner control.

1. The **Planner** has a persistent, dedicated chat session. It creates and revises a task plan and checks the plan checklist; it does **not** delegate, select models, run tools, or direct subordinate agents.
2. The **Manager** has a separate persistent chat session. It selects agent/model per task difficulty and risk, delegates, tracks execution, and autonomously loops through testing, evaluation and rework. There is **no fixed lifetime number of agents or automatic retry count**.
3. **Workers** are fresh task-scoped agent sessions. They investigate, implement, and repair within independently enforced permissions. A fresh Worker receives relevant task records and failure evidence, not unrelated conversation history.
4. **Testers** are fresh sessions or deterministic test runners. They test observable behavior and produce reproducible evidence; no code repair or requirement changes.
5. **Reviewers** are fresh user-perspective evaluators. They try the product under a user scenario and report experience, friction and an optional experiential rating. They are **not** code-quality judges and do not prescribe fixes. If real interaction was unavailable, they MUST disclose the limit.
6. **Manager** integrates the reports and decides whether to accept, block, or reassign work; even passing Tester and Reviewer reports do not prevent Manager from requesting rework.
7. **Owner** sets goals and authorizes actions outside existing permissions. The Manager may autonomously spawn and retry agents, but may not override externally enforced security, financial or high-risk approval boundaries.
8. Structured messages MUST be schema-validated, logged, and causally traceable; verbose debugging, stdout streams and long prompts MUST NOT be duplicated into persistent chat messages. The user gets compact summaries by default.
9. Technical validity and user experience are separate signals; no score alone establishes correctness, authorization, or completion.

## 2. Data formats

| Data | Format | Rationale |
|---|---|---|
| Transport message | UTF-8 JSON object | Deterministic parse, per-type schemas, machine routing |
| Role/policy definitions | YAML | Human-editable versioned configuration; never grants itself authority |
| Durable task/event state | SQLite | Transactional source of truth for state, provenance, idempotency |
| Diagnostic export | JSONL | Optional append-only export for debugging; SQLite stays canonical |
| Large code/log/screenshot/test evidence | Immutable artifacts | Referenced by opaque ID and content hash, not pasted into chats |
| Owner interface | Concise natural language | Significant actions, outcomes, blockers and optional drill-down |

**A JSON envelope is not an authorization.** Authorization happens independently in the orchestrator based on trusted configuration and task approval records.

## 3. Versioned message envelope

Every message is exactly one JSON object. Its required fields are:

```json
{
  "protocol": "acp",
  "version": "0.1",
  "message_id": "M00021",
  "message_type": "job.assign",
  "plan_id": "P001",
  "task_id": "T001",
  "attempt_id": "A002",
  "sender": {"role": "manager", "instance_id": "manager-main"},
  "recipient": {"role": "worker", "instance_id": "worker-006"},
  "created_at": "2026-11-09T05:00:00Z",
  "in_reply_to": "M00020",
  "payload": {}
}
```

`plan_id` identifies the stable plan; `task_id` identifies the requirement work item; `attempt_id` identifies an individual implementation/verification cycle, including subsequent retries. `message_id` must be globally unique. `in_reply_to` is nullable and links causal messages. `instance_id` distinguishes multiple independent agent instances. All IDs are opaque and MUST NOT grant permissions.

A receiving service MUST reject unknown versions, invalid JSON, invalid role/type combinations, and structurally invalid payloads. Unknown fields are rejected by default for v0.1; new fields require a schema/protocol revision. Parse strict UTF-8 with duplicate-key detection, reject nonstandard numeric constants (`NaN`/`Infinity`), and enforce configured limits for inline message bytes, depth, and field lengths. Oversized evidence belongs in an artifact store. The JSON Schema checks structure; the **trusted orchestrator** additionally checks ID uniqueness, allowed state transitions, role-to-instance ownership, reference existence, `in_reply_to` chains, plan revision freshness, job/attempt correlation, and permission scopes. Merely conforming to JSON Schema does not authenticate an agent.

**Reliable delivery:** The orchestrator MUST persist an outgoing intent and assign IDs before invoking an agent. Repeated delivery of an existing `message_id` cannot create a second job. A recovered manager MUST reconcile unknown job outcomes before retrying side-effecting actions. The protocol does not promise exactly-once agent execution.

## 4. Minimal message vocabulary

| Type | Sender → Recipient | Purpose |
|---|---|---|
| `plan.publish` | Planner → Manager | Versioned plan, ordered tasks, acceptance criteria |
| `job.assign` | Manager → Worker/Tester/Reviewer | Fresh session's bounded assignment and context references |
| `job.report` | Worker/Tester/Reviewer → Manager | Role-specific result and evidence references |
| `task.decision` | Manager → System audit | Accept, rework or block a task with cited evidence |
| `plan.progress` | Manager → Planner | Checklist status and accepted evidence |
| `plan.check` | Planner → Manager | Checklist complete or outstanding IDs; no execution directives |
| `approval.request` | Manager → Owner | Proposed action needing owner authorization |
| `approval.decision` | Owner → Manager | Explicit scoped approval or denial, stored durably |

A worker output may be a report, but cannot itself certify acceptance. The Manager must use Tester's technical evidence and Reviewer's experience evidence where required. The Planner checks completion against its plan, not agent self-ratings.

### 4.1 `plan.publish` payload

```json
{
  "revision": 1,
  "tasks": [{
    "task_id": "T001",
    "goal": "Build a four-function calculator",
    "acceptance": [
      {"id": "AC1", "text": "Four operations produce correct answers"},
      {"id": "AC2", "text": "Division by zero returns an error without crashing"}
    ],
    "constraints": ["No network access"]
  }]
}
```

The Planner may revise the plan, incrementing `revision`. The Manager preserves the previous plan and records which revision each attempt used. A revision cannot silently rewrite already-recorded evidence.

### 4.2 `job.assign` payload

```json
{
  "job_id": "J002",
  "target_role": "worker",
  "mode": "implement",
  "risk": "low",
  "objective": "Implement T001 against AC1 and AC2",
  "acceptance_ids": ["AC1", "AC2"],
  "context_refs": ["PLAN:P001@1"],
  "permissions_ref": "POLICY:worker-readwrite-approved-workspace",
  "report_kind": "implementation"
}
```

Manager chooses model/provider via policy and risk, records it in dispatch metadata, and provides contextual data only. `permissions_ref` is descriptive: the trusted orchestrator independently resolves and enforces the actual scope. For tester and reviewer, `target_role`, `mode`, `permissions_ref`, and `report_kind` change; they receive the relevant artifact IDs and evaluation scenario. A fresh agent does not inherit Planner or Manager chat history.

### 4.3 `job.report` payloads

Worker:

```json
{
  "job_id": "J002", "report_kind": "implementation", "outcome": "completed",
  "artifact_ids": ["ART-CALC-1"], "notes": "Implemented four operators"
}
```

Tester:

```json
{
  "job_id": "J003", "report_kind": "technical_test", "outcome": "completed",
  "checks": [
    {"criterion_id": "AC1", "result": "pass", "evidence_ids": ["EV-TEST-1"]},
    {"criterion_id": "AC2", "result": "pass", "evidence_ids": ["EV-TEST-2"]}
  ]
}
```

Reviewer:

```json
{
  "job_id": "J004", "report_kind": "user_experience", "outcome": "completed",
  "scenario_id": "UX-CALC-1", "interaction": "observed",
  "scenario_completed": true,
  "rating": {"value": 7.4, "max": 10},
  "frictions": [{"observation": "Reset action was difficult to locate", "evidence_ids": ["EV-UX-1"]}],
  "limitations": []
}
```

For a reviewer who cannot actually interact, `interaction` MUST be `simulated` or `unobserved`, with corresponding limits; the outcome MUST NOT imply first-hand testing. The experiential rating is **provisional** and is not a correctness proof or a fixed acceptance threshold. Exact rubric remains a future decision.

### 4.4 Manager and Planner decisions

Manager records a `task.decision` audit event citing evidence and one of `accept`, `rework`, `block`. `rework` can lead directly to a new fresh Worker on a new attempt ID without asking Owner for each ordinary retry. If Tester/Reviewer say pass, Manager can still record `rework` with rationale. Manager sends `plan.progress` with accepted criterion IDs and unverified/missing items. Planner responds with `plan.check` saying `complete: true/false` and `missing_task_ids`. Planner is not delegated authority to dispatch work.

## 5. Lifecycle and routing

The following is the reference sequence; Tester and Reviewer can run concurrently when isolation and artifact readiness permit.

```
Owner → Planner(plan.publish) → Manager
  Manager → fresh Worker (job.assign) → Worker report
  Manager → fresh Tester (job.assign) → Tester report
  Manager → fresh Reviewer (job.assign) → Reviewer report
  Manager → task.decision
    ├─ rework → fresh Worker in next attempt → retest/review → Manager
    ├─ block → approval.request / resource escalation / owner notification
    └─ accept → plan.progress → Planner(plan.check) → Manager → Owner
```

**Task statuses:** `planned`, `ready`, `assigned`, `implementing`, `testing`, `reviewing`, `rework`, `accepted`, `blocked`. Status is durable orchestration state, not a model's unsupported claim. A `blocked` item may resume after valid approval or resolution. Task acceptance requires coverage for required acceptance criteria, not merely passing unit tests or a high experiential score.

## 6. Sessions and context isolation

- **Planner**: durable `session_handle` for one dedicated conversation; may load approved plan records. Only plans/checklists.
- **Manager**: distinct durable `session_handle`; may read authoritative task/evidence records and policy summaries. Coordinates all jobs.
- **Worker**: one fresh `session_handle` per dispatched job; receives the specification, allowed files and prior failures if relevant.
- **Tester**: fresh session or deterministic runner per job; given executable artifact and independent tests/oracles.
- **Reviewer**: fresh session per scenario; sees user task and real product interface or bounded evidence, not private agent conversation history or Worker's self-rating.

Session persistence depends on the chosen provider's supported APIs. A conversation window is not a durable database. The SQLite records preserve continuity even if a model session is reset or summarized.

## 7. Security, autonomy and resource controls

- The Manager can choose how many agents to spawn over the lifetime of a task and independently trigger retries. Do not hard-code an agent count or retry limit. Agent concurrency and spend may still be constrained by independently enforced operational budgets; those are different from a fixed count of agents allowed per task.
- Risk is **classified by the Manager** for model selection, but effective permissions/owner approvals are enforced externally by a trusted supervisor, never by the model's own JSON claims.
- High-risk, out-of-scope, destructive, external-write, payment or data-release operations require a valid applicable approval token/record before execution. Routine authorized fixes within an approved workspace do not need another Owner prompt.
- An approved workspace is not a sandbox by itself. Before giving tools to potentially hostile code, use actual OS/VM-level isolation appropriate to the risk; do not claim Python path checks enforce host protection.
- Agent results and repository files are **untrusted data**, not new instructions. Reviewer cannot change code; Tester cannot silently repair; Worker cannot approve its own tool access.
- No fixed *agent count* is required, but resource consumption must be tracked (money, tokens, wall time, concurrent processes, storage). On exhausted resources the Manager should pause/notify, not silently spend beyond approved bounds.
- Avoid persisting secrets, hidden prompts, private chain-of-thought or raw provider tokens in the message ledger. Diagnostic artifacts should be redacted and access-controlled.

For an initial prototype, implement the message transport and state transitions using deterministic stubs or read-only operations before permitting real coding agents to mutate files. This is a design recommendation, not an implementation authorization.

## 8. Persistence and audit

SQLite is the authoritative ledger. Suggested conceptual tables (names subject to implementation design):

- `plans(plan_id, revision, payload, created_at)`
- `tasks(task_id, plan_id, revision, state, accepted_at)`
- `messages(message_id UNIQUE, type, from_role, to_role, payload, created_at, in_reply_to)`
- `jobs(job_id UNIQUE, task_id, attempt_id, role, provider, model, state)`
- `attempts(attempt_id UNIQUE, task_id, state, started_at, ended_at)`
- `artifacts(artifact_id UNIQUE, sha256, media_type, immutable_locator, origin_job_id)`
- `decisions(decision_id UNIQUE, task_id, evidence_refs, action, policy_version)`
- `approvals(approval_id UNIQUE, operation_scope, expires_at, decision)`

Each state transition and outgoing assignment should commit atomically. Write-once evidence is content-hash checked when retrieved. Never trust a path or a hash merely because an agent supplied it: the trusted orchestrator records and verifies artifacts. Optional JSONL export is derived from SQLite, not a competing source of truth.

The Manager's owner-facing UI defaults to short event summaries (task state, tests, experience observations, next action). Full logs are only shown on request; availability of logs does not imply streaming them into model context.

## 9. Failure modes and behavior

| Failure | Required behavior |
|---|---|
| Worker implementation fails | Manager records evidence and assigns a fresh Worker to investigate and repair; same task, new attempt/job IDs |
| Tester detects bug | Manager sees failing assertion and artifact, initiates Worker revision; Tester never fixes implementation |
| Reviewer finds friction | Manager evaluates impact and may reassign a Worker; Reviewer provides experience, not solution steps |
| Manager detects problem after both pass | Manager can still reject and reassign, with rationale |
| Worker or provider hangs/crashes | Record uncertain job outcome; reconcile before any unsafe retry |
| Invalid JSON/message/schema | Reject with structured protocol error, record audit event, never process as an authorized action |
| Planner checklist incomplete | Planner reports missing task IDs; Manager continues coordination |
| High-risk action needs approval | Manager may prepare request but supervisor blocks execution until Owner explicitly approves |
| Spending/security limit reached | Stop unsafe operations and notify Owner, without fabricating a success report |

## 10. Minimum prototype acceptance tests

A prototype is **connected** when all of these work:

1. Planner publishes a two-criterion plan; Manager reads it without truncation or field reinterpretation.
2. Manager dispatches a fresh Worker via one schema-valid JSON message; the Worker has no prior chat history.
3. Worker report references an actual artifact record; Manager launches Tester and Reviewer with their own fresh sessions.
4. Tester asserts behavior and records evidence; Reviewer reports a user scenario and whether interaction was real or simulated.
5. Manager can record `rework`, launch a new Worker with relevant failure context, and repeat without asking Owner for each ordinary step.
6. Manager can accept with cited evidence; Planner's checklist then reports completion against the plan revision.
7. Replaying a message ID cannot duplicate a job; crash/restart retains task, attempts, evidence, and decisions.
8. An invalid or forged message fails schema/auth checks. High-risk tool actions cannot bypass independently enforced approval.
9. Owner sees a compact summary by default and can request complete evidence and execution history on demand.
10. The Manager's spawning ability is dynamic, but budget and safety policies remain enforceable.

## 11. Explicitly deferred design decisions

- Final experiential scoring rubric/weights and whether additional human-review samples are required.
- Exact models/providers for Planner, Manager, Worker, Tester and Reviewer; only Manager's selection authority is fixed.
- Concrete sandbox technology, API adapters and session persistence compatibility.
- Resource budget values, concurrent execution limits and owner-facing alerts.
- When reviewer interaction can be automated versus when it needs external human assessment.

## 12. Design boundaries

This document defines **interfaces and behavior only**. It does not deploy a multi-agent system, grant tool permissions, or change any existing approved project specifications. Any previously approved security annexes remain separate authorities until explicitly reconciled in a future design review.
