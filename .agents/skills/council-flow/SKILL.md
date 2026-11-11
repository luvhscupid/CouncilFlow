---
name: council-flow
description: "Coordinate an ordinary coding goal through a Planner, parent Manager, fresh Worker, independent Tester, and independent Reviewer using native Codex subagents. Invoke explicitly with $council-flow for implementation, repair, or refactoring that needs this five-role workflow. Do not use for general questions or pretend unavailable delegation works."
---

# CouncilFlow

Invoke with `$council-flow <ordinary coding goal>` in a supported Codex host.

Use native Codex agents and the current session's approved tools, credentials,
permissions, models, and budget. This skill is an instruction workflow, not a
security sandbox. It needs no API key, service, database, or custom supervisor.
Only the parent **Manager** gives routine progress and results to the Owner.

## Execute the goal

1. **Establish scope.** Read repository instructions and status. Record the
   Owner's goal, authorized paths, constraints, and observable acceptance. Inspect
   available delegation and model controls; do not invent tool names or models.
   Read [roles](references/roles.md) and [workflow](references/workflow.md).
2. **Planner.** In native mode, ask a dedicated real Planner subagent for an
   immutable implementation contract before implementation. In external mode,
   preserve the Owner-approved supplied plan verbatim; record its provenance and
   do not claim to contact that external ChatGPT conversation. Have a native
   Planner check completeness if available. Resolve material gaps with the Owner
   only when existing authority cannot resolve them.
3. **Manager.** Accept and record the contract and acceptance IDs. Delegate a
   bounded request to a fresh real Worker, using the available custom role if
   supported or passing the role instructions to the native subagent. Inherit
   the current model configuration unless a supported, justified choice exists.
   The Manager does not write application code. Permit only one Worker to mutate
   a workspace at once; parallel implementation requires authorized isolation.
4. **Worker.** Implement within scope, run developer checks, and return changed
   files and actual results. A Worker cannot approve its own work or change the
   contract. Wait for implementation to finish before verification.
5. **Tester.** Assign a fresh separate native Tester the approved contract and
   implementation. Require independent execution and acceptance checks. The
   Tester reports failures and unknowns and never repairs implementation.
6. **Reviewer.** After technical verification, assign a fresh separate native
   Reviewer to approach the result as a user, inspect instructions, and exercise
   relevant interaction. Require observations distinct from inspection; never
   substitute a score for technical evidence. The Reviewer does not edit code.
7. **Rework.** Evaluate findings against unchanged criteria. Reject any failed
   mandatory check. Send a corrected bounded request to a fresh Worker for
   needed repairs, then repeat affected independent verification and review.
   Follow [recovery](references/recovery.md); no arbitrary repair-count limit.
8. **Final Planner check.** Ask the Planner to map every original acceptance ID
   to observed evidence and open gaps. The Manager evaluates all results and
   reports the outcome to the Owner using [acceptance](references/acceptance.md).

## Truthful completion

Keep compact requests/results and evidence in ordinary project files when
durability is useful. Record actual available session identifiers, commands,
exit status, artifact paths, findings, repairs, and final disposition. Keep long
logs out of routine Owner updates. JSON is a record, never permission authority.

If discovery, invocation, native delegation, a role, test, or interaction is
unavailable, explicitly mark it **UNVERIFIED** or **BLOCKED**. Deliver useful
authorized artifacts, but never simulate agents, rename self-review as
independent review, or declare the complete workflow verified. Report
**PARTIAL — precise missing capability** when mandatory evidence is missing.

Keep Owner authority over consequential or out-of-scope actions. Refuse or
escalate unauthorized external changes without attempting them. Continue
ordinary authorized engineering work without repeated approval requests.
