# Role aliases (step S2)

Optional, standalone display-name helper; not used by the skill or the wire contract.

**What:** `experiments/adaptive-execution/role_aliases.json` maps three ADR display
names to existing roles: Software Engineer -> worker, QA Engineer -> tester,
Technical Audit Director -> reviewer. Owner decision (2026-11-27): the roles stay
Worker/Tester/Reviewer; aliases are Owner-facing display text only.

**Preserved:** message contract 1.0 is unchanged. Wire roles remain
worker/tester/reviewer/planner/manager (plus `owner` in contracts.py). Aliases
never appear as sender/recipient roles. Default behavior is unchanged.

**Limits:** no runtime hook uses the aliases; `validate_wire_untouched` is a
checker for message-shaped JSON, not enforcement. Hand-written validation only.

**Run:**
- `python experiments/adaptive-execution/role_aliases.py FILE` (prints valid/errors; exit 0 or 2)
- `python -m unittest discover -s experiments/adaptive-execution/tests`
