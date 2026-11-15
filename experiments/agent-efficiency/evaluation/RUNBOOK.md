# Recording procedure — DRAFT_NOT_AUTHORIZED

Only section 1 is runnable during protocol preparation. Sections 2–4 describe
future work after actual Owner approval; they authorize no calls. No new runner,
hook or benchmark framework is installed. Run from the repository root.

## 1. Offline preparation validation (zero model requests)

The following uses existing synthetic fixtures and one harmless local Python
command. It creates temporary artifacts outside the repository. No Claude/Codex
CLI is invoked. The evaluator's numbers are fixture checks, not approved budgets.

<!-- offline-validation:start -->
```python
from pathlib import Path
import json, subprocess, sys, tempfile
base = Path('experiments/agent-efficiency').resolve()
draft = json.loads((base/'evaluation/protocol.draft.json').read_text())
assert draft['status'] == 'DRAFT_NOT_AUTHORIZED'
assert draft['owner_approval'] is None
assert draft['execution_protocol_sha256'] is None
assert all(v is None for v in draft['required_owner_decisions'].values())
assert draft['proposals_not_approvals']['pairs'] == 6 * 2
scratch = Path(tempfile.mkdtemp(prefix='councilflow-phase5-preparation-'))
for name, extra in [('codex', []), ('claude', ['--gateway','xkiro','--gateway-source','synthetic-fixture'])]:
    fixture = 'codex-exec-sanitized.jsonl' if name == 'codex' else 'claude-stream-sanitized.jsonl'
    proc = subprocess.run([sys.executable, str(base/f'{name}_adapter.py'),
        str(base/'fixtures'/fixture),
        '--source','synthetic-fixture','--artifacts',str(scratch/name),
        '--records',str(scratch/f'{name}-records.jsonl'), *extra], capture_output=True)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result['complete'] and result['record']['usage']['reported_cost'] is None
    assert result['record']['acceptance']['status'] == 'unknown'
    assert result['process_exit_code'] is None
    assert result['session_usage'] is None
proc = subprocess.run([sys.executable,str(base/'digest.py'),'run',
    '--artifacts',str(scratch/'test-output'),'--digest-output',str(scratch/'digest.json'),
    '--',sys.executable,'-c',"import sys; print('test-owned fixture'); sys.exit(3)"],capture_output=True)
assert proc.returncode == 3
proc = subprocess.run([sys.executable,str(base/'digest.py'),'expand',
    str(scratch/'digest.json'),'stdout'],capture_output=True)
assert proc.returncode == 0 and proc.stdout in (b'test-owned fixture\n', b'test-owned fixture\r\n')
proc = subprocess.run([sys.executable,str(base/'evaluate.py'),'evaluate',
    str(base/'fixtures/paired-evaluation.json'),'--minimum-improvement','0.10',
    '--minimum-reliability','0.95','--budget','5'],capture_output=True)
assert proc.returncode == 0
report = json.loads(proc.stdout)
assert report['approval_status'].startswith('NOT_APPROVED')
assert report['digest_missed_failures'] and report['spending']['known'] is False
print('Offline adapter/digest/evaluator fixture checks passed:', scratch)
```
<!-- offline-validation:end -->

Save that block to a temporary Python file or execute it through PowerShell's
`@' ... '@ | python -` here-string. Also run:

```powershell
python -m unittest discover -s experiments/agent-efficiency -p 'test_*.py' -q
git diff --check
```

## 2. Future authorization and fixture qualification gate — NOT RUN NOW

1. Fill every required Owner decision in the JSON draft with actual, traceable
   decisions. Approve task/oracle manifests and independently qualify them using
   the valid and seeded-defect local controls. Approve the fixed native workflow,
   Tester/Reviewer bindings, costs/quota/all-role call limits and stop mechanism.
2. Establish an already authorized safe route and perform only the separately
   approved compatibility qualification. A configured endpoint, login label or
   estimated CLI cap is insufficient. Without this evidence, keep LIVE_UNVERIFIED
   and stop before invoking a model. C1/C2 do not enforce spending limits.
3. After approval, create a **separate** execution version and immutable approval
   record outside this draft directory. Bind exact protocol, task/oracle/prompt
   bytes and hashes to Owner evidence before the first controlled run. Verify
   those bytes before every arm. Hashes alone do not prove approval. Do not hash
   this draft as if it were authorized, or modify it into a fake approved record.
4. Operator creates separate task copies in an approved scratch root, records
   the starting-tree hashes and applies the approved AB/BA schedule. Use the same
   permitted runtime profile for both arms. Recheck version/route without secrets;
   drift stops the block. Do not clean/reset this project or activate integration.

## 3. Future invocation and recording — templates, not execution

For the proposed Codex block, the fixed underlying CLI argv is:

```text
codex exec --json --ephemeral --sandbox workspace-write --skip-git-repo-check --cd <fresh-arm-directory> -
```

Supply the frozen arm prompt on stdin. `workspace-write` is a proposed profile
requiring approval; do not change native permissions to obtain a result. The
operator invokes it outside an active coding-agent session; do not recursively
launch agents or CouncilFlow from this preparation chat. The arm prompt carries
the same coding goal and existing workflow in A/B. Only B adds the declared test
wrapper instruction. No model/provider switch or automatic fallback is permitted.

Do not redirect CLI JSONL to a transcript file or run the model command through
`digest.capture`: that would persist private message/reasoning payloads. The
future operator uses this **in-memory** sequence with the existing adapter:

```python
# FUTURE PROCEDURE FRAGMENT ONLY; not runnable without approved run variables.
# First verify real Owner approval, frozen bytes, external spending guard,
# remaining all-role budget, independent-role bindings and planned arm schedule.
import subprocess, time, hashlib, json
import codex_adapter
from recorder import append_jsonl
started = time.monotonic_ns()
proc = subprocess.run(argv, input=frozen_prompt_bytes, capture_output=True,
                      cwd=approved_arm_directory, timeout=approved_remaining_seconds)
elapsed_ms = (time.monotonic_ns() - started) // 1_000_000
parsed = codex_adapter.process(proc.stdout, artifact_dir=fresh_private_artifact_dir,
    run_id=unique_attempt_id, repository_revision=frozen_task_revision,
    elapsed_ms=elapsed_ms, process_exit_code=proc.returncode,
    cli_version=observed_cli_version, source='supplied-capture')
parsed['capture_metadata'] = {'stderr_sha256': hashlib.sha256(proc.stderr).hexdigest(),
                              'stderr_bytes': len(proc.stderr)}
# Write parsed JSON and append the RunRecord once, to private ignored paths.
# Never print or save proc.stdout/proc.stderr; discard them after sanitization.
# Use exclusive creation for the sidecar/parsed JSON to avoid overwriting evidence.
append_jsonl(private_records_path, parsed['record'])
```

On timeout/cancellation, stop the direct process, retain only permitted sanitized
partial metadata, pass `process_exit_code=None` when unobserved and `cancelled=True`
when observed. Record the stop and failed/censored attempt; do not silently retry.
Native cancellation/process-tree behavior remains a qualification gap. Invocation
elapsed time above is only one phase; sidecar total wall time ends after final
Tester/Reviewer disposition. All their model calls and usage also count.

If a separate Claude block is later approved, its corresponding fixed argv is:

```text
claude --print --output-format stream-json --verbose --no-session-persistence
```

Run in the approved arm directory, prompt on stdin, same approved native profile
in A/B, then use `claude_adapter.process` in memory with explicit observed
`gateway='xkiro'`, `gateway_source='configured'`, configured model/version and
observed exit. Never derive effective upstream or price from configured labels.
This alternative is **not** a second authorized block or an access workaround.

For B only, the task prompt specifies this exact wrapper form around the frozen
test command (A uses that underlying command directly with native output):

```text
python <toolkit>/digest.py run --artifacts <fresh-test-artifacts> --digest-output <fresh-digest.json> --timeout <approved-test-seconds> -- <python> -m unittest discover -s <task-test-directory> -p test_*.py -v
python <toolkit>/digest.py expand <digest.json> stdout
python <toolkit>/digest.py expand <digest.json> stderr
```

Expand as needed, especially DIGEST_INCOMPLETE or uncertain failures. Record
wrapper adherence, excerpt misses, expansion requests and outcomes using native
observations/operator ledger; these are not automatically collected today.
Tester/Reviewer always receive full permitted test evidence, not just digests.

## 4. Record and analyze without overstating evidence

For each attempt, save the schema-valid RunRecord unchanged and fill the JSON
sidecar template with references to permissions, candidate/oracle/prompt hashes,
all-role metering and independent acceptance evidence. Fill every unknown field's
reason. External verifier evidence is necessary; adapter `complete` is not task
acceptance. Do not add `task_id` to RunRecords, which reject extra properties.

Retain failed/abandoned attempts, verification overhead and arm censoring. Sum
only non-overlapping source counters at known scopes; never infer API-call counts
from assistant messages or assume final-turn usage is whole-session usage. If
all-role metering is incomplete, mark the corresponding aggregate UNKNOWN.
Calculate all-attempt/all-role cost divided by accepted tasks only when reliable
complete costs exist. Zero accepted tasks gives an undefined ratio. Record wall
time per accepted task separately; unknown money cannot be imputed from tokens.

The legacy evaluator expects enriched paired objects, not raw adapter records.
No production sidecar-to-evaluator bridge or approval-aware decision engine
exists. Its fixture command in section 1 only validates a descriptive path.
Use the frozen task-level analysis/independent evidence and PROTOCOL.md stop
rules; never treat a helper's provisional outcome as a promotion decision.

## Preparation validation actually performed — 2026-11-15

Only the marked section-1 Python block was executed, by extracting it from this
file and compiling/executing that block locally. It passed: both adapter fixtures
produced valid incomplete-billing/unknown-acceptance records, test-owned command
exit 3 and byte-preserving expansion matched, and the evaluator retained missing
spend and its NOT_APPROVED status. Temporary evidence directory:
`C:\Users\cupid\AppData\Local\Temp\councilflow-phase5-preparation-xdrms1en`.
Those synthetic outputs are not trial observations or an authorized protocol.

`python -m unittest discover -s experiments/agent-efficiency -p 'test_*.py' -q`
ran 76 tests: 73 passed, 3 existing platform skips (two real symlink checks and
one POSIX signal check). `git diff --check` passed. Draft JSON, local document
links and preparation-only/null-approval invariants were validated. No toolkit
source, live skill, research specification or configuration was changed.
