# Optional Agent Efficiency helpers

Efficiency is disabled by default. Read this reference only when the Owner
explicitly requests efficiency helpers for the task, or invokes their CLI.
Installation never enables hooks, changes routes, captures sessions or starts
model requests. Normal CouncilFlow execution remains unchanged when disabled.

## Locate and invoke

Resolve `scripts/efficiency.py` relative to the installed `SKILL.md`, rather
than the working repository or a development checkout. Copy the complete skill
folder when installing. Python 3.11+ and its standard library are sufficient.
Examples below use a repository installation; for a user installation substitute
the actual absolute skill path. Run from the target repository so commands use
that repository as their working directory.

```sh
python .agents/skills/council-flow/scripts/efficiency.py --help
python .agents/skills/council-flow/scripts/efficiency.py record record-input.json --records local-evidence/records.jsonl
python .agents/skills/council-flow/scripts/efficiency.py digest run --artifacts local-evidence/run-01 --digest-output local-evidence/run-01/digest.json --timeout 30 -- python -m unittest discover -s tests
python .agents/skills/council-flow/scripts/efficiency.py digest expand local-evidence/run-01/digest.json stderr
```

`record-input.json` is an explicitly supplied JSON object of recorder keyword
arguments. Minimal example:

```json
{"run_id":"task-01","harness":"codex","route":"codex/native-or-configured"}
```

Optional fields include `task_class`, `repository_revision`, `elapsed_ms`,
`usage_scope`, `usage`, `attempt`, `acceptance`, `gateway`, `upstream_model`,
`source_kind` and `notes`; see `scripts/efficiency/record.schema.json` and
`record()` in `recorder.py`. Omit unobserved telemetry: nullable fields carry
availability reasons, never invented zeros or costs. Acceptance defaults to
unknown. An accepted record requires an evidence reference and caller-supplied
Owner/external-check provenance; the helper does not authenticate that claim.
The record CLI appends validated JSONL and exits 2 for invalid inputs.

## Evidence and failure handling

Digest runs only the explicitly supplied permitted local command. It retains
complete stdout/stderr bytes in separate artifacts, and returns the command's
exit code. Timeout returns 124 with `TIMED_OUT` and `DIGEST_INCOMPLETE` after
killing/draining the direct child. Descendants holding pipes can delay draining;
this helper is not a process sandbox. Capture buffers full output in memory.

Use a fresh digest filename/artifact run each time; existing artifacts are
refused. `--limit` bounds excerpts, important-line text and failure IDs. Truncation,
malformed UTF-8/JSON, timeout or unknown exit status mark `DIGEST_INCOMPLETE`;
nonzero exit also marks `COMMAND_FAILED`. Failure IDs are advisory. Expand when
any flag is present, expected checks are absent, or details affect acceptance.
Expansion verifies SHA-256 and emits original bytes without newline/ANSI/UTF-8
normalization. Preserve all permitted artifacts for the full review lifetime.
Keep local outputs outside version control and release sources; choose storage
permitted for their contents. The builder excludes `.local-runs/` directories.

Compact handoffs retain original-source references, criteria identities, exact
candidate, command/executable/arguments/workdir, exit status and full evidence
references. A digest excerpt cannot become the frozen Owner plan or replace
Tester execution, Reviewer comparison/rerun, Manager decisions or final Planner
checks. Reviewer stdout comparison still hashes raw stdout after CRLF-to-LF
replacement only; the digest's presentation excerpt uses different normalization.
Manager transfers references directly between native agents; Owner remains out
of routine courier work.

## Offline adapters

```sh
python .agents/skills/council-flow/scripts/efficiency.py codex permitted-events.jsonl --artifacts local-evidence/codex-01 --records local-evidence/codex-records.jsonl
python .agents/skills/council-flow/scripts/efficiency.py claude permitted-result.json --gateway xkiro --gateway-source caller-supplied --artifacts local-evidence/claude-01 --records local-evidence/claude-records.jsonl
```

These parsers consume only explicitly supplied captures or stdin. They never
invoke a host, inspect credentials/configuration, install hooks, or intercept
conversations. Expansion of adapter artifacts returns **allowlisted metadata**,
not the original transcript; raw prompts, reasoning, tools and conversations are
not copied. Digest command capture separately retains full permitted tool output.
Adapter exit 0 means a supported completed stream parsed; exit 2 indicates
incomplete/failed/unsupported input, not the original host process exit. Supply
`--process-exit-code`, timing/version/revision/cancellation labels only when
observed. Unknown process exit keeps digest evidence incomplete.

Codex uses `codex/native-or-configured`; Claude uses a separate
`claude-code/unknown/stream-json` or explicitly asserted
`claude-code/xkiro/stream-json` route. Configured, reported and effective model
identities remain distinct. Effective upstream identity, provider billing,
subscription quota, session totals and unreported cache metrics remain unknown.
Reported counters are not verified cache hits or authoritative costs.

Offline adapter tests are available; live Codex and Claude Code/xKiro
compatibility remains **LIVE_UNVERIFIED**. There is no observed native hook:
use these explicit CLIs where host activation is unavailable. Package D's
evaluation protocol remains **DRAFT_NOT_AUTHORIZED** in the development
`experiments/agent-efficiency/` tree, excluded from the installed capability.
This integration authorizes no trial, spending or universal model selector.
