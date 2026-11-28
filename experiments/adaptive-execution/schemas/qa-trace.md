# QA trace sidecar schema (adaptive-1)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Source: ADR 9.

Standalone JSON artifact, kind `adaptive-qa-trace`, referenced from the Tester job.report as an artifact ref
`{artifact_id, path, sha256, kind}`. No message type, field or role is added.

Top level (unknown fields are errors): `schema_version` = "adaptive-1"; `candidate_ref` (artifact ref or null);
`records` (list); `check_links` (list of `{check_name, test_id}`; `check_name` is a Tester `checks[].name`,
`test_id` must name a record).

Record fields (all required, no others): `test_id` (unique), `tested_behavior`, `ledger_ids` (nonempty list),
`slice_id`, `pinned_ledger_version` (positive int, not bool), `result` in passed|failed|blocked|unverified,
`evidence` (artifact ref), `timestamp` (ISO-8601 with timezone).

`validate_qa_sidecar(obj, ledger=None)`: with a ledger, every `ledger_ids` entry must exist and
`pinned_ledger_version` <= `ledger_version`.

`stale_results(ledger, records)`: a record is stale when one of its `ledger_ids` was superseded by an entry with
`version_introduced` > its pin (reason `superseded:<id>`); a superseded Goal also stales records whose `slice_id`
is in that Goal's `affected_slices` (reason `goal_changed`). `retest_scope(stale)` = sorted affected test_ids.
