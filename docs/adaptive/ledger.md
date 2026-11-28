# Versioned requirements ledger

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11. Implements ADR 3.1 (step S5).

**What it is.** A standalone JSON artifact (`experiments/adaptive-execution/ledger.py`, schema in
`experiments/adaptive-execution/schemas/ledger.md`) holding Goal, Requirement, Assumption, Constraint, Decision and
Open entries with the eight ADR traceability facets. The Planner is the sole semantic writer (`author_role: planner`).
Adaptive mode stays opt-in (D3); nothing here changes default behavior.

**What is preserved.** Roles stay Worker/Tester/Reviewer (D1); the message contract is unchanged; the ledger is
referenced from messages only as an artifact ref. Owner approvals live in Council 001/R6 runtime state (D5): the
ledger holds read-only `approval_ref` references and has no field that grants approval. No database dependency (D6).

**Rules enforced.** Unique ids; supersession targets exist with a lower version; `ledger_version` equals the max
entry version; an Assumption cannot be superseded by a Requirement or Decision without a `promotion` block
(owner_confirmation or preapproved_delegation_rule, with approval_ref). `check_append_only(old, new)` rejects edits,
deletions, reordering and version decreases. `active_entries(ledger)` drops superseded entries.

**Limits.** The module does not verify that an `approval_ref` exists or hashes correctly, does not generate
timestamps, and does not enforce who wrote a ledger beyond the `author_role` field.

**Run.**
```
python experiments/adaptive-execution/ledger.py FILE
python -m unittest discover -s experiments/adaptive-execution/tests
```
