# Agent efficiency experiments (development records)

**Status: experiment and development record. Not a product, not a release, and not a standalone AI application.**

This directory holds the offline development material for the Agent Efficiency
work. Its runtime helpers were integrated into the CouncilFlow skill. The
directory itself is not a runtime dependency of CouncilFlow, and nothing here
enables hooks, changes routing, captures sessions, or starts paid model requests.

## Purpose

- Preserve the Phase 1-5 development history and the draft paired-evaluation
  protocol (Package D) for owner review.
- Provide a deterministic offline evaluator (`evaluate.py`) and its unit tests,
  run against a synthetic paired fixture.

## Non-goals

- Running any paired trial, live model comparison, or quota-consuming session.
- Claiming savings, billing reduction, cache-hit efficacy, upstream model
  identity, or subscription-quota behavior. Offline tests establish none of these.
- Approving the Package D protocol. It is marked `DRAFT_NOT_AUTHORIZED` and
  `PROPOSED_FOR_OWNER_APPROVAL`; integration does not authorize running it.
- Serving as the source of the installable helpers. Use the skill copy instead
  (see Links).

Live Codex and Claude Code / xKiro compatibility remains `LIVE_UNVERIFIED`.

## Prerequisites

- Python 3 with the standard library only. The installed helpers require
  Python 3.11+ per the skill reference.
- A local checkout of this repository. Run commands from the repository root.
- No API keys, network access, or host CLI sessions are needed for the
  commands below.

## Safe commands

All commands below are offline and read-only with respect to the repository,
except where noted. Add `-B` to avoid writing `__pycache__`.

1. Run the original component tests (installed efficiency helpers, Packages A-C2):

   ```sh
   python -B -m unittest discover -s tests -p 'test_efficiency_*.py' -v
   ```

2. Run the offline unit tests for Package D (no trial is launched):

   ```sh
   python -B -m unittest discover -s experiments/agent-efficiency -v
   ```

3. Evaluate the synthetic paired fixture and print the result to stdout:

   ```sh
   python -B experiments/agent-efficiency/evaluate.py evaluate experiments/agent-efficiency/fixtures/paired-evaluation.json --minimum-improvement 0.1 --minimum-reliability 0.8 --budget 10
   ```

   The `draft` subcommand of `evaluate.py` requires `--output` and writes a file.
   Do not run it unless you intend to write that file, and point `--output` at a
   scratch location outside the repository.

## Expected outputs

- Command 1: a `Ran 76 tests` summary ending in `OK (skipped=3)` when last run
  (the skip count may differ by platform).
- Command 2: `Ran 3 tests` ending in `OK`. The tests assert that the synthetic
  fixture yields `provisional_outcome` `CLOSED_NO_BENEFIT` and
  `approval_status` `NOT_APPROVED; offline analysis only`.
- Command 3: pretty-printed JSON with `accepted_cost`, `reliability`,
  `digest_missed_failures`, and `provisional_outcome`. Missing values stay
  `null`; they are not zero-filled.

A non-zero exit or traceback indicates a broken environment or a changed input,
not a result. Do not treat any output here as evidence of efficiency gains.

## Layout

| Path | Kind | Notes |
| --- | --- | --- |
| `evaluate.py`, `test_evaluate.py` | Experiment code and tests | Offline Package D evaluator. |
| `fixtures/paired-evaluation.json` | Test data (synthetic) | Three synthetic baseline/optimized pairs. Not host captures. |
| `evaluation/PROTOCOL.md`, `evaluation/RUNBOOK.md` | Draft protocol | `DRAFT_NOT_AUTHORIZED`; procedures only. |
| `evaluation/protocol.draft.json` | Draft protocol data | Machine-readable draft decisions. |
| `IMPLEMENTATION-STATUS.md` | Historical handoff | Phase 1-5 record. Old paths describe earlier checkpoints. |
| `.gitignore` | Config | Excludes local captures, caches, and secrets-like files. |

## Links

- Installed skill interface and safeguards:
  [`.agents/skills/council-flow/references/efficiency.md`](../../.agents/skills/council-flow/references/efficiency.md)
- Maintained runtime package:
  [`.agents/skills/council-flow/scripts/efficiency/`](../../.agents/skills/council-flow/scripts/efficiency/)
- Explicit CLI:
  [`.agents/skills/council-flow/scripts/efficiency.py`](../../.agents/skills/council-flow/scripts/efficiency.py)
- Sanitized parser test data (test data, not captures):
  [`tests/efficiency-fixtures/`](../../tests/efficiency-fixtures/)
- Draft protocol: [PROTOCOL.md](evaluation/PROTOCOL.md),
  [RUNBOOK.md](evaluation/RUNBOOK.md),
  [protocol.draft.json](evaluation/protocol.draft.json)
- Historical handoff: [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md)
- Recovery references (not required to run anything here): git branch
  `feature/agent-efficiency`; checkpoint `d34492aed433a81d3677064a0a834d8bc367208c`.
