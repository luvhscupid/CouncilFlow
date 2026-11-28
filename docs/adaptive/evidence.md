# Evidence records and Reopen Requests

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Implements ADR 3.3 and 7 (step S6).

**What it is.** Two standalone JSON artifact types (`experiments/adaptive-execution/evidence.py`, schema in
`experiments/adaptive-execution/schemas/evidence.md`): an evidence record (what an agent observed) and a Reopen Request
(a request to reassess the ledger). Adaptive mode stays opt-in (D3).

**What is preserved.** Roles stay Worker/Tester/Reviewer (D1); wire role names only. The message contract is closed and
unchanged: no new message type. Evidence cannot change a requirement (AC-S6b): any key such as `new_requirement`,
`ledger_change`, `decision`, `supersedes` or `status_update` is rejected as an unknown field, records only reference ledger
ids, and the module has no function that returns or writes a ledger. Only the Planner changes the ledger (S5). Owner
approvals stay in Council 001/R6 runtime state (D5). No database (D6).

**Reopen rule.** `classify_reopen(request, ledger)` gives `valid_for_reopen` only when at least one cited ledger entry id
exists in the supplied ledger and the request names the contradiction, includes supporting evidence, identifies affected
slices and states the consequence. Otherwise it gives `retained_as_evidence_only` plus reasons. It does not modify the ledger.

**Referencing from a message.** Save the record as a file, then list it in a `job.report` `evidence_refs` entry:
```json
{"artifact_id": "EV-1", "path": ".councilflow/runs/demo/evidence/EV-1.json",
 "sha256": "<lowercase sha256 of that file>", "kind": "adaptive-evidence"}
```
A Reopen Request uses `"kind": "adaptive-reopen-request"` the same way.

**Limits.** Artifact paths and hashes are checked for shape only, not for existence. Supporting evidence ids are not
resolved to files. The decision to reopen belongs to the Planner and Owner process, not this module.

**Run.**
```
python experiments/adaptive-execution/evidence.py FILE
python -m unittest discover -s experiments/adaptive-execution/tests
```
