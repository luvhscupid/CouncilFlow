# Claude Code plugin

The Claude Code plugin packages CouncilFlow as a `/councilflow:run` command. One real calc-001
smoke test completed **VERIFIED_ACCEPT**. Actual native Planner, Worker, Tester and
Reviewer sessions were observed; the full 11-message sequence validated.
See the [sanitized evidence summary](../../reports/documentation-release-sync/claude-calc-001.md).
This establishes one successful run, not universal host compatibility. Upstream model
identity, effective route, cost and quota remain unknown. Agent Efficiency helpers
are offline-tested and opt-in; live adapter and billing compatibility remain
unverified. Package D remains **DRAFT_NOT_AUTHORIZED**.

## Load it locally

These commands affect only the current checkout and session. No global configuration
is modified. Run them from the repository root:

```sh
claude --plugin-dir plugins/councilflow          # load from this checkout, current session only
claude plugin validate plugins/councilflow       # check the manifest, skill and agents
```

## Use it in another repository

1. Extract `dist/councilflow-claude-plugin.zip` to a directory of your choice.
2. From the target repository, start Claude Code with `claude --plugin-dir <that directory>`.
3. Run `/councilflow:run <coding goal>`.

Run artifacts are written to the target repository under `.councilflow/runs/`. Keep that
directory out of version control. Efficiency helpers stay opt-in. The Phase 5 evaluation
protocol remains DRAFT_NOT_AUTHORIZED.

## How the Manager works

The main Claude Code session is the Manager. It validates each message, then launches a
fresh plugin agent for each step: Planner, Worker, Tester and Reviewer. The Planner's
final check runs last. Only the Manager reports results to you.

See [Structured communication](structured-communication.md) for the message format and
validator commands.

## Related

- [Host packages](host-packages.md)
- [Optional efficiency helpers](efficiency-helpers.md)
