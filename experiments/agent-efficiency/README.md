# Agent efficiency recorder (Phase 1)

Offline, opt-in prototype. It reads no host configuration, credentials, prompts, or session logs and makes no network/API calls.

Run the tests with `python -m unittest discover -s experiments/agent-efficiency -p 'test_*.py' -v` from the repository root. The Python module exposes `record`, `validate`, `parse_codex_event`, `parse_claude_json`, and `append_jsonl`; callers must explicitly supply test-owned, locally consented input.

The Codex and Claude parsers accept only narrow event shapes and emit `null` for absent telemetry with a reason. Fixtures are synthetic, not verified host samples. In particular, the Claude route is labeled `claude-code/xkiro/<upstream-model>` and reported cost remains unknown: a Claude usage counter does not establish xKiro billing. Accepted status requires an evidence reference and owner or external-check provenance; the recorder does not verify that evidence itself.

| Metric | Offline support | Live host status |
| --- | --- | --- |
| Input/cached input/cache creation/output | Nullable parser fields | UNVERIFIED |
| Reported cost | Nullable; never inferred | UNVERIFIED |
| Wall time/retries/attempt | Record fields | Caller supplied; UNVERIFIED |
| Accepted task outcome | Evidence reference plus provenance required | No automatic verification |

Schema: `record.schema.json`. Synthetic sanitized JSONL example: `fixtures/sanitized-runs.jsonl`.

## Phase 2 command digest

Run an explicitly selected safe local command and save a digest plus complete stream artifacts:

```sh
python experiments/agent-efficiency/digest.py run --artifacts /tmp/agent-run --digest-output /tmp/agent-run/digest.json --timeout 30 -- python -m unittest
```

The process exit code is returned by the wrapper (timeout returns 124 and is marked `TIMED_OUT`). Inspect either original stream only by explicit expansion; expansion checks its recorded hash first:

```sh
python experiments/agent-efficiency/digest.py expand /tmp/agent-run/digest.json stderr
```

Artifacts may contain sensitive command output. Choose a permitted local artifact directory and do not commit run artifacts. Summaries are intentionally not proof of success: important lines are sampled, not a complete classification; truncation, malformed UTF-8/JSON, timeout, and nonzero exit receive flags. Always expand when details matter.
