# 02 — Preferred Council communication and policy contract

## Separation of formats

| Data | Format | Purpose |
|---|---|---|
| Task messages at CouncilFlow-controlled boundaries | UTF-8 JSON | Versioned, parseable assignments/reports; role-specific validation |
| Role/workflow/policy definitions | YAML | Human-readable, reviewable policy source |
| Codex native agent settings | TOML | Only supported Codex-native configuration keys; not a policy substitute |
| Optional debug/events | JSONL | One JSON event per line, no secrets; not a transactional database |
| Owner-facing | Concise natural language | Action, result, proof, blocker, decisions |
| Large code/test logs | Files with IDs/hash references | Avoid pasting huge logs into role chats |

These data formats are requested for the **CouncilFlow skill**. The recovered ACP-SPEC v0.1 describes a similar format but is marked PROPOSED / DESIGN ONLY; do not claim a fully frozen byte-for-byte v0.2.1 schema without the actual text.

## Skill-level envelope

See `examples/job.assign.json`, `examples/job.report.json`, and `examples/role-policy.yaml`. Minimum fields:

```json
{
  "protocol": "council-flow",
  "version": "1.0",
  "message_id": "M0001",
  "message_type": "job.assign",
  "plan_id": "P0001",
  "plan_revision": 1,
  "task_id": "T0001",
  "attempt_id": "A0001",
  "sender": {"role":"manager", "instance_id":"manager-main"},
  "recipient": {"role":"worker", "instance_id":"worker-001"},
  "in_reply_to": null,
  "payload": {"objective":"Implement task T0001", "scope":["demo/"], "acceptance_ids":["AC1"], "instructions":["Synthetic example only"]},
  "evidence_refs": []
}
```

**Illustrative** IDs/timestamps, not evidence of an actual run. Do not change the source ACP protocol number in archived source documents. This skill-level format is an adaptation where the full ACP Supervisor isn't present.

## Vocabulary

- `plan.publish`: Planner → Manager: task contracts and acceptance criteria.
- `job.assign`: Manager → Worker/Tester/Reviewer: scoped assignments.
- `job.report`: Worker/Tester/Reviewer → Manager: role-specific results, candidate/evidence references.
- `task.decision`: Manager → audit/Planner: accept, rework, discard, escalate, with evidence references.
- `plan.progress`: Manager → Planner: accepted/remaining acceptance IDs.
- `plan.check`: Planner → Manager: final sufficiency determination.
- `approval.request`: Manager → Owner: only consequential boundary decisions.
- `approval.decision`: Owner → Manager: actual owner-supplied decision, never invented.

## Validator requirements

Reject duplicate JSON keys; invalid UTF-8; NaN/Infinity; unknown versions; malformed/missing/extra fields; unsupported role/message combinations; incorrectly typed fields (including bool as int); oversized/deeply nested payloads; absent required IDs; impossible in-reply-to/plan/attempt references **when context is present**. Validate role-specific payloads, not just generic JSON. Do not treat the sender's self-described identity as authenticated. An instruction skill does not automatically control native agent transport, so distinguish validated skill-owned records from unaudited Codex internals.

## Evidence discipline

Worker's `completed` does not equal verified. Tester's tests must bind to candidate and approved criterion; Reviewer reports advisory usability, actual-vs-simulated. Planner's final check uses approved plan and evidence. No score alone authorizes acceptance.

## YAML and TOML

Keep roles and policy in YAML (illustrative file in examples); native agent configs in `.codex/agents/*.toml` because Codex may require TOML. Do not invent unsupported TOML keys or add dependencies just to parse YAML. If parsing YAML is required, use existing trusted parser or a limited documented subset; never claim to parse full YAML using a regex or unsafe eval.

## JSONL

Optional events should have structured type, task/attempt/candidate refs, UTC time and redacted detail. Treat this as diagnostics, not durable event-sourced security enforcement. Never write secrets, hidden prompts or chain-of-thought.
