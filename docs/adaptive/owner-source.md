# Owner-message preservation and question packet (S7, ADR 4)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

## What it is

`experiments/adaptive-execution/owner_source.py` stores an Owner message's exact bytes
plus a hash record (`capture_owner_message`), re-verifies it (`verify_record`), keeps Planner
interpretations in separate files, validates Planner question packets, and checks that outbound
question text equals the packet's `exact_text` byte for byte (`check_outbound`). The caller
passes `store_dir`; the module has no default location and writes only inside it. Schema:
`experiments/adaptive-execution/schemas/owner-source.md`.

## What is preserved

Existing source-fidelity capture is unchanged. Wire roles and message contract 1.0 are unchanged.
Owner approvals and waivers stay in Council 001/R6 runtime state (D5); a question packet carries no
approval, and an unanswered question is never approval.

## Guarantee limits

Preservation here is a best-effort local file record, not authenticated capture and not transport
enforcement. Prompt instructions alone are not a guarantee. Where the host cannot expose the
original message, the record is UNVERIFIED. Anyone with file access can alter both bytes and
record; `verify_record` detects only bytes changed without a matching record change.

## Run

    python experiments/adaptive-execution/owner_source.py PACKET.json   # prints {"valid", "errors"}; exit 0 or 2
    python -m unittest discover -s experiments/adaptive-execution/tests
