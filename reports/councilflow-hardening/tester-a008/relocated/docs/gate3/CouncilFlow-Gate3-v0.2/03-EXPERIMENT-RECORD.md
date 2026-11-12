# Gate 3 Evidence and Results — BLANK TEMPLATE

**This is not an execution report. Every field remains unverified until filled from a real experiment.**

## Context
- Date/time and timezone:
- Codex product (local CLI / app / Cloud):
- Codex exact version:
- Shipped CouncilFlow commit:
- Disposable worktree / isolated copy path:
- Frozen criteria fixture path:
- Frozen criteria SHA-256:
- Initial exact invocation text, or path to unmodified copy:
- Source(s) of host evidence (screenshots/log IDs/thread records):
- Skill/config/policy unchanged? (host/working-tree evidence):

## Evidence table

| Check | Status (PASS/FAIL/BLOCKED/UNVERIFIED) | Class if not PASS | Source label | Verifiable reference | Notes |
|---|---|---|---|---|---|
| E1 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Listing: —; direct invocation: — |
| E2 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Was spawning requested explicitly? — |
| E3 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Count/types/thread labels: — |
| E4 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Effective TOML settings: — |
| E5 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Tester thread command evidence: — |
| E6 | UNVERIFIED | EVIDENCE_INSUFFICIENT | — | — | Separate Worker/Tester/Reviewer IDs: — |
| E7 | UNVERIFIED | EVIDENCE_INSUFFICIENT | OWNER-LOG | — | Courier count: —; authorizations: — |
| E8 | UNVERIFIED | EVIDENCE_INSUFFICIENT | RECORDED-EXECUTION | — | Tester command/result & Reviewer rerun: — |
| E9 | UNVERIFIED | EVIDENCE_INSUFFICIENT | OWNER-LOG | — | Planner/Manager plain English only: — |
| E10 | UNVERIFIED | EVIDENCE_INSUFFICIENT | DIFF | — | Original vs Planner criteria diff: — |

## E8 normalized stdout record
- Deterministic command as specified by Tester:
- Working directory, inputs/environment constraints:
- Normalization algorithm (e.g. normalize CRLF to LF only; no trimming of meaningful characters):
- Tester exit code:
- Tester normalized stdout SHA-256:
- Reviewer rerun exit code:
- Reviewer normalized stdout SHA-256:
- Direct comparison PASS/FAIL/NOT_COMPARABLE:
- Supporting authentic execution artifacts:

## E7 Owner interventions
| Event | Time | What happened | COURIER or AUTHORIZATION | Source |
|---|---|---|---|---|
| (none entered) | — | — | — | — |

## E10 criteria integrity
- Frozen fixture copy/hash:
- Planner criteria output copy/hash:
- Exact diff output:
- Metadata separated from criteria? (Y/N):

## Metrics (not a gate)
- Token usage:
- Coverage (which sessions/agents included):
- Host support unavailable? State `UNAVAILABLE`:

## Summary
- Run-level outcome (do not fill in advance):
- Failed checks:
- Blocked checks:
- Unverified checks:
- E3 stop rule triggered? Evidence:
- Owner decisions requested separately:
- **RAN/READ/CLAIMED provenance summary:**
