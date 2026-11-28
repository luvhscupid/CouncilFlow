# Owner source records and question packet (schema adaptive-1)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

## Source record `<source_id>.json` (bytes in `<source_id>.txt`)

| Field | Rule |
|---|---|
| schema_version | `"adaptive-1"` |
| source_id | immutable, unique, `[A-Za-z0-9][A-Za-z0-9_-]*`; generated as `OS-0001`, `OS-0002`, ... or supplied |
| sha256 | lowercase hex SHA-256 of the exact stored bytes |
| byte_length | integer length of the stored bytes |
| received_at | caller-supplied ISO-8601 timestamp with timezone (never invented) |
| kind | `"owner-message"` |

Owner responses are captured as further, separate source records.

## Planner interpretation `<interpretation_id>.interpretation.json`

`{interpretation_id, source_id, text, author_role}`; `author_role` is `"planner"`. Separate file; never replaces a source.

## Question packet

Exactly: `question_id` (string), `exact_text` (string, compared byte for byte), `blocking` (bool),
`reversibility` (`cheap_reversible` | `costly_reversible` | `irreversible_or_external` |
`security_data_financial_legal` | `owner_controlled`), `affected_slices` (list of strings),
`permitted_default` (string or null; null unless `cheap_reversible`), `reason` (string).
Fields `approved` and `default_applied` are rejected: a question is not an answer.
