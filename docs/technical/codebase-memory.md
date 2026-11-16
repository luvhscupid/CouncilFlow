# Codebase Memory context

Before the Planner runs, the Manager can use the existing DeusData Codebase Memory MCP for
navigation in existing projects, when its tools are available.

## How it is used

1. The Manager first inspects local content. An empty directory, or one containing only
   CouncilFlow installation files, makes **zero** MCP calls.
2. Once meaningful source exists, the Manager identifies the exact project, initializes a useful
   missing index, checks freshness, and retrieves task-relevant symbols, files and dependencies.
3. After implementation and any rework, the Manager updates the index once the Worker stops
   editing.
4. Source reads cover critical code, uncertain freshness and index gaps.

## Limits

- Codebase Memory is optional and separately configured. CouncilFlow does not install or
  reconfigure it.
- CouncilFlow adds no memory engine, manifest, database, API key or manual initialization step.
- If the tools are missing or a configured server cannot be reached, the Manager falls back to
  ordinary repository inspection. Live MCP use is then reported as **UNVERIFIED**.
- Graph findings support navigation only. Independent Tester, Reviewer and final Planner checks
  still decide acceptance.

## Reference and checks

The lifecycle reference is
[`codebase-memory.md`](../../.agents/skills/council-flow/references/codebase-memory.md). It ships
inside the complete skill folder copied during installation. No extra skill or registration is
needed.

Focused static instruction checks:

```sh
python -m unittest discover -s tests -p test_codebase_memory_integration.py -v
```

Full suite:

```sh
python -m unittest discover -s tests -v
```

These checks do not establish native invocation or live MCP behavior.
