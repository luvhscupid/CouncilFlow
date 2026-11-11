# CouncilFlow skill communication contract 1.0

This is the Owner-specified **CouncilFlow skill-level** contract. No authoritative
Council v0.2.1 schema was found here; this does not implement the trusted ACP
Supervisor. Historical unversioned reports remain historical, never fabricated
migrated messages.

Agent task packets/results are **UTF-8 JSON**, not Markdown prose. Policy is
[roles.yaml](../policies/roles.yaml); native Codex configuration remains TOML.
Optional bounded JSONL is diagnostics, not an authoritative/crash-safe ledger.
Only Manager routinely talks to Owner, using concise natural language:
requested, implemented, tested, review findings, remaining gaps, genuine decisions.
Never dump envelopes, YAML or long diagnostic streams into normal Owner chat.

## Envelope and closed payloads

Exact envelope fields and routes are in [message-contract.json](message-contract.json).
Every envelope has protocol="council-flow", version="1.0" (a string), message_id,
message_type, plan_id, positive integer plan_revision, task_id, attempt_id,
sender, recipient, nullable in_reply_to, payload, evidence_refs. Agent-authored
messages omit `created_at`; validated order and reply references preserve causality
but do not establish elapsed wall-clock time.
Actors have exactly role and instance_id. Use exposed native session/task-path
identities. Examples are not runtime evidence.
Boolean integers, unknown fields/roles and unsupported versions fail.

Every artifact reference has exactly artifact_id, repository-relative POSIX path,
lowercase SHA-256 sha256, and kind. Reference large files instead of copying them
into messages. Candidate references identify an immutable file or manifest.
Worker output is a new candidate; Tester/Reviewer receive that exact output. With --root, every
referenced file must exist within that root and match its digest. Traversal and
resolved symlink escapes are rejected before opening a target.

| Purpose | Route | Required payload |
|---|---|---|
| plan.publish | Planner → Manager | objective, scope, acceptance_ids, plan_ref |
| job.assign | Manager → Worker/Tester/Reviewer | objective, scope, acceptance_ids, instructions; candidate_ref required for Tester/Reviewer, optional Worker input; Tester also requires Manager-assigned oracle_ref |
| job.report | Assigned role → Manager | status, summary, acceptance_ids, candidate_ref, findings, errors; Worker adds changed_files; Tester adds checks and deterministic_commands; Reviewer adds comparison |
| task.decision | Manager → Planner | disposition, reason, acceptance_ids, candidate_ref, report_ids; rework adds failed_acceptance_ids |
| plan.progress | Manager → Planner | status, objective, scope, acceptance_ids, verified_progress, next_action; optional candidate_ref |
| plan.check | Planner → Manager | status, summary, acceptance_ids, plan_ref, results |
| approval.request | Manager → human Owner | question, reason, options, operation_ref |
| approval.decision | human Owner → Manager | decision, approval_request_id, provenance_ref |

Report status is passed/failed/blocked/in_progress: technical observation, never
self-approval. A Reviewer `tester_report_ref` identifies the exact earlier
Tester message by its message ID and `kind: "message"`; it is not a self-hash
inside the Tester message. With `--root`, the referenced file must contain that
exact serialized Tester message and match its SHA-256. Findings and every allowed changed_files value are bounded string
arrays; Worker requires changed_files, while other roles may list generated
evidence files without gaining permission to edit product code. Errors are
{code,field,message}. Checks are {name,status,evidence_ref}, with status
passed/failed/blocked/unverified. Reviewer comparison binds the original plan,
Worker candidate, exact Tester report evidence and discrepancies. Passing requires
a matching exit code and CRLF-to-LF-only normalized stdout SHA-256. UX scoring is
not a Reviewer duty.
Plan-check results are {acceptance_id,status,evidence_refs}; each passed result
requires explicit nonempty evidence references. Passed checks map every original
criterion and cannot contain an unmet result. An accept decision cannot also
declare failed_acceptance_ids; any supplied failure identities must be valid
assigned/original criteria.

Manager approves test strategy in the original plan/assignment and optional
oracle_ref. Tester may propose or write isolated oracle tests but cannot approve
its own oracle or lower acceptance. No AI may manufacture an Owner decision.
Actual external Owner input/provenance is required; synthetic unit fixtures are
never actual approvals.

## Validation at controlled boundaries

From the installed repository:

~~~sh
python3 .agents/skills/council-flow/scripts/contracts.py message packet.json --root . --expected-sender worker --expected-instance /root/actual-worker
python3 .agents/skills/council-flow/scripts/contracts.py sequence plan-packet.json assignment.json report.json --root . --bindings observed-bindings.json
python3 .agents/skills/council-flow/scripts/contracts.py policy .agents/skills/council-flow/policies/roles.yaml
python3 .agents/skills/council-flow/scripts/contracts.py events events.jsonl --root .
~~~

The sequence begins with a plan.publish envelope, not the larger plan artifact.
With --root, the referenced JSON plan must contain typed plan_id, positive integer
plan_revision (not boolean), and a nonempty acceptance array of objects with
unique nonempty id values. Criterion text, when supplied, must be a nonempty
string. Other project-owned plan metadata is preserved rather than interpreted
as a new generic schema. An Owner-approved external prose plan stays verbatim in
its own referenced file; create a JSON plan wrapper with these identities and
the unchanged approved criteria, citing the original artifact/hash in the
publication evidence. This does not contact an external conversation.
An initial plan.progress is allowed before publication. A new fully validated
boundary may begin with an actual plan.publish having in_reply_to=null. Preserve
pre-schema bootstrap packets unchanged and label their limitations; do not
rewrite them to manufacture successful history.

Importable API: loads, read_json, validate_message, validate_sequence,
parse_policy, validate_policy, validate_jsonl. Expected sender is an externally
observed {role,instance_id}. Sequence expected_senders is a mapping from message
identity to externally observed actor, not an assertion copied from the packet.
Optional owner_provenance is a set of externally confirmed human-provenance
artifact identities. CLI --owner-provenance is for actual supplied Owner facts.

Ordered context rejects duplicate IDs, unknown predecessors, plan/task/revision
drift, report/assignment origin or attempt mismatch, changed candidate/hash,
unknown acceptance, omitted final mandatory criteria and mutated artifacts.
Rework requires genuine preceding failure evidence; repair needs a fresh Worker
and attempt. If a failed or blocked Planner check triggers rework, the Manager
decision replies to that exact check and preserves its complete failed criterion
set. A completed Tester report reference is an immutable artifact outside the
Tester message, avoiding a circular self-hash while remaining bound by message
ID and (when available) exact file bytes.
Acceptance needs passing distinct Tester and Reviewer reports for the same
candidate/attempt with all required criteria; Worker assertion alone fails.
Planner checks the original plan. External origin bindings detect spoofed actor
labels when actual origin metadata is available.

This **does not authenticate senders**, prove evidence semantics, enforce opaque
native transport, verify model reasoning, or grant permissions. Without ordered
context only structure is checked. Without root, hash shape is checked, not file
existence/content. Codex native transport is outside this helper's control.
Validate controlled packet/report files before dispatch/after receipt while
respecting actual native sandbox and approval mechanisms.

## Bounds and restricted YAML

Messages: 65,536 UTF-8 bytes, 16 nested containers, 128 entries per container,
8,192 characters per ordinary string, 128 per identity, 1,024 per artifact path.
No duplicate keys, NaN/Infinity/overflow, lone surrogates or unknown fields.
Context supports at most 1,024 supplied messages; these are deterministic file
checks, not a persistent resource-enforcing agent runtime.

Policy YAML uses two-space nested mappings with simple lowercase keys,
JSON-quoted strings, strict JSON integers/booleans and inline JSON string lists.
Comments occupy separate lines. Duplicate keys, tabs, implicit strings,
floats/null, tags, anchors, aliases, merges, multiline scalars and block sequences
are unsupported and rejected. This is deliberately not a general YAML parser.
Semantic validation freezes required authority/workflow invariants. No parser
dependency is installed. YAML responsibilities map into native TOML
developer_instructions; no unsupported Codex keys are introduced.

## Optional JSONL

One object per nonblank line with exactly protocol, version, event_id, event_type,
created_at, message_id, plan_id, task_id, attempt_id, evidence_refs. The optional
diagnostic timestamp must come from trusted clock tooling; syntax validation does
not prove provenance. Known types:
plan_published, worker_dispatched, worker_reported, test_failed, review_completed,
rework_requested, acceptance_blocked, task_completed. A trusted tool must capture
event time from a real clock; syntax validation cannot prove this provenance.
Use known message/evidence identities; never invent native session IDs.
Exports are limited to 1 MiB, 1,024 lines and normal per-message limits.
validate_jsonl(..., messages=known_messages) checks message/plan/task/attempt links.
This is optional skill-local diagnostics, not SQLite, accounting or an ACP
Supervisor. Never store credentials, hidden prompts, secrets or private reasoning.
Validation cannot guarantee text redaction. Keep streams out of Owner chat.

## Worker input/output semantics

A new-output Worker assignment may omit candidate_ref. A repair assignment supplies
its immutable input candidate_ref. Worker job.report candidate_ref always names the
actual output artifact/hash; when an input was assigned, input_candidate_ref must
echo that input separately. Do not reuse mutable source paths as old candidates:
use immutable snapshots/manifests. Tester/Reviewer assignments require the exact
output candidate and their reports must preserve it unchanged. Worker output is
allowed to differ from input; verification output is not. Causal plan/task/attempt,
actor and acceptance checks still apply. This is not source-code sandbox enforcement.

## Deterministic command comparison

The Tester records each executed deterministic command: the exact invoked
executable path in `command` and arguments,
working directory, candidate and relevant input references/hashes, integer exit
code, SHA-256 of `raw_stdout.replace(b"\r\n", b"\n")`, acceptance ID, and evidence
artifact. No other normalization is permitted. The Reviewer receives and
independently reruns one declaration using that exact executable path, arguments,
working directory, candidate and relevant inputs; it must not substitute a shell
alias or another executable. It records its execution artifact,
exit code and hash. A match proves repeatability for that command only. A mismatch
preserves both results and fails comparison. With no eligible command, record
`NOT_COMPARABLE`; it cannot pass E8. JSON assertions and structural validation do
not authenticate execution; host-observed evidence is required for runtime claims.

## Verification consistency

Tester assignments require oracle_ref identifying a Manager-approved strategy or
oracle artifact; technical job.report must echo that exact reference in supplied
context. Tester cannot self-approve or substitute it. Every reported technical
check is mandatory for its claimed passed status: failed/blocked/unverified
checks prevent a passed report. Manager cannot accept a supplied failed mandatory
verification. Rework failure IDs must belong to original assigned criteria.
Artifact identity consistency includes nested checks and Planner result references.

Known failed mandatory Tester reports for the same candidate/attempt cannot be
hidden merely by omitting their IDs from an accept decision. A passing final
Planner check follows the Manager evidence-accept decision in supplied context.
