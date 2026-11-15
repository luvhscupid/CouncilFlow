# AI Agent Token & Context Efficiency — Council Research Record

> **Status:** CLOSED — research concluded; **not normative**, **not an approved implementation task**.  
> **Date:** 2026-11-15 (Asia/Pontianak)  
> **Participants:** Owner (Jace), GPT-6 (OpenAI), Claude Sonnet 5.5 (Anthropic), exchanging responses via the Owner.  
> **Repository:** `luvhscupid/CouncilFlow`  
> **Scope:** Agent token use, API/quota efficiency, reliable handoffs, context retrieval, memory, and evaluation economics.  
> **Authority:** This document records discussion and agreed research conclusions. It does **not** amend CouncilFlow's frozen architecture, Security Annex, Owner authority, acceptance criteria, or existing development priorities. Nothing here authorizes coding, experiments, approval-gate changes, or changes to the Supervisor.

## Quick recall

**Original question:** Can we reduce token usage beyond JSON/YAML communication, codebase-memory MCP, and prompt caching?

**Revised objective:** Maximize **verified, accepted engineering work per unit of total constrained resources**, not merely minimize raw token count. Consider API cost, subscription quotas, elapsed time, model calls, tests, retries, maintenance, and Owner attention.

**Core finding:** The most promising immediate savings come from **avoiding unnecessary LLM work**, preserving useful prompt caching, returning compact deterministic tool results with an expand path, and not retransmitting the same evidence. **Measure before implementing.** Smaller context can hurt correctness, trigger extra turns, and erase any apparent savings.

**Decision:** Research closed by agreement between GPT-6 and Claude Sonnet 5.5. No outstanding substantive disagreement. Preserve as optional future experiments only; do not interrupt approved CouncilFlow development.

## 1. Critical distinctions

| Lever | What it actually changes | Caution |
| --- | --- | --- |
| Token reduction | Fewer input/output tokens processed | More retrieval rounds or lower task quality may undo benefit |
| Cost reduction | Lower prices through caching/model choice | Cached input can be cheaper than a shortened, cache-busting prompt |
| Work reduction | Fewer agent turns, repeated operations and retries | Often more valuable than shaving formatting tokens |
| Reliability/security | Better evidence, authorization, and acceptance | Required safeguards do not need to justify themselves with token savings |

**Cost per accepted task (CPAT):** For comparable attempts, approximate `CPAT = cost_per_attempt / acceptance_probability`. In practice, include the full cost of failed attempts, retries, verification, and related usage. Track acceptance rates separately.

A 10% cheaper attempt improves the simplified CPAT calculation only if `P_new > 0.9 * P_baseline`. This is a **mathematical break-even condition**, **not** authorization to accept security regressions or materially lower reliability.

**Lifecycle net benefit:** `N * (C0 - C1) - E - M`, where `N` is **measured or defensibly forecast** accepted-task volume over the period, `C0/C1` are baseline/optimized CPAT, `E` is implementation/evaluation cost, and `M` is ongoing maintenance cost. Rank optional optimizations by expected incremental net benefit, subject to non-negotiable correctness, security, and Owner-authority constraints. There is **no universal 10% or 40% improvement threshold**.

For subscription-based coding agents, where dollar amounts may not be visible, measure useful tasks completed per quota window and time-to-completion separately. Do not equate vendor-reported tokens with billed costs without checking provider behavior.

## 2. Surviving candidates: test first, do not assume value

### A. Baseline instrumentation

Record per task:
- task identity/class, repository/spec revision, accepted/rejected outcome, number of attempts;
- uncached input, cache reads, cache writes, output/reasoning tokens **where provided**, total provider cost/quota impact;
- LLM turns, tool calls, tool-result size, test/execution time, wall time, retries;
- Owner intervention count and elapsed time, security/acceptance outcomes.

Do not confuse instrumentation with an optimization. First determine where costs actually occur and whether they are significant relative to total project work.

### B. Cache hygiene

Keep reusable instructions and definitions stable, and changing task data later where supported by the provider. Avoid gratuitous prefix rewrites and unnecessary compactions. Consider compaction or a checkpoint at a clean task boundary or after a cache-cold pause, subject to the harness's actual implementation.

Cache benefit depends on **model-specific read/write prices, TTL, minimum size, prefix mechanics, and third-party proxy support**. Earlier discussion considered illustrative write/read multipliers of `1.25x/0.05x`; **these are not universal constants**. Confirm actual usage telemetry before optimizing.

A warm large cached context can be cheaper than a short freshly assembled context. Owner approval waits can cause TTL expiry, but mandatory approval must never be skipped for cache efficiency.

### C. Deterministic tool-output digests + expandable handles

Prefer machine-produced summaries of test runs, searches, or logs: exit status, failing test IDs, relevant assertion diff, counts, and bounded excerpts; persist full outputs as artifacts and return a reference for expansion.

Example **illustrative**, not an implementation schema:

```yaml
task: T17
status: failed
tests: 42/43
failure: test_module::test_case
artifact: artifacts/T17/test-run.json
```

Do not use an LLM to summarize logs by default if deterministic parsing suffices. Preserve complete test evidence externally; digest truncation must not erase the ability to inspect it.

### D. Avoid redundant deterministic work

Use grep/LSP/symbol indexes, Git diffs, formatters, codemods, scripts, parsers, and ordinary test runners instead of LLM interpretation where the operation is deterministic. Memoize identical safe computations only when their input identity and environment are trustworthy. Prefer eliminating unnecessary turns to generating fewer narrative tokens inside the same number of turns.

### E. Compact handoffs and artifact references

Exchange task status, *actual changes*, evidence IDs, and unresolved questions rather than repeated transcripts or full logs. Any referenced artifact must remain accessible and revision-bound. JSON/YAML is valuable primarily for deterministic parsing and validation; there is **no demonstrated major token-saving advantage** to a custom compact dialect. Avoid over-compressed or unfamiliar encodings that impair model comprehension.

## 3. Required safeguards, independent of optimization economics

- **Owner authority**: Owner-approved scope, protected actions, and mandatory approvals remain in force; no implicit authorization.
- **Trusted Supervisor**: Enforce machine-checkable permissions, budgets, authorization, scope boundaries, isolation, and evidence integrity outside the LLM. The prompt explains policy but is **not** an enforcement boundary.
- **Verification**: Tester, Reviewer, Manager, and any other verification participants retain their distinct responsibilities as defined by the currently approved CouncilFlow role specification; this research note neither redefines nor merges those roles. Neither an agent's confidence nor model agreement substitutes for required verification.
- **Unknown is not none**: For high-risk, security-adjacent changes, unresolved dependency/impact information cannot be treated as proof of no impact. If required evidence remains unknown, block promotion or escalate appropriately.
- **Integrity is not sufficiency**: A harness-authenticated test result proves provenance and what ran, not that tests were complete or architectural intent was fulfilled.
- **Semantic claims remain advisory** unless independently substantiated by appropriate evidence. Machine-checkable authorization can be enforced; arbitrary architectural intent is not fully machine-decidable.
- **No automatic Owner rubber-stamping**: Routine uncertainties can be investigated autonomously under existing approval. Material ambiguity/new authority requires Owner decision. Exhausted escalation budget does not confer approval.

None of these safeguards may be removed just because they increase CPAT.

## 4. Evidence and verification research (not an approved subsystem)

A slim handoff *concept* used four fields: `claim`, `evidence_id`, `producer`, `revision`; evidence also has a `deterministic` versus `advisory` classification. Full authenticated records would retain spec revision, command/arguments, environment, harness identity/version, outputs, and hashes in an evidence store.

Anti-self-certification principles:
- Agent-authored claims are **not** self-certifying; deterministic evidence originates in trusted harness execution.
- Evidence must bind to the relevant code, spec, and execution environment; stale inputs invalidate applicability.
- Reject circular claim-as-proof chains; ultimately ground deterministic claims in authenticated artifacts.
- Semantic/advisory assessments do not become deterministic proof by repetition.

**Reusing evidence across revisions** is deferred. A whole-suite result often becomes stale at each commit; narrowly scoped per-test or file-hash evidence may be reusable, but real hit rates are unknown. The main potential value of evidence references is provenance and compact handoffs, not guaranteed cross-revision savings.

**Risk-bounded impact checks** are worth a separate correctness pilot, not assumed to save tokens. Identify changed interfaces and known dependencies/tests; distinguish covered, partial, and unknown impact; increase checking with risk. A complete reverse-dependency closure can explode for common utility functions, and observed/static dependencies can miss reflection, runtime configuration, or dynamic behavior. Running all *known* tests is not proof of full behavioral coverage.

Potential semantic techniques: differential testing against a previous version, executable contracts, meaningful metamorphic relations, targeted mutation testing of changed lines, and independent model assessment. Each proves only what its oracle/property covers. Same-agent tests, line coverage, or snapshots alone offer weak assurance. Cross-family review may reduce correlated misses but must be benchmarked, not assumed.

## 5. Deferred ideas and why

| Candidate | Why deferred |
| --- | --- |
| Full build-system memory dependency graph | Hashes show freshness of declared inputs, not semantic correctness or completeness; complexity unproven |
| Query-backed scoped memory, observed read-sets, reverse-dependency invalidation | Promising for repeated rediscovery; measure first, dynamic dependencies remain difficult |
| Adaptive online context controller / bandit | Additional complexity, low expected task volume, potentially unsafe exploration |
| Broad static policy table | Not proven necessary beyond risk-based checks and actual task requirements |
| Tool-call fusion and prefetch | Could reduce turns but embed hidden retrieval ranking and return oversized results |
| Tool-result masking / compaction engine | May help context size but may bust caches or suppress needed evidence |
| Dynamic model routing/cascades | Could save cost; cheap model + thin context may harm success; escalate based on reliable signals |
| Aggressive lazy retrieval / context manifests | Missed dependencies and unrecognized omissions; log actual context and allow expansion |
| Lazy MCP schema discovery | Existing platforms may already defer tools; interaction with cache and callable schemas must be tested |
| Reusable proof-carrying evidence across commits | Invalidation and maintenance cost may outweigh reuse |
| Custom compressed JSON/YAML dialect | Low likely return and possible semantic ambiguity |

A **build-system approach to memory** remains an interesting long-term idea: persist claims with originating queries, source hashes/revisions, observed read-sets and provenance, then invalidate affected results. It was **not** selected for implementation.

## 6. Minimal evaluation sequence

1. **Instrument existing baseline** on real or replayed tasks. Measure accepted-task volume `N` and cost/turn/cache distribution, without altering behavior.
2. **Inspect existing caching** in the actual provider/harness, including whether it is already automatic and whether added mechanisms would duplicate it.
3. **Experiment A, if justified:** compare deterministic digests/expand handles plus cache hygiene against unchanged baseline, with paired tasks and repeated runs.
4. **Risk-bounded impact-check pilot** against seeded defects as a correctness evaluation; do not confuse this with a pure cost optimization.
5. **Experiment B, only if needed:** add evidence handles if A reveals enough repeated reading or verification to justify them.
6. **Measure reviewer miss correlation** when a credible seeded-defect benchmark exists; Claude preferred doing this earlier. This preference was not contested, but was not formally agreed by GPT-6.

Include an **oracle-minimal vs retrieved vs full-context** comparison if exploring aggressive retrieval. It tests the potential of retrieval minimization, not the value of every other optimization.

Evaluation metrics: CPAT, accepted-task rate, retries, token/caching breakdown, wall time, Owner interventions, security or authorization breaches, retrieval miss/expansion rates, independent defect-detection false negatives/positives, and maintenance cost. Paired experiments, multiple runs, and uncertainty intervals are preferable to single-run anecdotes. An initial proposal discussed ~30–50 tasks with at least three seeds each, **not an approved sample size or proof of adequate power**.

Benchmark sources should mix historical real defects, filtered mutation-generated defects, independently authored specification violations, and **valid** implementations. Split by repo/defect family to reduce leakage, maintain genuine holdouts, and avoid tuning repeatedly on the holdout. Public bugs can already be in a model's training data. Track missed violations and correlated reviewer misses rather than assuming model diversity solves them.

## 7. Stop governance (agreed in final rounds)

**Strategic authority:** Owner defines and approves research scope, maximum budget, success/quality criteria, and stop conditions **before the first run**.

**Execution:** Within that authorization, the Manager enforces stops mechanically without requesting permission to stop a wasteful experiment. Manager may not weaken or redefine criteria after observing results.

**Immutable protocol:** Record the experimental protocol as an artifact and bind it by hash to experiment runs, including the *minimum worthwhile effect*, sample size or maximum budget, non-inferiority expectations, and pre-declared interpretation of flat results.

**Terminal outcomes:**
- `CLOSED_NO_BENEFIT`: criteria show insufficient worthwhile improvement, negative expected net benefit, or a predeclared stop condition; retain evidence.
- `INCONCLUSIVE`: insufficient evidence under the predeclared decision rule; still stop once the approved budget is exhausted.
- Any constraint violation or budget-exceeding condition triggers the corresponding authorized stop/block.
- Reopening a terminal or exhausted-budget initiative requires **new Owner authorization**, not automatic deferral.

Do not turn a failed experiment into a perpetually deferred task. A confidence interval that excludes the predeclared minimum worthwhile improvement can support `CLOSED_NO_BENEFIT` **when the specified statistical decision rule is met**. Lack of statistical power alone is not proof of no benefit.

The net-benefit rule remains `N * (C0 - C1) - E - M`. The decision to **do nothing** is valid.

## 8. CouncilFlow application and authority boundary

- This is a **research reference**, not a change request.
- Do **not** amend or replace existing frozen Architecture Specification v1.0, Security Annex v1.0-A, approved vNext plans, acceptance criteria, or Owner authorization.
- Do **not** launch implementation, expand scope, create recurring optimization work, or delay the existing development program on the strength of this note.
- When the Owner later explicitly requests optimization work, first inspect the then-current harness, implementation, pricing/quota telemetry, and normative plans. Treat all proposals above as hypotheses until tested.
- New experimental budgets, frozen stop conditions, and permissions would need explicit Owner approval at that time.

## 9. One-paragraph future recall

The GPT-6 × Claude Sonnet 5.5 research concluded that token compression alone is the wrong optimization target. Prefer cost and quality per **accepted engineering task**, including retries, time, quotas, Owner attention and maintenance. Start by profiling the existing coding-agent workflow and its cache behavior. Optional early experiments are deterministic tool-output digests with expandable artifacts and elimination of redundant deterministic LLM work. Keep trusted Supervisor enforcement, Owner authority, required verification and explicit high-risk uncertainty regardless of cost. Defer sophisticated memory graphs, masking, fusion, routing, and adaptive context engines until measurements justify them. Every future experiment requires an Owner-approved, hash-bound protocol with budgets, minimum worthwhile effect and executable stop conditions. This discussion granted **no implementation authorization**.

---

*This document is a synthesized record of the exchanged discussion, not a verbatim transcript, independent repository audit, measured performance result, or signed approval artifact. Model-specific price examples must be reverified before use.*
