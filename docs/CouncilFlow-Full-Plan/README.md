# CouncilFlow Full Plan (planning bundle)

**Assembled:** 2026-11-11
**Status:** Historical planning and single-run instruction bundle. It is not normative for the current product, and it does not establish verified implementation status.

## What this is

A source-grounded plan and single-run instruction package for the existing CouncilFlow Codex agent-skill repository. It records the intended outcome, the delivery sequence and the known source gaps as they stood on 2026-11-11.

## What this is not

- Not a built or installable skill.
- Not a clone of the private CouncilFlow GitHub repository.
- Not a finished application.
- Not proof of native agent activation.
- Not a newly approved Council architecture amendment.

The product this plan targets is, per the research index, a multi-agent workflow skill for existing AI coding environments, currently Codex-native. The bundle itself is not that installed skill. CouncilFlow is not a standalone AI agent, application, or runtime. The roles rely on the host's models, tools and native delegation.

## Critical invariant

**The product is a reusable, repository-scoped Codex agent skill that actually activates and completes a real coding task using distinct native agent sessions where available.** The protocol, validator and policy documents support the skill. Passing validation tests alone is not completion.

## Start here

1. Read `00-SCOPE-AND-STATUS.md` to see what is established and what is not.
2. Read `01-PRODUCT-AND-ROLES.md` and `02-PROTOCOL-AND-POLICY.md` for the outcome and communication contract.
3. Read `03-DELIVERY-AND-ACCEPTANCE.md` to avoid scope drift and premature completion claims.
4. `prompts/ONE-SHOT-CODEX-CLOUD.md` is a self-contained instruction artifact for a Codex Cloud run. This README does not authorize running it.

## Contents

- [`00-SCOPE-AND-STATUS.md`](00-SCOPE-AND-STATUS.md): truthful baseline, document authority and open issues.
- [`01-PRODUCT-AND-ROLES.md`](01-PRODUCT-AND-ROLES.md): owner-facing outcome, the five AI roles and functional use.
- [`02-PROTOCOL-AND-POLICY.md`](02-PROTOCOL-AND-POLICY.md): JSON, YAML, TOML and JSONL formats, examples and validation limits.
- [`03-DELIVERY-AND-ACCEPTANCE.md`](03-DELIVERY-AND-ACCEPTANCE.md): build sequence, acceptance matrix and verification gates.
- [`04-SECURITY-AND-LIMITS.md`](04-SECURITY-AND-LIMITS.md): Codex permissions, forbidden changes and trusted claims.
- [`05-OPERATIONS-AND-HANDOFF.md`](05-OPERATIONS-AND-HANDOFF.md): cloud workflow, usage, recovery and deliverables.
- [`prompts/ONE-SHOT-CODEX-CLOUD.md`](prompts/ONE-SHOT-CODEX-CLOUD.md): unified implementation, correction and verification prompt.
- [`examples/`](examples/): example structured task messages and a role policy. These are examples only.
- [`source-docs/`](source-docs/): copies of retrieved historical source documents, each keeping its own status.
- [`SOURCE-MANIFEST.md`](SOURCE-MANIFEST.md): provenance and status of each source.
- [`SHA256SUMS.txt`](SHA256SUMS.txt): hashes of the bundled files.

## Source-of-truth status

- **Council 001 Architecture Specification v1.0** is source-recovered and is the historical source for trust architecture.
- **Security Annex v1.0-A**: the original approved text is unavailable. The included recovery note is a secondary reconstruction and is **not normative**. Its compatibility with the original is unverified.
- **`ACP-SPEC`** (`source-docs/ACP-SPEC-v0.1-PROPOSED.md`) is marked **PROPOSED / DESIGN ONLY**. Do not present it as the verbatim frozen v0.2.1 contract.
- **November 9 readiness assessment**: proposes infrastructure slices. It does not replace the Owner's deliverable of a Codex skill and does not show completion.
- **Pre-v1 sources** (Council R4 and R6): historical. Superseded where inconsistent.
- **Format choices**: CouncilFlow uses Codex TOML for native agent configuration. That does not rule out YAML for Council policy.

### Evidence limits

No CouncilFlow cloud repository files were available when this bundle was assembled. Its status claims come from a provided report: commit `d30e906`, a skill package reportedly built, native skill discovery reportedly passed, direct `$council-flow` invocation unverified because of CLI authentication refresh, and five role sessions reportedly participating through manual application of the skill instructions. **None of these claims have been independently reproduced in this bundle.**

## Precedence and later documents

This bundle is "older CouncilFlow documentation" for the purposes of the Gate 3 package. Where it conflicts with the Owner Charter or the frozen Gate 3 v0.2 specification, those controlling documents win. See [`../gate3/README.md`](../gate3/README.md). The research records in [`../research/README.md`](../research/README.md) are non-normative and do not change this bundle's content.

For the root project contract, see [`../../AGENTS.md`](../../AGENTS.md).
