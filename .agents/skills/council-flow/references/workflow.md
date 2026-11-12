# Operational workflow and controlled boundaries

Owner → Planner → parent Manager → Worker → Tester → Reviewer → Manager →
Planner final check → Owner. Preserve that responsibility order.

1. Inspect authorized repository, original goal, instructions, status and actual
   tools. Read policies/roles.yaml and communication.md. The native sandbox and
   actual Owner authorization remain authoritative. Manager performs the
   [Codebase Memory lifecycle](codebase-memory.md) before Planner automatically.
2. Dedicated Planner returns plan.publish JSON with exact immutable acceptance
   and plan artifact/hash. External mode preserves a supplied Owner-approved
   plan verbatim, with provenance; do not claim contact with external ChatGPT.
   Before dispatch, Manager runs sequence validation with
   `--require-criteria-fidelity` and `--authoritative-criteria-ref` pointing to
   the unchanged Owner-approved criteria artifact. Its kind is
   `owner-approved-criteria`, and its JSON shape is
   `{ "criteria": [{"id": "...", "criterion": "..."}] }`. IDs and criterion
   strings are compared in order, exactly, without normalization. The caller
   establishes Owner approval; SHA-256 detects stale bytes but is not
   authentication. Missing, stale, or mismatching sources block dispatch.
   Preserve rejected plans and evidence; corrections require a new plan through
   the existing authorized workflow. All roles use stable IDs and the immutable
   artifact instead of rewriting criterion text.
3. Manager constructs bounded job.assign JSON with objective, scope, original
   acceptance IDs, exact candidate reference and instructions. Validate the
   controlled packet, file hashes and criteria fidelity before delegation. Supply known native
   actor bindings from actual tool metadata, never from self-asserted role text.
4. Fresh Worker implements, runs developer checks and returns job.report JSON.
   Validate on receipt and wait for it to stop edits. Parent Manager does not
   implement application code. Only one Worker mutates this workspace.
   Manager then synchronizes the available Codebase Memory index with the
   resulting source before passing context to independent agents; repeat after
   rework. Failed or unavailable indexing uses the documented source fallback.
5. Fresh independent Tester receives the approved verification strategy and exact
   candidate hash in its own job.assign. It executes original acceptance and
   meaningful negative controls, returns technical job.report, and never repairs.
   Worker self-report alone cannot satisfy acceptance.
6. Fresh independent Reviewer receives job.assign after Tester evidence and
   compares the original plan, candidate and Tester report. It independently
   reruns one Tester-declared deterministic command, captures its own output/exit
   evidence, and reports both hashes, comparison, discrepancies and missing
   evidence to Manager. A match supports repeatability for that command only;
   NOT_COMPARABLE does not pass E8.
7. Manager records task.decision JSON, linking original criteria and actual
   reports/evidence. Mandatory failure triggers rejection/rework or a precise
   blocker. Fresh Worker repair preserves acceptance and authorization, followed
   by affected independent rechecks. See recovery.md.
8. Manager sends verified plan.progress; original Planner returns plan.check
   mapping every original criterion. Manager reconciles all evidence and gives
   Owner concise prose: requested, implemented, tests, Reviewer, open gaps and
   any genuinely necessary Owner decision.

## Practical file boundary

Use ordinary bounded files, for example messages/M001.json, candidate.json and
test-output.txt, referenced by artifact identity/path/SHA-256. Validate UTF-8 JSON
using scripts/contracts.py. Ordered message context checks causal links,
attempt/candidate identities, published acceptance and known actor bindings.
Refer to communication.md for exact schemas, CLI and limitations. This is not a
database, message broker, Supervisor, agent simulator or transport adapter.

Native Codex transport may wrap these messages in an opaque protocol. CouncilFlow
only controls the task packet/report files and instructions passed through
supported native tools; never claim the helper enforces the underlying transport.
Structure is not authentication; YAML cannot grant OS permissions.

Optional diagnostics are bounded one-object-per-line JSONL, tied to real messages
and evidence, never raw prompts/secrets/reasoning. No event file is represented
as authoritative crash-safe accounting. Owner never has to inspect JSON/YAML/
JSONL during ordinary work.

## Native compatibility and truthful gaps

Keep .codex/agents/*.toml in native format. YAML policy responsibilities map to
developer_instructions; do not invent native keys or unsupported models.
If custom-role selection is missing but real native agents work, pass role
instructions to separate native sessions and disclose unverified file selection.
If native roles are unavailable, preserve useful artifacts and mark that run
blocked. Never rename sequential self-assessments as distinct agents.

Native discovery/explicit invocation require actual host evidence. Reading files
or validating example JSON is not activation proof. Preserve historical bootstrap
packets with their limits, then start actual fully validated exchanges after the
contract exists. No fake migrated history or manufactured approvals.

Example ordinary invocation: $council-flow Implement an offline receipt calculator
inside this repository with tests. The Owner need not author internal packets.
