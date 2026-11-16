# Agent Efficiency development records

Packages A, B, C1 and C2 are now an optional capability of the installable
CouncilFlow skill. The single maintained Python runtime is in
[`scripts/efficiency/`](../../.agents/skills/council-flow/scripts/efficiency/),
with the explicit CLI at
[`scripts/efficiency.py`](../../.agents/skills/council-flow/scripts/efficiency.py).
Read [the installed interface and safeguards](../../.agents/skills/council-flow/references/efficiency.md).
Copying the complete skill is sufficient in another compatible repository;
this experiment directory is not a runtime dependency.

Run the original component tests from their maintained locations:

```sh
python -m unittest discover -s tests -p 'test_efficiency_*.py' -v
```

The sanitized parser fixtures moved to `tests/efficiency-fixtures/`. No raw
host captures or private transcripts are packaged. Live Codex and Claude
Code/xKiro compatibility remains LIVE_UNVERIFIED; no savings, billing, cache
hit, upstream identity or subscription-quota claim follows from offline tests.
No hooks or paid model requests are enabled by installation.

## Package D remains draft

`evaluate.py`, `test_evaluate.py`, the paired synthetic fixture and
`evaluation/` remain here as preserved offline development material.
**DRAFT_NOT_AUTHORIZED** still applies to the protocol and all experimental
trials; integration does not authorize running them. The deterministic offline
unit tests may be run without launching any trial:

```sh
python -m unittest discover -s experiments/agent-efficiency -v
```

[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) is the retained historical
Phase 1-5 handoff, including old paths and earlier deferred integration notes.
Those historical paths describe their original checkpoints, not today's runtime.
Git branch `feature/agent-efficiency` and checkpoint
`d34492aed433a81d3677064a0a834d8bc367208c` remain recoverable.
