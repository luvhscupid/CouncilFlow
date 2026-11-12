# Next Gate 3 observation: Owner fixture and handoff

## Owner fixture approval procedure

1. Personally review the exact proposed task text in
   `reports/gate3-next/OWNER-TASK-DRAFT.txt`. It is not approved yet.
2. If acceptable, save that exact task text byte-for-byte under a new
   `owner-fixtures/` directory in the disposable workspace, outside
   `.agents/skills/`. Also save a JSON
   sidecar in the validator's documented shape:
   `{ "criteria": [{"id": "AC1", "criterion": "..."}, ...] }`.
   Copy each numbered acceptance line into its `criterion` string exactly,
   including its visible number, punctuation, spaces, and wording; IDs are
   separate metadata. Review both files together. Stage them before the
   observation and treat them as read-only inputs during it.
3. Explicitly approve the task text and its criteria sidecar as one fixture
   set, and record both paths and SHA-256 values. A matching digest records byte
   integrity; the Owner's explicit approval is the provenance. Do not treat any
   earlier task, agent-authored hash, or this procedure as approval.

## Execution handoff

After approval, use a **new authenticated local Codex session** with
   `reports/gate3-next/disposable-workspace` as its authorized workspace root.
Submit one initial instruction consisting only of `$council-flow` followed by
   the exact saved task text. Before any role dispatch, Manager must point the
contract validator at the Owner-approved JSON sidecar and pass the required
criteria-fidelity gate. Do not paste the skill or add a spawn instruction.
After submission, do not relay messages or files between agents. Capture the
host-observed activation, delegation, child-thread, Tester execution and loaded
configuration records if the host exposes them. Preserve all failures and stop
under the frozen E3 rule if distinct subagent spawning is not established.

The next observation has **not** been run. The prior E10 failure remains a
historical failure; this handoff does not retroactively approve its fixture.
