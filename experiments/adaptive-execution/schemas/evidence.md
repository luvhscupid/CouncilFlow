# Evidence record and Reopen Request schema (adaptive-1)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Standalone JSON artifacts (ADR 3.3, 7).
All fields are required; unknown fields are rejected. Records only reference ledger ids and cannot change a requirement.

## Evidence record
| field | type |
|---|---|
| evidence_id | nonempty string |
| source_agent | one of worker, tester, reviewer, planner, manager (display aliases rejected) |
| observation | nonempty string |
| artifacts | list of artifact refs `{artifact_id, path, sha256, kind}`; path repo-relative POSIX (no `..`, no leading `/`); sha256 lowercase 64 hex |
| ledger_ids | list of strings, may be empty |
| affected_slices | list of strings |
| timestamp | ISO-8601 with timezone |
| reopen_status | none, submitted, valid_for_reopen, retained_as_evidence_only, decided_ledger_changed, decided_no_change |

## Reopen Request
| field | type |
|---|---|
| request_id | nonempty string |
| submitter_role | one of the five wire roles |
| ledger_entry_ids | list of strings |
| contradiction_or_affected_assumption | nonempty string |
| supporting_evidence_ids | list of strings |
| affected_slices | list of strings |
| consequence | nonempty string |

`classify_reopen(request, ledger)` returns `(status, reasons)`: `valid_for_reopen` only if at least one cited id exists in the
supplied (valid) ledger and the contradiction, supporting evidence, affected slices and consequence are all present; otherwise
`retained_as_evidence_only` with reasons. It never modifies the ledger.
