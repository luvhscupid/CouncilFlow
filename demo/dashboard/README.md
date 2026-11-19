# CouncilFlow run board

The dashboard source is bundled with the Codex skill at
`.agents/skills/council-flow/dashboard/`. During each explicit `$council-flow`
task, Manager opens a task-specific board automatically after plan publication
and refreshes its self-contained snapshot after packet updates. Users do not
need to choose a run folder or packet files.

`index.html` is a local demo entry point that forwards to the bundled dashboard.
The dashboard still supports manual folder or JSON import if automatic browser
launch is unavailable. A generated task board reloads its embedded snapshot
every two seconds; it starts no server or background watcher.

The board derives workflow state from CouncilFlow 1.0 packet files and orders
events by packet references. It does not authenticate native sender identity,
claim trusted event time, dispatch agents, approve work, or modify packets.
Packet records remain the source of truth.

## Focused checks

From the repository root:

```powershell
node --test demo/dashboard/tests/*.test.cjs
python -m unittest demo.dashboard.tests.test_publisher -v
```
