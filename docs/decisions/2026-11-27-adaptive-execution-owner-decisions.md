# Owner decisions on the Adaptive Execution ADR (step S1)

**Date:** 27 November 2026
**Authority:** Owner, given in conversation; verbatim replies are preserved in `.councilflow/runs/adr-adaptive-i1-i4/source/owner-d1-d3-decisions.txt` (local, gitignored run evidence).
**Status:** Decision record only. It authorizes no code, schema, erratum, migration or any step other than creating this note (S1).
**Subject:** ADR "Adaptive Execution, Authority Separation, and Versioned Project State" (26 November 2026; implementation status: not authorized). Analysis: `.councilflow/runs/adr-adaptive-i1-i4/deliverable/inspection-and-migration-plan.md` (local run evidence; source revision unknown because git was unavailable).

This note does not edit or supersede any frozen record. Gate 3 records, Council Meeting 001 and role policies keep their authority until a separate Owner-approved record (for example an erratum like `docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md`) says otherwise.

| ID | Question | Owner decision (Owner reply) |
|---|---|---|
| D1 | ADR role names (Software Engineer, QA Engineer, Technical Audit Director) vs Worker, Tester, Reviewer | Keep Worker/Tester/Reviewer; the ADR names are display aliases only. ("Use your recommendations") |
| D2 | ADR "Planner never talks to the Owner" vs the Gate 3 charter's "Planner or Manager" output rule | Amend the charter by a separate erratum, never by editing it. The charter is unchanged until an erratum is separately authorized. ("Use your recommendations") |
| D3 | ADR "Manager sole owner of the execution plan" vs Planner-authored tasks and instructions | Opt-in "adaptive mode" in which both coexist; current behavior stays the default. ("Use your recommendations") |
| D4 | Is Council Meeting 001 signed off? | Yes. It is a frozen Owner decision that keeps its authority; whether the ADR amends its Planner/Manager split is not decided. ("Yes, signed off") |
| D5 | Where do Owner approvals and waivers live? | In the existing Council 001/R6 runtime state; any ledger holds read-only references only. ("Yes, keep existing") |
| D6 | May SQLite enter the product? | Deferred. The existing prohibition stays; durable event serialization (S10) waits for a later decision. ("Yes, defer SQLite") |

## Also recorded

- AC1 of the I1-I4 inspection run (only the deliverable changed) was accepted by the Owner on a file-timestamp check only; git was unavailable. ("Accept timestamp check")
- **D7 (which of migration steps S1-S11 to authorize):** only S1, this note, is authorized. Every other step needs its own separate Owner authorization.

## Not decided

- Whether the ADR amends Council Meeting 001's Planner/Manager split (its lines 26-27).
- Any erratum text, alias table, adaptive-mode design, ledger schema or other implementation.
