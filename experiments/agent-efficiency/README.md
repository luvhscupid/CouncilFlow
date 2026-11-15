# Agent efficiency toolkit (offline prototype)

**For AI agents continuing this work:** read [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) first. It records the Phase 1–5 commits, actual component boundaries, tests reported versus verified, important contract gaps, and the next safe steps. No live integration or demonstrated token savings yet.

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

The process exit code is returned by the wrapper. On timeout, the wrapper returns
124 with `TIMED_OUT` and `DIGEST_INCOMPLETE`; the digest retains the observed
termination code after killing/draining the direct child. Inspect either original
stream only by explicit expansion; expansion checks its recorded hash first and
writes the original bytes, including malformed UTF-8, ANSI sequences and CRLF:

```sh
python experiments/agent-efficiency/digest.py expand /tmp/agent-run/digest.json stderr
```

Use a fresh digest-output filename for every run; existing digest and artifact
files are refused rather than overwritten. The Python API `expand_bytes` returns
the hash-checked original bytes; `expand` remains a decoded compatibility view.

`--limit` bounds each stream's excerpt, the total important-line text and the
total failure-ID text separately, in characters. Recognized unittest/pytest
failure identifiers are advisory; other formats remain available in the original
artifact. Truncation, malformed UTF-8/JSON, timeout and unknown exit status mark
`DIGEST_INCOMPLETE`; nonzero exits also mark `COMMAND_FAILED`. The same input and
limit produce the same stream summaries and hashes. Capture records command
arguments, actual working directory, an explicitly supplied absolute executable
when available, and an environment source label without environment values.

Artifacts may contain sensitive command output. Use a permitted local directory
(for example this folder's ignored `.local-runs/`) and do not commit real outputs.
Summaries remain heuristic views, not proof of success. Expand when details
matter, including failures outside the initial excerpt. Capture buffers complete
output in memory and timeout manages the direct child only; descendants holding
inherited pipes can delay draining. Path checks reject traversal and observed
symlink/junction paths but do not provide race-free containment or sandbox
isolation. No measured token savings or live integration is established here.

## Phase 3 Codex adapter

`codex_adapter.py` is an offline adapter: it consumes an explicitly supplied `codex exec --json` JSONL file (or stdin), emits a Phase 1 record, and uses the Phase 2 digest to retain/hash the exact input stream. It does not invoke Codex or make API calls. For example:

```sh
python experiments/agent-efficiency/codex_adapter.py experiments/agent-efficiency/fixtures/codex-exec-sanitized.jsonl --artifacts /tmp/codex-run --records /tmp/codex-runs.jsonl
```

Only completed turn aggregate usage is counted; missing fields stay null, unsupported/malformed events make the result incomplete, and acceptance remains unknown. The route defaults to `codex/native-or-configured`; pass an explicit route label only when its source is known. The fixture is synthetic. Codex CLI availability/version may be checked locally, but a live `codex exec` request requires separate user selection and is not part of offline parsing.

## Phase 4 Claude Code and compatible gateways

`claude_adapter.py` consumes an explicitly supplied Claude Code `--output-format stream-json` JSONL capture or stdin, emits a Phase 1 record, and stores/hashes the complete input through the Phase 2 digest. It never starts Claude, reads environment variables/config files, or handles credentials:

```sh
python experiments/agent-efficiency/claude_adapter.py experiments/agent-efficiency/fixtures/claude-stream-sanitized.jsonl --artifacts /tmp/claude-run --gateway xkiro --model fixture-upstream-a --records /tmp/claude-runs.jsonl
```

| Telemetry | Adapter behavior |
| --- | --- |
| Harness | `claude-code` |
| Gateway | Explicit label (`xkiro` default); label only, not verified gateway identity |
| Upstream model | Explicit CLI value or unambiguous event model; changes across events remain unknown and are noted |
| Route | Separate route field, defaults to `claude-code/<gateway>/stream-json` |
| Input/output/cache read/cache creation | Read from the final recognized usage snapshot when present; otherwise null with reason |
| Cost/prices | Always unknown; no Anthropic price inference and no gateway billing inference |
| Retries | Reported only if a gateway event explicitly supplies `gateway.retry_count`; otherwise unknown |
| Acceptance | Always unknown; usage output does not prove task acceptance |
| Timing | Optional caller-supplied elapsed milliseconds; not inferred from timestamps |

Recognized event types are `system`, `assistant`, `user`, `result`, and `stream_event`; unsupported or malformed lines make the stream incomplete. The adapter uses the final observed usage snapshot and does not add potentially cumulative snapshots. It accepts no claim that xKiro emits this optional metadata unless it is actually present in the supplied capture. `fixtures/claude-stream-sanitized.jsonl` is synthetic; live Claude/xKiro integration is UNVERIFIED.

## Phase 5 offline evaluation and protocol draft

`evaluate.py` compares paired JSON observations with matching `task_id`. Each pair has `baseline` and `optimized` Phase 1 records; optionally add `digest_review` to the optimized side with `failure_present`, `summary_detected`, and an evidence reference. The evaluator only counts explicitly reported accepted-task cost, known acceptance outcomes, attempts, elapsed time, and cache counters. Missing usage makes total spend unknown; it is never treated as zero. Sample counts, means, standard deviations, and approximate 95% normal intervals are reported where there are enough measurements. Cache fraction means `cached_input/input`, not verified gateway cache effectiveness.

Offline synthetic evaluation:

```sh
python experiments/agent-efficiency/evaluate.py evaluate experiments/agent-efficiency/fixtures/paired-evaluation.json --minimum-improvement 0.10 --minimum-reliability 0.95 --budget 5
```

Prepare a protocol for Owner review (draft only):

```sh
python experiments/agent-efficiency/evaluate.py draft --task-set 'Owner selected task IDs' --minimum-improvement 0.10 --minimum-reliability 0.95 --budget 5 --max-runs 30 --max-minutes 60 --output proposed-protocol.json
```

Before any future live run, the Owner must review and explicitly approve the task set, paired procedure, thresholds, budgets, stop rule, and terminal outcomes. After approval, freeze the exact protocol bytes and SHA-256 before collecting observations. No live experiment is authorized or activated by this toolkit. Cost comparisons require comparable authoritative reported costs on both sides; xKiro cost may remain unavailable.
