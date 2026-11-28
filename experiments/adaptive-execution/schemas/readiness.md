# Readiness extension (S8)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.

Adaptive-mode readiness document = the S4 readiness plus, only for PROCEED_WITH_ASSUMPTIONS:

| field | rule |
| --- | --- |
| state | adaptive: READY, PROCEED_WITH_ASSUMPTIONS, BLOCKED. default mode: READY, NEEDS_INFORMATION, BLOCKED (unchanged); PROCEED_WITH_ASSUMPTIONS invalid |
| assumption_ids | nonempty list; each id an active (not superseded), provisional Assumption or Decision ledger entry |
| blocking_decision | must be `false` |

CLI document: `{"readiness": {...}, "ledger": {...}, "mode": "adaptive"|"default"}`.

Other inputs (Python API, not files): events `[{slice_id, cycle_kind}]` (max 2 `discovery` per slice);
config `{"unconfirmed_decision_limit": int >= 0}` (Owner-approved default 5 per project, passed in);
slices `[{slice_id, requires_new_defaults >= 0, blocking_decision, depends_on}]`.
The unconfirmed count is derived from the ledger, never stored.

Decision classes: cheap_reversible (Planner provisional default, proceed); costly_reversible (Owner
approval, pause affected slice); irreversible_or_external, security_data_financial_legal,
owner_controlled (Owner approval, block). Approvals live in Council 001/R6 runtime state.
