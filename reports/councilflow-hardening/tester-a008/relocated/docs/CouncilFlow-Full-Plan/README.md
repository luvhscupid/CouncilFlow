# CouncilFlow — Complete Planning and Execution Bundle

**Assembled:** 2026-11-11  
**Purpose:** Source-grounded plan and single-run instruction package for the **existing CouncilFlow Codex agent-skill repository**.  
**NOT:** A built/installable skill, a clone of the private CouncilFlow GitHub repository, a finished application, proof of native agent activation, or a newly approved Council architecture amendment.

## Start here

1. Read `00-SCOPE-AND-STATUS.md` to understand what is established and what is not.
2. Read `01-PRODUCT-AND-ROLES.md` and `02-PROTOCOL-AND-POLICY.md` for the outcome and communication contract.
3. Read `03-DELIVERY-AND-ACCEPTANCE.md` to prevent scope drift and premature completion.
4. To task Codex Cloud in one run, give it **`prompts/ONE-SHOT-CODEX-CLOUD.md`** in the existing `CouncilFlow` repository and make this bundle available to it. The prompt is also self-contained if you cannot add the archive.

### Critical invariant

**The product is a reusable, repository-scoped Codex agent skill that actually activates and completes a real coding task using distinct native agent sessions where available.** The protocol/validator/policy documents support the skill; passing validation tests alone is NOT completion.

### Contents

- `00-SCOPE-AND-STATUS.md` — truthful baseline, document authority, open issues.
- `01-PRODUCT-AND-ROLES.md` — owner-facing outcome, five AI roles, functional use.
- `02-PROTOCOL-AND-POLICY.md` — JSON/YAML/TOML/JSONL, examples, validation limits.
- `03-DELIVERY-AND-ACCEPTANCE.md` — build sequence, acceptance matrix, verification gates.
- `04-SECURITY-AND-LIMITS.md` — Codex permissions, forbidden changes, trusted claims.
- `05-OPERATIONS-AND-HANDOFF.md` — cloud workflow, usage, recovery, deliverables.
- `prompts/ONE-SHOT-CODEX-CLOUD.md` — unified full implementation/correction/verification prompt.
- `examples/` — example structured task messages and role policy (examples only).
- `source-docs/` — copies of retrieved historical source documents, preserving their own statuses.
- `SOURCE-MANIFEST.md` — provenance and status of sources.
- `SHA256SUMS.txt` — hashes of bundled files.

### Source status and conflicts

Council 001 **Architecture Specification v1.0** is source-recovered. Its subsequently approved **Security Annex v1.0-A original text is unavailable**: the included recovery note is NOT normative. `ACP-SPEC.md` is explicitly titled **PROPOSED / DESIGN ONLY** and should not be presented as the verbatim frozen v0.2.1 contract. The November 9 readiness assessment proposed infrastructure slices; it does not replace the Owner's current deliverable of a Codex skill. CouncilFlow uses Codex TOML for native agents; that does not negate YAML for Council policy.

No actual CouncilFlow cloud repository files were available in this container. Its last status is based on the provided Sol report: commit `d30e906`, skill package reportedly built, native skill discovery passed, direct `$council-flow` invocation unverified because of CLI authentication refresh, five role sessions reportedly participated through manual application of skill instructions. **Those claims have not been independently reproduced here.**
