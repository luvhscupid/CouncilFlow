# Requirements ledger schema (adaptive-1)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Source: ADR 3.1.

Top level (unknown fields are errors): `schema_version` = "adaptive-1"; `ledger_id` (nonempty string);
`ledger_version` (positive int, not bool, equals max `version_introduced`); `author_role` = "planner";
`entries` (nonempty list, non-decreasing `version_introduced`).

Entry fields (all required): `id` (unique), `type` (Goal, Requirement, Assumption, Constraint, Decision, Open),
`content`, `source_ids` (nonempty list), `status`, `timestamp` (ISO-8601, supplied by data),
`version_introduced` (positive int), `superseded_entry_ids` (earlier entry ids, may be empty),
`affected_slices` (list, may be empty).

Status by type: Goal/Requirement/Constraint = established; Assumption/Decision = provisional, confirmed, rejected;
Open = open.

Optional: `approval_ref` (Decision only) and `promotion` (Requirement/Decision only) are read-only artifact refs
`{artifact_id, path (repo-relative POSIX), sha256 (lowercase hex), kind}` into Council 001/R6 runtime state (D5).
`promotion` = `{authority: owner_confirmation | preapproved_delegation_rule, approval_ref}`; required when a
Requirement or Decision supersedes an Assumption. Authority "planner" is rejected.

Append-only (`check_append_only(old, new)`): old entries must be canonical-JSON identical at the same positions;
only appends; `ledger_version` and `ledger_id` stable/non-decreasing. Changes are new superseding entries.
