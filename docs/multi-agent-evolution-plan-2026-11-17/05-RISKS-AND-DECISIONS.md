# 05 — Risk register, decisions and governance

**Status:** PROPOSED, not permission to change product behavior. This is a pre-implementation design review, not a claim that the following risks are already mitigated.

## Hard boundaries inherited from CouncilFlow

- Preserve Owner control of consequential scope, authorization, subjective acceptance, release, spending, permissions and policy change. Agent recommendations never authorize themselves.
- Preserve original input, ordered frozen criteria, plan/source hashes, correct candidate identity, independent Tester evidence, Reviewer rerun/comparison, Manager decision, Planner final check. Do not relax these to save tokens.
- Maintain one mutating Worker per workspace until independent isolation and safe integration are **demonstrated**, not merely requested by a prompt.
- Never invoke a gateway, edit Claude/xKiro/Codex configs, connect OAuth subscriptions to an API proxy, retrieve credentials, change ACLs, weaken host permissions or publish a release because a plan mentions it.
- Do not erase or rewrite historical failures, amend the frozen Gate 3 protocol, reclassify prior UNVERIFIED native evidence, or start Slice 2 by implication.
- No assumption of a trusted Supervisor, atomic promotion, authenticated model identity or real OS sandbox until independent runtime enforcement is evidenced.

## Risk register

| ID | Failure mode | Consequence | Proposed detection and mitigation | Gate |
| --- | --- | --- | --- | --- |
| R01 | Feature copied from a differently licensed project | License violation or forced distribution changes | Conceptual rewrite; source manifest; counsel/license review before code copying | All |
| R02 | Source docs mistaken for runtime enforcement | Unsafe false security claim | Test actual host and OS boundary; label `UNVERIFIED` | P0-P4 |
| R03 | "Per-role model" is merely inherited root model | False independence/cost claims | Host capability probe; explicit inherit/unknown labels; reject unsupported override | P2 |
| R04 | OAuth subscription treated as general API credential | Unauthorized provider use or account/terms risk | Do not harvest/replay tokens; supported native auth only; separate approved API route | P2 |
| R05 | Gateway relabels reported upstream model | Incorrect quality/cost attribution | Configured, reported, effective recorded separately with provenance | P1-P2 |
| R06 | Snapshot token counters added repeatedly | Inflated usage, false cost savings | Explicit usage scopes; deduplication tests; unknown billing retained as null | P1/P6 |
| R07 | Compact handoff loses a failed assertion | False accepted implementation | Hash-preserved full output; fail-closed incomplete digest; targeted expand | P1/P5 |
| R08 | Journal append succeeds but state transition fails | Corrupt/replayed task state | Single transaction/CAS; crash injection; sequence and artifact-hash checks | P3 |
| R09 | Interrupted Worker resumes with stale authority | Unauthorized edits / stale promotion | Attempt/revision binding; validate live session/workspace/Owner approval; reject stale | P3 |
| R10 | File/path lock perceived as enforced isolation | Cross-agent edits, lost work | Isolated worktrees plus host sandbox; concurrency/TOCTOU tests; serial promotion | P4 |
| R11 | Reviewer modifies product code or trusts Worker self-test | Collapse of independence | No mutation permission for independent reviewers; real separate verification | All |
| R12 | Memory contains stale or poisoned instructions | Scope/permission escape, bias | Source-scoped reviewed lessons, no Worker auto-memory, supersession and poison tests | P5 |
| R13 | Dashboard renders "green" on missing events | Owner receives false confidence | Strict event contract; explicit SKIP/BLOCKED/UNVERIFIED; read-only projection | P5 |
| R14 | Optimization overfits easy benchmark tasks | Regression on realistic work | Multi-stratum fixtures, holdout tasks, independent oracles and failed attempts counted | P6 |
| R15 | Auto-experiment uses paid quota or changes main | Unapproved spend/deployment | Disable by default; exact authorized limits; separate branch; Owner merge gate | P6 |
| R16 | Independent council room imports malicious instructions | Prompt-injection or forged authorization | Untrusted-text envelope; immutable submission refs; no execution access; Owner publishes plan | P7 |
| R17 | More infrastructure than value | Maintenance burden and startup cost | Feature flag, dependency/footprint gate, no mandatory DB/server/cloud | All |
| R18 | Existing release artifacts and source diverge | Users install stale skill or mismatched plugin | Reproducible release packaging, byte-for-byte shared runtime, install-path tests | Every release |
| R19 | Concurrent branch work merges over newer decisions | Lost remediation or unauthorized Slice 2 | Refresh HEAD, compare plan authority, PR review and non-force merge | All |
| R20 | Public repo leaks prompts, keys or private traces | Privacy/security incident | Metadata allowlist, credential redaction, local evidence storage policy, scan negative controls | P1-P7 |

## License checkpoints

- **Forge:** FSL-1.1-ALv2 restrictions on competing commercial use, source available, delayed future Apache license. Ideas can inform independently written implementation; don't paste its code blindly. [License source](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/LICENSE.md).
- **Agyn:** current `agynio/platform` is AGPL-3.0; original `agynio/v1` is under a custom restrictive license. Keep implementations distinct, review copy/linking/distribution obligations before reuse. [Current license](https://github.com/agynio/platform/blob/6a778d39828aaf096dbe2b7f2ea676a48957404b/LICENSE).
- **MetaGPT:** MIT, subject to notice/copyright terms for actual reuse. [License](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/LICENSE).
- **CouncilFlow:** research found no root `LICENSE` in inspected `main` tree at baseline. Before distributing forked/copyleft components or making broad open-source promises, confirm the desired CouncilFlow project license with Owner; do not add one silently.

**This is a technical license flag, not legal advice.**

## Decisions Owner should make phase-by-phase

| Decision | Proposed default | Why it must be explicit |
| --- | --- | --- |
| D01 — Is this plan authoritative? | **No.** Research only | The frozen charter and accepted decisions outrank it |
| D02 — Which phase is next? | P0 read-only inventory; consider P1 only after separate approval | Current P1 benchmark protocol is DRAFT_NOT_AUTHORIZED |
| D03 — Model/route policy? | Inherit native host unless a capability-tested opt-in is approved | Can't turn Plus/Claude/xKiro subscriptions into API auth |
| D04 — Any paid trials? | None | Quota, route, unit and spend must be Owner-bound |
| D05 — Journal backend? | Compare SQLite against durable file/event approach in a design spike | Must prove crash/CAS semantics before choosing |
| D06 — Parallel execution? | Disabled by default | Real workspace isolation and integration validation needed |
| D07 — Lessons shared across projects? | No by default; scoped curated index | Memory poisoning and irrelevant carryover |
| D08 — Automatic self-improvement? | Candidate experiments only, never self-merge | Owner authorization and controlled security baseline |
| D09 — Separate opinion webpage? | Later, opt-in and no execution privileges | Prevent feature creep into a standalone service |
| D10 — External source incorporation? | Independent implementation of concepts | Upstream licensing and unstable APIs |
| D11 — Public release/licensing? | Leave unchanged until explicit discussion | New source and package obligations |
| D12 — Existing dashboard integration? | Reuse if compatible, don't fork a second surface | Avoid parallel maintenance and telemetry drift |

Decision records must distinguish `PROPOSED`, `OWNER_APPROVED`, `REJECTED` and `SUPERSEDED`, include exact Owner input/provenance, scope and time. A Markdown checkmark without original authorization is not a decision.

## Open technical questions to resolve with evidence

1. Does each supported Codex/Claude Code version expose an independent per-role model override, or do all roles necessarily inherit the same upstream? Capture actual delegated role metadata.
2. Which process/host metadata can prove an agent is still alive and permitted after a restart? What does the host guarantee about resumed sessions?
3. Can local SQLite be accessed from each intended host/workspace without introducing unwanted portability or backup concerns?
4. What trusted mechanism mediates approval and candidate promotion if a Worker is untrusted and the Manager is only a native parent model?
5. Which existing dashboard worktree is authoritative at phase start, and what does it already display? Never overwrite in-flight work.
6. Which native host features allow a real read-only Tester/Reviewer boundary rather than merely instruction-level discipline?
7. Are recorded provider token/usage scopes comparable across Codex native subscriptions and Claude Code configured gateways? If not, compare within each cohort only.
8. Can a compact handoff cite all mandatory evidence without copying sensitive full logs into a prompt or repository?
9. Which parts of this plan reproduce existing implementation? Avoid regenerating features that already exist and work.
10. What is the minimum benchmark that can disprove an apparent improvement without burning through the user's quota? The protocol must be predeclared, not improvised mid-run.

## Scope control

**Current authorization for this document set:** research and publication of these Markdown plan files only. No feature flag is enabled; no implementation, model run or experiment is started. All P1-P7 work waits for independent Owner approval. Future implementation should first check the current state, because the dated source snapshot can become obsolete.

A recommendation should always include the alternative `DO_NOT_BUILD` when the expected gain fails to justify operational cost.
