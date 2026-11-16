# Optional efficiency helpers

The installed skill includes a recorder, deterministic digest and expand tools, and offline
adapters for Codex, Claude Code and xKiro. All helpers stay **disabled unless you explicitly
request them**.

## Opt in

Invoke the skill with an explicit request, for example:

```text
$council-flow <goal>; use the optional efficiency helpers for permitted local test output
```

Or call the command-line tool directly. Resolve the path relative to the installed skill:

```sh
python .agents/skills/council-flow/scripts/efficiency.py --help
python .agents/skills/council-flow/scripts/efficiency.py record record-input.json --records local-evidence/records.jsonl
python .agents/skills/council-flow/scripts/efficiency.py digest run --artifacts local-evidence/run-01 --digest-output local-evidence/run-01/digest.json --timeout 30 -- python -m unittest discover -s tests
python .agents/skills/council-flow/scripts/efficiency.py digest expand local-evidence/run-01/digest.json stderr
```

A minimal `record-input.json` looks like this:

```json
{"run_id":"task-01","harness":"codex","route":"codex/native-or-configured"}
```

Full permitted command output stays available for hash-checked expansion. Compact handoffs keep
the original criteria and all mandatory native roles, independent tests and Reviewer reruns. No
developer checkout is required.

## Adapters and safeguards

For adapter behavior and evidence and failure safeguards, read the packaged
[efficiency reference](../../.agents/skills/council-flow/references/efficiency.md).

## What is not established

- Offline parser tests do not prove live Codex or Claude Code or xKiro compatibility, which
  remains **LIVE_UNVERIFIED**.
- No native hook, billing or cache savings, effective upstream model identity, or subscription
  quota metering is claimed.
- The Package D evaluation protocol remains **DRAFT_NOT_AUTHORIZED** and is not in the
  distributable. No experimental trials are active. Existing research and backup branches and
  records are preserved.
