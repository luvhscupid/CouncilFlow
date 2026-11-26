# Plan: fix the findings from the lifegrid-1 run

Date: 2026-11-25. Status: **plan only, nothing implemented.**
Source: `councilflow-runs/lifegrid-1/RUN-RECORD.md` (project files), sections
"New CouncilFlow bugs" (items 1 to 8) and "Friction (recurring)" (items 9 to 15).

Item numbering used below:

| # | Item | Kind |
|---|---|---|
| 1 | One changed evidence file locks the run folder forever (and the dashboard cascades) | bug |
| 2 | Rework instructions have no home in the packet | bug |
| 3 | A second Tester assignment for the same attempt is accepted | bug |
| 4 | Error-path deterministic commands cannot be compared (no stderr hash) | bug |
| 5 | Accepting is impossible after any failed Reviewer report on an attempt | bug |
| 6 | `approval.decision` cannot be saved | bug |
| 7 | Evidence kinds are not checked against their field or role | bug |
| 8 | lifegrid watch mode piped into `head` exits 1 with a BrokenPipeError traceback | app bug |
| 9 | Role TOMLs point at `~/.agents/...`; path styles mix | friction |
| 10 | Field shapes live only in `contracts.py`; no example packets ship | friction |
| 11 | No helper to build artifact refs from a path | friction |
| 12 | No way to pre-check a packet against its assignment without `save` | friction |
| 13 | No field for "passed with unverified sub-aspects" | friction |
| 14 | Staging folder and manifest conventions undefined; copied assignments carry stale text | friction |
| 15 | Watch mode BrokenPipeError (side finding) | app bug, **same issue as 8** |

Items 8 and 15 are the same defect listed twice in the run record. They get one
fix (see 8/15).

## Base and authority

- **Base:** PR 21 (`claude/project-thread-cgwv23`, commit 3cd2c0b, open). This
  work branches from it (`claude/project-thread-his4vw`) and is retargeted to
  `main` once PR 21 merges. The lifegrid run itself used the PR 21 build, so every
  finding below is against PR 21, not `main`.
- **What PR 21 already touches:**
  - Item 1: PR 21 bug 2 (`plan_ref_reused`, per-revision `plan-rN.json`) removed
    one way to lock a run (overwriting the plan). Evidence files are still
    unprotected, which is what happened here. Same function (`save_message`) and
    same error class.
  - Item 2 and item 5: PR 21 bugs 1 and 4 changed the `job.assign` payload
    (`plan_task_id`) and `_check_assign` attempt rules. Items 2, 3 and 5 edit the
    same code paths.
  - Item 12: PR 21 added `planner_contract.py plan` (pre-check for plans only).
    Item 12 extends the same idea to every packet.
  - Item 10: PR 21 grew `communication.md` with field rules, but still no example
    packets.
  - Items 3, 4, 6, 7, 8/15, 9, 11, 13, 14: not touched by PR 21.
- **Authority.** Items 1, 3, 6, 7, 9 to 12 and 14 are helper-script, dashboard and
  doc fixes inside the existing contract. Items 2, 4, 5 and 13 change the message
  contract or the verification flow, and item 4 extends the Reviewer comparison
  written into the Owner Charter (`01-OWNER-CHARTER.md`: "compares exit code and
  normalized-stdout SHA-256"). Those need cupid's decision before their batch
  starts (see "Decisions needed"). No change to role order, role authority or the
  frozen Gate 3 records.

## Contract versioning (applies to batches 3 and 4)

New required fields would make every already-saved run folder fail
revalidation. To keep old runs valid, new packets declare `"version": "1.1"`:
- `contracts.py` accepts `"1.0"` and `"1.1"`. Rules added in this plan are
  required only on `1.1` packets.
- `save` refuses a `1.0` packet appended to a run that already holds a `1.1`
  packet (no downgrading mid-run).
- Docs and example packets use `1.1`.

Test: every saved packet in `councilflow-runs/{tabsplit-1,dashboard-issues-1,lifegrid-1}`
still validates with `sequence` after the change (fixture replay, see Batch 0).

## Batches

Each batch is one commit on the branch, with its tests written first and seen
failing on the PR 21 head. Plugin copy and `dist/` are rebuilt once, in Batch 5,
so the zip files do not conflict between commits.

| Batch | Items | Needs a decision first? |
|---|---|---|
| 0. Test scaffolding | none (fixtures + test file) | no |
| 1. Tooling and small contract fixes | 6, 7, 9, 11, 12 | no |
| 2. Evidence integrity | 1, 14 | D1 |
| 3. Contract additions (version 1.1) | 2, 4, 13 | D2 |
| 4. Verification flow | 5, 3 | D3 |
| 5. Docs, examples, packaging | 10 (+ docs for all), plugin sync, `dist/` | no |
| 6. App fix as a validation run | 8/15 | D4 |

Batch 1 and Batch 2 can start right away; Batch 2 waits only on D1. Batches 3 and
4 wait on D2 and D3. Batch 5 comes after 3 and 4 because the example packets must
show the final contract.

---

## Batch 0: test scaffolding

- Copy the saved packets and their cited files from the three real runs into
  `tests/fixtures/real-runs/` (lifegrid-1, lifegrid-1-r2, tabsplit-1,
  dashboard-issues-1), keeping paths so `--root` hash checks work. Strip nothing
  else; these are already project data with no secrets. Size check before commit
  (lifegrid dashboards are 400+ KB and are not needed; leave them out).
- New file `tests/test_lifegrid_regressions.py`, one `TestCase` class per item
  (`Item01EvidenceLock`, ... `Item14Staging`). Every test must fail on 3cd2c0b.
- A replay test: each fixture run validates with `contracts.py sequence --root`
  (guards the versioning rule above).

Risk: low. The fixtures are large-ish; keep to message packets plus the files they
cite.

## Batch 1: tooling and small contract fixes

### Item 6: `approval.decision` cannot be saved

**Change.**
- `save_message(raw, run_dir, *, root, expected_sender, owner_provenance=())`;
  the `save` CLI passes `--owner-provenance` through (today it is accepted by the
  parser but dropped in save mode).
- When `save` accepts an `approval.decision` with a provenance identity supplied
  on the command line, it appends that identity to `<run>/owner-provenance.json`
  (append-only list, never rewritten). Later `save` calls read that file and pass
  it to `validate_sequence`, so the saved decision keeps validating.
- `dashboard.py` reads the same file.
- Docs: `communication.md`, `recovery.md` (replace the "carry the Owner answer as a
  task.decision reason" workaround with the real packet).

**Files.** `scripts/contracts.py`, `scripts/dashboard.py`,
`references/communication.md`, `references/recovery.md`.

**Test.** Replay lifegrid-1-r2 M001 to M011, then an `approval.decision` replying
to M011 whose `provenance_ref` is `owner-decision-1.txt`:
`save --owner-provenance owner-decision-1` succeeds; the next `save` (a Manager
`task.decision` replying to it, no flag) succeeds; the same decision saved without
the flag is refused with `owner_provenance`.

**Risk.** Medium-low. `owner-provenance.json` is writable by any role, which is the
same trust level as the CLI flag today (the host, not the script, observes the
Owner). Document that only the Manager writes it, and only from an observed Owner
message.

### Item 7: evidence kinds not checked

**Change.**
- A per-field kind table in `contracts.py`, built from the kinds actually used in
  the three real runs: `plan_ref`→`plan`, `candidate_ref`/`input_candidate_ref`→
  `candidate`, `oracle_ref`→`oracle`, `tester_report_ref`→`message`,
  `provenance_ref`→`owner-provenance`, `evidence_ref`/`tester_evidence_ref`/
  `operation_ref`→`evidence`, `input_refs`→`input|oracle`, `evidence_refs`→any of
  `evidence|message|plan|oracle|candidate|owner-provenance`.
- `owner-provenance` in `evidence_refs` is allowed only for an artifact already
  recorded as Owner provenance in the run (from item 6's file or `--owner-provenance`).
- When the same artifact id is cited with a different kind, refuse with a new code
  `artifact_kind_changed` naming the first packet and kind, instead of the generic
  `artifact_identity`.

**Files.** `scripts/contracts.py`, `references/communication.md`
(kind table), `references/message-contract.json`.

**Test.** The lifegrid plan.check case: an artifact first cited as
`owner-provenance` in M012, then as `evidence` in a later packet, is refused with
`artifact_kind_changed` and a message naming M012. `provenance_ref` with kind
`evidence` is refused with `artifact_kind`. All real-run fixtures still validate.

**Risk.** Medium. A new refusal can reject packets that pass today. The table is
derived from real usage and the fixture replay test guards it.

### Item 9: role TOML paths

**Change.**
- `.codex/agents/*.toml`: replace `~/.agents/skills/council-flow/...` with the
  repo-relative `.agents/skills/council-flow/...` used by the skill, README and
  worker TOML (the default install is per repo; the README calls user-wide install
  optional). Add one line: "if the skill is installed user-wide, the same paths
  are under `~/.agents/`".
- One path style in the skill docs: repo-relative for files in the user's repo,
  skill-relative (`references/...`) only inside the skill's own files. Fix the
  mixed cases.
- `doctor.py`: new check that every `.agents/...` path named in a role TOML or
  plugin agent file exists in the install.

**Files.** `.codex/agents/council-{planner,worker,tester,reviewer}.toml`,
`plugins/councilflow/agents/*.md` (via build), `scripts/doctor.py`, skill
references with mixed paths.

**Test.** `doctor.py` on the repo reports no missing role paths; a copy with a TOML
pointing at a missing file reports it. A test greps the TOMLs for `~/.agents` and
expects none.

**Risk.** Low. Release archives include the TOMLs, so `dist/` changes (Batch 5).

### Item 11: artifact-ref helper

**Change.** `contracts.py ref <path> --root . --kind <kind> [--id <artifact_id>]`
prints a ready `{"artifact_id","path","sha256","kind"}` object (path relative to
root, refuses paths outside it or symlinks, kind checked against item 7's table;
default id derived from the file name).

**Files.** `scripts/contracts.py`, `references/communication.md`.

**Test.** Output for a fixture file equals the ref already saved in a real packet;
a path outside `--root` is refused; the printed ref passes `artifact(..., root)`.

**Risk.** Low. New read-only command.

### Item 12: pre-check without `save`

**Change.** `contracts.py save --dry-run` (or a `check` mode with the same
arguments) runs every check `save` runs, against the saved run plus the new
packet, and writes nothing. Output names the predecessor it bound to and echoes
the fields it compared (`candidate_ref`, `oracle_ref`, `input_candidate_ref`,
`attempt_id`).

**Files.** `scripts/contracts.py`, `references/communication.md`, role docs that
say "run save".

**Test.** A Tester report with a wrong `oracle_ref` is refused by `--dry-run` with
`oracle_binding` and no file appears in `messages/`; a correct one prints
`"saved": false, "would_save": true`.

**Risk.** Low.

---

## Batch 2: evidence integrity (needs D1)

### Item 1: one changed evidence file locks the run folder

**Change (recommended option A, see D1).**
- At `save`, every artifact the new packet cites is copied into a
  content-addressed store `<run>/evidence/sha256/<hash>` if not already there
  (never overwritten; size cap reuses the existing bounded-read limit; a candidate
  that is a directory manifest stores the manifest only).
- When `save` revalidates earlier packets, their hashes are checked against the
  store, not the working file. The new packet's own refs are still checked against
  the working files under `--root`.
- If a working file no longer matches a saved packet, `save` still saves and
  reports `"evidence_drift": [{"message_id","path","saved_sha256","current_sha256"}]`;
  the dashboard shows the same warning. Drift stops blocking the run but stays
  visible.
- Packets saved before this change have no store entries: on first revalidation
  `save` falls back to the working file (today's behaviour) and, if it matches,
  backfills the store.
- `dashboard.py` and `dashboard/run-reader.js`: a packet that fails no longer
  cascades. Validation continues with that packet excluded; its dependants are
  marked "depends on refused Mxxx" instead of "unknown predecessor".
- `recovery.md`: "new boundary" becomes the last resort, not the only exit.

Option B (smaller, weaker): revalidate earlier packets with `root=None` (structure
and sequence only). Earlier evidence then has no protection at all.

**Files.** `scripts/contracts.py`, `scripts/dashboard.py`,
`dashboard/run-reader.js`, `references/recovery.md`, `references/communication.md`.

**Test.** Replay lifegrid-1 M001 to M016, then overwrite
`staging/tester-2/AC7.txt` (as Tester 3 did): today the next save is refused with
`artifact_hash`; after the fix it saves and reports the drift for M010. The
dashboard for that run lists M010 with a drift warning and no "unknown
predecessor" for M011 to M016. A JS test (`dashboard` Node tests) covers the
non-cascade.

**Risk.** Medium-high. Biggest change in the plan: run folders grow by the size of
cited evidence; the fallback path for old runs must not let a changed file pass
silently (it reports drift instead).

### Item 14: staging and manifest conventions

**Change.**
- Document one layout in `communication.md`: `<run>/staging/<role>-<n>/` per role
  session (write-only for that session), `<run>/messages/` only via `save`,
  `<run>/evidence/` owned by `save` (item 1). A role never writes into another
  role's staging folder; that is what overwrote M010's evidence.
- Candidate manifest format (`candidate-attempt-N.txt`: one `sha256  path` line per
  file, sorted) written by a tiny helper `contracts.py manifest <dir>` so roles stop
  hand-writing it.
- Stale text: `save --dry-run` (item 12) warns when a `job.assign` names an
  `attempt-N` or staging path that differs from its own `attempt_id` or recipient.

**Files.** `references/communication.md`, `references/roles.md`,
`scripts/contracts.py`.

**Test.** `manifest` output for a fixture app folder equals the saved
`candidate-attempt-4.txt`; a `job.assign` for attempt-5 whose instructions say
"attempt-4" gets a `stale_text` warning (not a refusal).

**Risk.** Low. Warnings only; the layout is a convention, not enforced, because
roles run with the same permissions.

---

## Batch 3: contract additions, version 1.1 (needs D2)

### Item 2: rework instructions have no home

**Change.**
- `task.decision` with `disposition: rework` (version 1.1) requires
  `defects`: `[{"defect_id", "acceptance_ids", "summary", "evidence_refs"}]`.
- A Worker `job.assign` that replies to a rework decision requires
  `rework_scope`: `{"decision_id", "defect_ids", "instructions"}`. The Planner's
  `instructions` stay byte-for-byte (so `planner_contract.py assignment` still
  matches); the repair scope lives in `rework_scope.instructions`.
- Sequence checks: `decision_id` equals `in_reply_to`; every `defect_id` exists in
  that decision; every defect is covered by the new assignment.
- A Tester `job.assign` in that attempt may carry `oracle_change`:
  `{"supersedes_oracle_ref", "defect_ids", "reason"}` when its oracle differs from
  the previous attempt's, so the Reviewer can verify where an oracle rule came from
  (the r3/r4 error).

**Files.** `scripts/contracts.py`, `scripts/planner_contract.py` (ignore
`rework_scope` when matching), `references/{communication,workflow,roles}.md`,
`references/message-contract.json`, `dashboard/run-reader.js` (show defects).

**Test.** Built from lifegrid-1-r2 M012/M013: a 1.1 rework `job.assign` without
`rework_scope` is refused (`rework_scope_required`); one naming an unknown defect
is refused; a valid one passes `sequence` and `planner_contract.py assignment`.
The 1.0 originals still validate.

**Risk.** Medium. Contract change; every role doc that builds a rework assign
changes.

### Item 4: stderr hash for deterministic commands

**Change.**
- Tester `deterministic_commands[]` (1.1) adds required `stderr_sha256`
  (CRLF-to-LF normalized, same as stdout).
- Reviewer `independent_rerun` adds `stderr_sha256` and `tester_stderr_sha256`;
  `MATCH` requires exit code, stdout and stderr hashes all equal.
- Tester guidance: declare only commands whose stderr is deterministic (no
  timestamps, absolute temp paths or addresses).

**Files.** `scripts/contracts.py`, `references/{acceptance,communication,roles}.md`,
`references/message-contract.json`, `policies/roles.yaml`
(`reviewer_comparison` wording), dashboard reader.

**Test.** Two AC9-style commands with empty stdout, one printing a one-line
`error:` and one a usage block: same stdout hash, different stderr hash; a
Reviewer `MATCH` between them is refused. The real lifegrid DC1 packets (1.0) still
validate.

**Risk.** Medium. Extends the Charter's Reviewer rule (D2). Non-deterministic
stderr would cause false `MISMATCH`.

### Item 13: passed with unverified sub-aspects

**Change (recommended form, see D2).** Optional `unverified`:
`[{"acceptance_id", "aspect", "reason"}]` on Tester and Reviewer reports.
Informational only: it does not change pass/fail. A Manager `task.decision`
accept and the Planner's `plan.progress` must carry every `unverified` entry from
the reports they cite (sequence check), so the Owner sees them in the final
answer.

**Files.** `scripts/contracts.py`, `references/{acceptance,communication}.md`,
`references/message-contract.json`, dashboard reader.

**Test.** A passing Tester report with one `unverified` entry; a Manager accept that
drops it is refused (`unverified_dropped`); one that carries it passes and the
dashboard shows it.

**Risk.** Low technically. It was deferred in the tabsplit plan as an
acceptance-policy question, so it needs cupid's yes.

---

## Batch 4: verification flow (needs D3)

### Item 5: accepting is impossible after a failed Reviewer report

**Change (recommended).** A new rework form for "the candidate is fine, the
verification record was wrong": `task.decision` rework with
`rework_kind: "verification"` (1.1). It opens a fresh attempt on the **same**
candidate with no Worker step: the next `job.assign` goes to a fresh Tester
(`candidate_ref` unchanged, new `attempt_id`), then a fresh Reviewer. The failed
reports stay in the earlier attempt and remain cited by the rework decision.
`_check_assign` allows a Tester assign to reply to such a decision; the
accept rule is unchanged (no failed report in the accepting attempt; distinct
Tester and Reviewer sessions; each covers all criteria).

This removes the no-change Worker attempt the lifegrid run needed (attempt-5),
and nothing else.

**Files.** `scripts/contracts.py` (`_check_assign`, `_check_decision`),
`references/{workflow,roles,recovery}.md`, `references/message-contract.json`,
`SKILL.md` (one line in the Manager step), dashboard reader.

**Test.** Replay lifegrid-1-r2 to M011, then a verification rework, fresh Tester
(pass), fresh Reviewer (pass), Manager accept: saves. A verification rework whose
next assign changes `candidate_ref` is refused; a verification rework followed by
a Worker assign is refused; accept in the original failed attempt is still
refused.

**Risk.** Medium-high. It changes the visible role order for one path (Manager →
Tester instead of Manager → Worker → Tester), which is why it needs D3.

### Item 3: second Tester assignment in the same attempt

**Change.** Refuse a second Tester `job.assign` in the same attempt for the same
candidate (`retest_same_attempt`). The legitimate re-test path is item 5's
verification rework, which records why, preserves the failed report and, with
item 2, records any oracle change.

**Files.** `scripts/contracts.py` (`_check_assign`), `references/workflow.md`.

**Test.** lifegrid-1-r2 M005 (failed Tester) followed by M006 (second Tester assign,
same attempt) is refused for a 1.1 packet; the same through a verification
rework passes. The 1.0 originals still validate.

**Risk.** Medium. Without item 5 this would force a no-change Worker attempt for
every re-test, so 3 ships only together with 5.

---

## Batch 5: docs, examples and packaging

### Item 10: field shapes only in `contracts.py`; no example packets

**Change.**
- `references/examples/`: one valid 1.1 packet per message type and role
  (plan.publish, Worker/Tester/Reviewer job.assign and job.report, task.decision
  accept and both rework kinds, plan.progress, plan.check, approval.request,
  approval.decision), each with a matching file tree under
  `references/examples/files/` so `--root` checks pass.
- A field table in `communication.md` for `scope`, `checks`,
  `deterministic_commands`, `comparison`, `independent_rerun`, allowed `kind`
  values, generated from the same constants `contracts.py` uses (a small
  `tools/gen_contract_tables.py`, with a test that the doc is up to date).

**Files.** `references/examples/**`, `references/communication.md`,
`tools/gen_contract_tables.py`, `tests/test_skill_files.py`.

**Test.** Every example validates with `message --root` and the full example chain
validates with `sequence --root`; the doc-table test fails if a field is added to
`contracts.py` without regenerating.

**Risk.** Low. Release size grows slightly.

### Packaging

- `python tools/build_claude_plugin.py build` (plugin copy) and
  `python tools/build_release.py` (`dist/`), as PR 21 did.
- Full suites from RELEASE.md: `python -m unittest discover -s tests`, demos,
  reports, dashboard Python and Node tests.

---

## Batch 6: app fix as a validation run (needs D4)

### Items 8 and 15: lifegrid BrokenPipeError

**Change.** In `lifegrid.py` watch mode, catch `BrokenPipeError` around frame
writes and the final flush, point stdout at `os.devnull` so the interpreter's
exit flush does not raise again, and exit 0 quietly (same as `yes | head`).

**Where.** The app is not in the CouncilFlow repo; it lives in project files
(`councilflow-runs/lifegrid-1/app/`). Recommended: do it as a small new
CouncilFlow run (lifegrid-2) on the finished build. That fixes the app and is the
end-to-end check of batches 1 to 4 (rework_scope, stderr hash, dry-run, ref
helper, evidence store).

**Test.** `python3 lifegrid.py --pattern glider --watch | head -n 3` exits with
status 0 for `lifegrid` (checked with `PIPESTATUS`) and prints no traceback on
stderr; existing 58 unit tests still pass; a new unit test drives the watch loop
with a stdout that raises `BrokenPipeError`.

**Risk.** Low for the app. The run itself costs a full role cycle.

---

## Decisions needed from cupid

- **D1 (item 1): how to unlock a run after evidence changes.** Recommended: A,
  `save` keeps its own content-addressed copy of cited evidence and reports drift
  instead of refusing. Alternative: B, stop hash-checking earlier packets
  (simpler, but earlier evidence is then unprotected).
- **D2 (items 2, 4, 13): contract additions under version 1.1.** Recommended: yes
  to all three. Item 4 extends the Owner Charter's Reviewer rule from "exit code
  and normalized-stdout SHA-256" to also compare stderr; item 13 was deferred in
  the tabsplit plan as an acceptance-policy question and is proposed here as
  informational only.
- **D3 (items 5 and 3): verification-only rework.** Recommended: allow a rework
  that re-runs Tester and Reviewer on the same candidate in a fresh attempt
  without a Worker step, and refuse a second Tester assignment inside one attempt.
  This changes the role sequence for that one path.
- **D4 (items 8/15): fix the app?** Recommended: yes, as a small lifegrid-2
  CouncilFlow run that also serves as the end-to-end test of the fixes.
- **Merge order (no decision needed unless cupid prefers otherwise):** this work
  stacks on PR 21; PR 21 should merge first, then this PR retargets to `main`.

---

## Per-role model split (approved by cupid, 2026-11-26)

Approved as proposed. No model setting is changed by the plan's own commits
until the split is applied in Batch 5 (plugin agent frontmatter and Codex TOML,
each after its format is verified against the host docs).

| Role | Model | Why |
|---|---|---|
| Planner | Opus | Holds frozen criteria; final criteria check. A missed criterion is costly. |
| Worker | Sonnet | Multi-file code edits. |
| Manager | Sonnet | Coordination and packet writing. |
| Reviewer | Sonnet | Judgment across Worker, Tester and frozen plan; caught real defects in lifegrid-1. Never Haiku. |
| Tester (oracle design) | Sonnet | Designs the independent reference and test strategy. |
| Tester (command run and hashing) | Haiku | Mechanical: runs declared commands, records exit code and output hashes. |

Caveats: the split is a hypothesis until measured. The first real run after
Batch 5 must report whether Haiku's command runs and hashes match Sonnet's on the
same commands; if not, revert the Tester split.

### Item 16: record the model each role ran on (new, part of Batch 3)

- Every saved packet that is produced by a role session records the model that
  session actually ran on, as `sender.model` in version 1.1 (string, identity
  shape, required on 1.1 packets, optional on 1.0 packets).
- A Tester that delegates command runs to a Haiku sub-session records that
  sub-session's model in `deterministic_commands[].runner_model`.
- `save` and `sequence` check that `sender.model` is consistent for one role
  instance across its packets. A model change for the same instance is refused
  (`model_changed`).
- Reviewer's independent rerun records `runner_model` too. A Reviewer rerun run on
  a different model from the Tester's command run is allowed and reported, not
  refused: the rerun is independent evidence either way.

Files: `scripts/contracts.py`, `references/message-contract.json`,
`references/communication.md`, dashboard reader.
Test: a 1.1 packet without `sender.model` is refused; a model change within one
instance is refused; a 1.0 fixture still validates.

### Batch 5 addition: apply the split

- `plugins/councilflow/agents/council-{planner,worker,reviewer,tester}.md`:
  `model:` in frontmatter per the table (Tester gets Sonnet; its command runs are
  delegated to a Haiku sub-session whose model is recorded per item 16).
- `.codex/agents/*.toml`: the same mapping, only after the Codex custom-agent
  `model` field is verified in the Codex docs; otherwise leave Codex inherited and
  say so in the doc.
- Test: `tests/test_claude_plugin.py` checks each agent's frontmatter model
  matches the table.
