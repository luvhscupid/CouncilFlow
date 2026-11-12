# Council 001 — Security Annex v1.0-A: Recovery Note

**Document status:** SECONDARY RECOVERY NOTE — **NOT** the original Annex, **NOT** the exact normative text, and **NOT** a replacement or amendment.
**Prepared:** 2026-11-09
**Audience:** Claude reviewing proposed Agent Communication Protocol (ACP) v0.2.1 against the earlier Council 001 baseline.

## Why this document exists

The Council 001 architecture was reviewed on 2026-10-29. The Owner later approved **Architecture Specification v1.0 plus Security Annex v1.0-A** as its frozen, normative reference design. A copy of the original Annex text has **not** been located in the available file library. The separately bundled `Council-001-Architecture-v1.0-Original-Source.txt` is a retrieved historical source of the architecture specification (titled "R7-Claude: Architecture Specification v1.0 (for Owner sign-off)"). This source predates the final approval but provides directly inspectable architecture text.

**Do not represent this recovery note as a verbatim Annex or mark Annex compatibility as verified.** Use `UNVERIFIED — ORIGINAL ANNEX TEXT UNAVAILABLE` for any clause that requires exact wording.

## Historically documented Annex subject areas (summary, not quoted clauses)

The earlier approval and subsequent summaries identify these topics as part of Annex v1.0-A, but their precise requirements, thresholds, exceptions, and ordering cannot be recovered reliably from the available files:

1. T1/T2 verifier threat model and separation between trusted supervisor observations and untrusted verification claims.
2. Independently evaluated negative-control canary for verification/evidence integrity; distinguish independently verified harness behavior from a self-reported pass.
3. Static test-discovery limitations: discovery or enumerated tests are not by themselves sufficient evidence of test execution/coverage.
4. Immutable, handle-validated artifact handling and Windows filesystem/path safeguards (including alias/reparse and path-race concerns).
5. Mandatory non-waivable containment properties, contrasted with low-risk, expressly waivable provider-only Worker egress; approvals are scope-bound and expire/revalidate as specified.
6. An enforcement manifest, dispatch sentinels, and revalidation when the effective enforcement environment changes or becomes stale.
7. High-risk hidden-check mutation quality requirements; when mandated mutation testing is infeasible, an explicit Owner-acknowledged gap may produce `ACCEPTED_WITH_GAP` rather than falsely claiming verification.
8. P0b security probes and their effects remained **unexecuted and unauthorized** at the Council review's closure.

These are **retrieval-supported subject summaries, not original Annex requirements**. They cannot authorize execution, replace the normative text, or settle policy conflicts.

## Inspectable requirements in the original architecture source

The bundled architecture source discusses:

- Distinct controller, Worker and restricted Verifier identities; trusted controller must not execute untrusted code.
- Worker change artifacts frozen into an immutable manifest before validation or reconstruction; path and alias rejection.
- Non-waivable containment; Verifier has no network or credentials; limited low-tier Worker egress waiver.
- Fresh attempt sessions; Codex resume disabled pending separate verification.
- Controller-observed execution facts vs verifier-reported claims; tests and hidden-check discrimination requirements.
- Risk-tier verification and Owner acceptance; limits and recovery mechanisms in earlier contracts.
- P0b as a **probe specification**, not approval to run the probes.

Consult source sections 1–11 and 13 for the original wording. Do not assume the architecture source fully incorporates the subsequently approved Annex.

## Compatibility questions for ACP v0.2.1

| Topic | Baseline risk | Required disposition |
|---|---|---|
| Restricted verification identity | A Tester model and Reviewer model are not equivalent to a restricted Verifier execution environment | Preserve the restricted runner for real code execution; do not equate declarative Slice 1 checks with full security proof |
| Immutable artifact validation | ACP sealing/hashing alone may omit exact Windows path/handle checks | Preserve until detailed Annex reconciled; fail closed before autonomous code execution |
| Negative controls and high-tier mutation testing | A normal green test suite may be nondiscriminating | Keep unresolved, distinguish `ACCEPTED_WITH_GAP` when eligible under exact policy |
| Effective enforcement, identity and egress | Job Object alone is insufficient to prove containment | P0b or equivalent approved proof required before real Codex Worker execution |
| Waivers/approval | Scope, expiry and protected properties must not be diluted by agent policy | Supervisor-enforced; only Owner may authorize waivable exceptions |
| Retries | ACP Owner has approved Manager-controlled engineering repair retries | ACP policy decision; does not automatically modify the older Council baseline outside ACP |

## New ACP decisions reported in the current discussion

- **O1 — Approved (ACP design scope):** Replace Council's fixed engineering repair counts in ACP with Manager-controlled repair/rework attempts, bounded by supervisor-enforced budgets, deadlines, authorization and evidence. Separate infrastructure retry and crash-recovery limits remain proposed, not yet approved. No implementation authorization.
- **O2 — Approved in principle:** Manager may make discretionary quality improvements using a *separate supervisor-enforced discretionary budget*. The amount is **not decided**. No implementation authorization.
- Remaining Owner decisions and exact original Annex compatibility are unresolved.

## Status to report to the Owner

The available historical architecture source can inform a provisional ACP compatibility checklist. **Exact compliance with Annex v1.0-A is unknown**, because the original Annex text was not recovered. Do not silently reconstruct normative clauses or claim a completed sign-off.
