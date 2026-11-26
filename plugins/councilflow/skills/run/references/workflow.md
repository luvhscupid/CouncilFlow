# Operational workflow and controlled boundaries

Owner → Planner → parent Manager → Worker → Tester → Reviewer → Manager →
Planner final check → Owner. Preserve that responsibility order.

1. Inspect authorized repository, original goal, instructions, status and actual
   tools. Read policies/roles.yaml and communication.md. The native sandbox and
   actual Owner authorization remain authoritative. Manager performs the
   [Codebase Memory lifecycle](codebase-memory.md) and
   [original-input/oracle capture](source-fidelity.md) before Planner automatically.
   An optional routing hint may classify the bounded task before planning, but
   Manager validates the route hint and may ignore or override it, recording the
   choice (see communication.md). Routing never grants scope, tool authorization,
   model identity, or role dispatch. Manager supplies Planner with the bounded
   verified context the plan needs; Planner may add read-only, cited research for factual gaps.
2. Dedicated Planner follows [planner.md](planner.md) and returns plan.publish JSON with exact immutable acceptance
   and plan artifact/hash. Manager checks the readiness answer with `planner_contract.py readiness` (only READY, or PROCEED_WITH_ASSUMPTIONS within the project budget, is dispatchable) and applies each task's optional `model_hint` as advice (hint, role default, host model), recording the choice and reason. External mode preserves a supplied Owner-approved
   plan verbatim, with provenance; do not claim contact with external ChatGPT.
   Supplied frozen criteria always require the pre-Planner original-input
   reference, not another agent's derivative. Before dispatch Manager runs
   sequence validation with `--require-criteria-fidelity --original-source-ref`
   and actual caller-observed `--owner-provenance`, as specified in source-fidelity.md.
   The plan preserves `original_source_ref`; exact ordered text is derived from
   the raw source bytes. Missing, stale, substituted or mismatching sources block dispatch.
   Preserve rejected plans and evidence; corrections require a new plan through
   the existing authorized workflow. A Planner revision goes in a new file
   (`plan-r2.json`), keeps objective, scope and acceptance, and is saved in the
   same run folder (see communication.md). All roles use stable IDs and the immutable
   artifact instead of rewriting criterion text. Ordinary requests without
   supplied frozen criteria may generate a native plan, preserving the actual
   request and distinguishing generated acceptance.
3. Manager constructs bounded job.assign JSON with objective, scope, original
   acceptance IDs, exact candidate reference and instructions. For each Worker
   assignment, validate the READY plan against frozen criteria and verify the
   plan ID/revision, task ID, acceptance IDs and Planner-authored instruction
   array exactly match that selected task using
   `scripts/planner_contract.py assignment <plan-rN.json> <frozen-criteria.json> <assignment.json>`
   (or `--planner-generated-criteria` instead of the criteria file for native
   planning). The envelope `task_id` stays the run's task; `payload.plan_task_id`
   names the Planner task. The first Worker assignment replying to `plan.publish`
   starts the implementation attempt with its own `attempt_id`.
   Also validate the controlled packet, file hashes and any required criteria
   fidelity before delegation. Non-ready responses are not published or dispatched;
   Manager keeps them as evidence and asks the Owner through approval.request.
   Manager copies Planner task instructions exactly and never rewrites them.
   Supply known native
   actor bindings from actual tool metadata, never from self-asserted role text.
   Runs that use project state use council-flow 1.1: assignments and reports pin
   `ledger_version` and `slice_id`, and contradicting evidence goes as
   `evidence.reopen` (see communication.md, recovery.md).
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
   For required frozen-criteria invocations, repeat exact fidelity validation
   against the original trusted reference before accepting this final check.

## Practical file boundary

For Codex runs, Manager stores each task's packet files in
`.councilflow/runs/<task-id>/`, with messages in its `messages/` folder. Use
ordinary bounded files, for example `messages/M001.json`, `candidate.json` and
`test-output.txt`, referenced by artifact identity/path/SHA-256. Validate UTF-8 JSON
using scripts/contracts.py. Save every packet into `messages/` only with
`contracts.py save <packet.json> --run .councilflow/runs/<task-id> --root .`:
Planner packets, every `job.assign` (Worker, Tester and Reviewer), every
`job.report`, `task.decision`, `plan.progress` and `plan.check`. It refuses a
bare report body without the council-flow envelope, a packet that fails
`message` or breaks the run order, and an existing message id; a refused packet
is kept outside `messages/` as evidence, never rewritten to pass. Do not write
packets into `messages/` by hand or as Markdown. Ordered message context checks causal links,
attempt/candidate identities, published acceptance and known actor bindings.
Refer to communication.md for exact schemas, CLI and limitations. This is not a
database, message broker, Supervisor, agent simulator or transport adapter.

After validating `plan.publish`, Manager opens the read-only dashboard once for
the task with `scripts/dashboard.py publish --root . --task-id <task-id> --open`.
After each Manager packet write and each validated role result, Manager reruns
the helper without `--open` so the same self-contained board refreshes from the
current task directory. The dashboard is an informational projection; packets
remain authoritative, and no local service or watcher is started. If the host
cannot open the browser, report the dashboard as blocked and continue the normal
workflow without claiming a live connection.

Native Codex transport may wrap these messages in an opaque protocol. CouncilFlow
only controls the task packet/report files and instructions passed through
supported native tools; never claim the helper enforces the underlying transport.
Structure is not authentication; YAML cannot grant OS permissions.

Optional diagnostics are bounded one-object-per-line JSONL, tied to real messages
and evidence, never raw prompts/secrets/reasoning. No event file is represented
as authoritative crash-safe accounting. Owner never has to inspect JSON/YAML/
JSONL during ordinary work.

## Adaptive execution with project state

Applies to runs that use project state (ADR-001, [project state](project-state.md)).
Runs without it keep the single-task workflow above. Packets are council-flow 1.1.
The Manager never edits the ledger and never changes a requirement.

1. **Intake.** Save every Owner message with `project_state.py source-add` before
   any agent reads it. The Planner writes ledger v1 from those sources; with frozen
   criteria supplied, use `project_state.py bootstrap`.
2. **Plan.** The Manager proposes slices in `.councilflow/project/plan.json`. Each
   slice is pinned to a ledger version and cites ledger ids. Run
   `project_state.py validate` after each plan edit.
3. **Readiness.** The Planner answers readiness per slice. Check it with
   `planner_contract.py readiness --project`. Only a dispatchable slice gets a
   `job.assign` carrying `ledger_version` and `slice_id`.
4. **Run.** Each slice keeps its own run folder (`run_dir`) and the existing
   per-task workflow inside it. One mutating Worker per workspace still applies, so
   unrelated slices run one after another unless isolated workspaces are authorized.
5. **Model choice.** For worker, tester and reviewer, apply the Planner hint, then
   the role default from the approved split, then the host model. Record
   `hint`, `used`, `source` and `reason` in the slice `model_routing`.
6. **Reopen.** Forward an `evidence.reopen` request to the Planner unchanged.
7. **Reconcile.** After `ledger.publish`, run `project_state.py affected --project
   DIR --to-version M`. Set affected slices to PAUSED until a new readiness
   answer; unaffected slices continue. Closed slices listed as `closed_affected`
   may hold stale verification and are reported to the Planner.
8. **Budget.** When the assumption budget is exhausted, slices that need new
   defaults stay BLOCKED while the others continue.
9. **Owner questions.** Ask only through `approval.request`, with `questions`
   copied exactly from the readiness answer. Save each Owner reply with
   `source-add` and cite it as `owner_source_ref` before any agent reads it.
10. **Disagreement.** If Planner and Manager disagree, raise it to the Owner
    (ADR-001 section 10). Do not change requirements to resolve it.

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
