# CouncilFlow dashboard

A read-only control room for one CouncilFlow run. It shows which role holds the
work, every recorded handoff, how far the current attempt has got, and which
acceptance criteria the Planner's final check verified. It never dispatches
agents, approves work or changes packets. Packet records stay the source of truth.

## How it reaches the browser

The dashboard ships inside the skill at `.agents/skills/council-flow/dashboard/`:
`index.html`, `styles.css`, `run-reader.js` (packet validation) and `app.js`
(the built React app). During an explicit `$council-flow` task every packet is saved with
`scripts/contracts.py save … --run .councilflow/runs/<task-id>`, and each save
republishes two self-contained pages:

- `.councilflow/runs/<task-id>/dashboard.html`, the board for that run;
- `.councilflow/dashboard.html`, the project board, which always shows the run this
  project saved to most recently.

The run's first packet opens the project board once in the default browser, so a
CouncilFlow run in any project connects its own board with no file picking.
Set `CI` or `COUNCILFLOW_NO_BROWSER`, or pass `--no-open`, to keep the browser
closed. The same pages can be published by hand:

```sh
python .agents/skills/council-flow/scripts/dashboard.py publish --root . --task-id <task-id> --open
```

The page starts no server; its **Follow live** button reloads the file every 3
seconds while the run is in progress and stops once the final check is recorded.

The board opens on the run it was published for, headed by the project name
(the repository folder) with the task objective in smaller text beneath it.
Looking at a different run is a deliberate step: the **Project list** tab links
to the other published runs of the same project, and can open a run folder (watched for new packets in Chromium browsers) or a set of JSON
files. `index.html` in this folder forwards to the bundled board, which starts on
that tab's prompt when no run is embedded.

## What each number comes from

| Shown | Source |
|---|---|
| Role states, latest handoff, activity | Validated `council-flow 1.0` packets, in reply order |
| Workflow steps recorded (x of 10) | The ten packets one accepted attempt records, counted for the current attempt |
| Acceptance verified | Only the Planner's complete final check with its evidence chain |
| Times and durations | Packet file write times, labeled as such; never authenticated event times |
| Tokens and models | Agent Efficiency records, only when published with `--efficiency-records <file.jsonl>` and matching the task ID |
| Workflow policy | `policies/roles.yaml`, read-only |

Anything the records do not hold is shown as unavailable, never estimated.

## Changing the dashboard

The source lives in `demo/dashboard/app/src` (React 18, no other runtime
dependency). `styles.css` stays hand-written in the skill folder.

```sh
cd demo/dashboard/app
npm install
npm run build   # writes .agents/skills/council-flow/dashboard/app.js
```

Commit the rebuilt `app.js`; a test fails if it does not match the sources. Then
sync the plugin copy with `python tools/build_claude_plugin.py sync`.

## Focused checks

From the repository root:

```sh
node --test demo/dashboard/tests/*.test.cjs
python -m unittest discover -s demo/dashboard/tests -v
```

`tests/fixtures/council-run.cjs` holds synthetic runs used only by these tests.
