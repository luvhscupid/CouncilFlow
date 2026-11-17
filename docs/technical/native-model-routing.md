# Native model routing: experimental data contract

## Purpose and limits

`experiments/native-model-routing/routing.py` validates declared policy and
identity data deterministically. It is not a trusted Supervisor, dispatch
service, credential store, security boundary, or OS sandbox. The checked-in
policy intentionally authorizes no routes. No model pool, entitlement,
qualification, price or credential is inferred from a model name or a host tool.

## Identity and qualification

An exact identity is the tuple `(provider, route_id, model_id, harness)`. Records
keep four observations separate: configured identity, requested identity,
host-reported identity, and independently verified effective identity. Unknown
observations remain null. A request matching its parent identity is rejected as
an inheritance mismatch; a reported or effective mismatch is rejected.

Qualification records need verified status, an evidence artifact identity and
digest, an ISO validity date, capabilities, supported reasoning efforts, route
availability, and applicable usage restrictions. Role policy binds permitted
task IDs, capabilities, and reasoning efforts. Empty or unapproved policy,
missing evidence, invalid or expired dates, unsupported routes, unavailable
credentials, unknown/exceeded limits, and unauthorized fallback/escalation deny
the request. Credential state is an enum; secret material is not accepted or
returned.

Resource observations use `enforced`, `estimated`, or `reported`. These labels
describe evidence; this helper does not enforce them. Execution records include
safe failure, retry, cancellation, incomplete and rollback fields. Worker and
Tester separation is descriptive metadata; it does not provide process or OS
isolation.

## Native adapter boundary

The native child-delegation surface available in this session accepts explicit
`model` and `reasoning_effort` arguments. This shows only that a request can be
formed. It does not prove provider entitlement, dispatch, effective model,
account access, or identity observability. The adapter does not call the host,
change parent settings, or read credentials. When the caller reports that model
selection is unsupported, the result is `UNSUPPORTED_NATIVE_MODEL_ROUTING` and
no dispatch is attempted. Otherwise it returns `REQUEST_READY_NOT_DISPATCHED`.
Until an authorized live result and an independent identity observation exist,
the status is `NATIVE_MODEL_ROUTING_UNVERIFIED`; see the [capability record](../../evidence/native-model-routing/native-capability.json).

## Optional SkillLab suggestion

The Manager-only adapter invokes SkillLab's existing validated `route` CLI as a
read-only suggestion source. It pins repository commit
`40b4239e14f3c711ec3d32bb7ef4bb0820abdc63`, registry version `1.1`, and registry
SHA-256 `5f8c2f969d85ce95431661c60a520ea000b64661555dfb7136b0ee2ba3289a1b`.
The seven candidate IDs are `writing-for-agents`, `tdd`, `codebase-memory`,
`diagnosing-bugs`, `frontend-design`, `mattpocock-skills:codebase-design`, and
`mattpocock-skills:pr`. SkillLab still applies its own role/action/tool/condition
checks. The adapter rejects candidates outside that set, does not assign a
worker, add tools/actions/permissions, install skills, or mutate the independent
repository. `selected` and `activated` are separate; activation is always
`unverified` here. Denied, unavailable, and no-skill results preserve a safe
empty selection.

## Reproduction

Run `python -m unittest tests.test_native_model_routing -v` for the focused
synthetic suite, or `python -m unittest discover -s tests -v` for product tests.
Both are local data checks, not live model-routing proof. The controlled A/B
observations and their evidence limits are in the [benchmark report](../benchmarks/native-model-routing.md).
