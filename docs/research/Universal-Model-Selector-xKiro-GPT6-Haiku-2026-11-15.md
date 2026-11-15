# Universal Model Selector v1 — GPT-6 × Claude Haiku Council Research

> **Status:** CLOSED — planning-level consensus; **NON-NORMATIVE; NO IMPLEMENTATION AUTHORIZED**.
>
> **Date:** 2026-11-15 (Asia/Pontianak)  
> **Participants:** Owner (Jace), GPT-6 (OpenAI), Claude Haiku 5.5 (Anthropic, Medium); exchanged via the Owner.  
> **Target project:** CouncilFlow (`luvhscupid/CouncilFlow`).  
> **Purpose:** Preserve the proposed universal model-selector design so it can be recalled without reconstructing the discussion.  
> **Live xKiro/account verification as of 2026-11-15:** NOT YET PERFORMED.
>
> **Authority boundary:** This is a synthesis of a design discussion, **not** a new frozen requirement, implementation authorization, repository audit, model certification, account entitlement verification, or amendment to CouncilFlow's Architecture Specification, Security Annex, approved development plan, role definitions, or Owner-control rules. Those authoritative sources prevail where there is disagreement.

## Quick recall

Design a **universal selector** for OpenAI and Anthropic models, potentially through **xKiro** as one optional gateway, with future support for additional Owner-approved models and routes. The Council used **Luna, Haiku, Sol, Sonnet, Astra, and Opus** as illustrative model choices, **not** as an approved or validated model list. **Terra and Fable appeared in GPT-6's earlier pre-Council UI sketch, not as models evaluated or agreed by the Council.** Do not assume any exact IDs, versions, prices, entitlements, or harness compatibility without current verification.

**Agreed v1:** An Owner-approved, hashed policy and per-role pools; an exact-model-and-route registry with verification status; independent compatibility evidence; Manager selects within an eligible set; trusted Supervisor authorizes each dispatch; clear distinction among enforced, estimated, and reported spending. Maintain existing CouncilFlow responsibility boundaries, without a parallel agent or adaptive selection service.

**Status:** Architectural discussion closed with no identified blocking *design defect*. **Implementation remains unauthorized.** Several external and repository facts must be checked before implementation.

## 1. Why this is not simply a dropdown

A model can be:
1. **Discoverable:** An API/catalog advertises an ID.
2. **Authorized:** Owner policy permits a particular model, route, harness, scope, reasoning-effort configuration, and spending exposure.
3. **Compatible:** Independent evidence demonstrates that this combination can execute required tooling through the actual harness.
4. **Qualified:** The combination passed an approved representative evaluation for specified task classes and conditions.

These are different states. A live model catalog **validates claims about availability; it cannot grant eligibility**.

**Model capability ≠ harness capability:** A model that supports tool calling through one API may fail in Claude Code or Codex due to protocol, tool schema, or context differences. Do not infer execution support from generic OpenAI/Anthropic-compatible endpoints.

## 2. xKiro integration: research assumptions, not verified production behavior

Documentation reviewed during the discussion: <https://docs.xkiro.com/>.

The discussion cited these xKiro-documented surfaces, which must be checked against live documentation and the account before use:

- Model discovery: `GET https://api.xkiro.com/v1/models`.
- Account usage and allowances: an authenticated `/v1/usage` endpoint.
- Vendor-prefixed model identifiers, model metadata, reasoning capabilities, pricing, and access-tier restrictions.
- Anthropic-compatible Messages routing for Claude Code and OpenAI Responses routing for Codex CLI, with differing endpoint/base-url conventions.
- Distinct subscription allowance, wallet, and pay-as-you-go arrangements.
- Gateway **upstream failover** for a requested model, separate from a **Manager-authorized cross-model selection**.

**No live xKiro catalog, account entitlements, usage, tier limits, model mappings, or billing guarantees were verified in this Council.** Provider API compatibility alone is not proof that the coding harness works reliably. Provider descriptions and model/pricing examples can change.

Reference starting points:
- <https://docs.xkiro.com/models/>
- <https://docs.xkiro.com/api/list-models/>
- <https://docs.xkiro.com/api/usage/>
- <https://docs.xkiro.com/models/tiers/>
- <https://docs.xkiro.com/guides/tools/claude-code/>
- <https://docs.xkiro.com/guides/tools/codex/>

xKiro is **optional**, not exclusive. Native OpenAI and Anthropic routes may remain separate, explicitly configured options. A different route can change data destination, tooling, subscription treatment, and billing; no silent unapproved provider fallback.

## 3. Agreed v1 design

### A. One Owner-approved policy file

Versioned, content-hashed, and loaded through a trusted approval path, with:

- Per-role **model pools** and exact allowed model/route/harness identities.
- Model-specific cost/usage ceilings as well as task/pool/period budgets where supported.
- Permitted cross-provider/cross-pool routes and fallback choices.
- Approved reasoning-effort options, task class/scope, and authorization restrictions.
- Qualification validity windows, certification requirements, and permitted low-risk experimental use.
- Separate opt-in for pay-as-you-go and consequential billing exposure.

A content hash alone is **not** authorization; approval and active-policy storage must be protected. The Manager may propose changes but cannot activate an altered policy, expand a pool, or modify its own limits.

### B. Flat versioned registry, without a new service

Keep four related record types, initially as files/data integrated with existing mechanisms rather than a dedicated database:

1. **ModelIdentity:** provider, configured route/endpoint, exact model ID, harness, relevant configuration identity/hash (including supported reasoning effort).
2. **Status:** `UNVERIFIED`, `COMPATIBLE`, or `QUALIFIED`, with task-class scope, suite version and validity/revalidation requirements.
3. **Evidence:** independent runner identity, test-run reference, results per required capability, sample counts, timestamp and relevant execution metadata.
4. **Pricing and limits:** route-specific cost basis, plan/wallet distinction, reservations and indication whether each limit is *enforced*, *estimated*, or *reported*.

Role pools reference these exact identities. Don't add a complex graph, online model-ranking agent, or speculative runtime discovery subsystem.

### C. Independent certification, not Manager self-approval

A **trusted, versioned compatibility test procedure** evaluates the exact provider + endpoint + model ID + harness + relevant configuration, including requested reasoning effort when it affects behavior.

Qualification states:
- **UNVERIFIED:** A catalog entry or untested configuration; **not eligible for automatic dispatch**.
- **COMPATIBLE:** Authenticated call, required tool interactions, structured responses, and basic isolated workflow pass; only suitable for explicitly Owner-authorized experimental scope where required.
- **QUALIFIED:** Compatible and passes the approved representative task-class checks, with recorded evidence and sample limitations. Qualified **only for the capabilities and classes actually evaluated**.

Do not invent a universal qualification pass rate. The Owner approves representative suite scope, thresholds, and the revalidation budget. Sparse data is explicitly marked uncertain; passing a smoke test is not a global reliability guarantee.

Owner-authorized **low-risk experiments** with COMPATIBLE pairs may run under appropriate isolation, restrictions and budget. Experiment results are **valid evidence**, but do not auto-upgrade a pair to QUALIFIED.

Known model/harness/endpoint/config changes require reassessment; also consider silent provider drift. Expiry, live failure signals, and targeted revalidation should be handled without committing to costly continuous probing. An expired QUALIFIED record is **not currently qualified**. Low-risk experimental exceptions require distinct prior authorization; a warning alone does not restore qualification.

### D. Existing Manager judgment, independent Supervisor enforcement

At dispatch:

1. Read the active, Owner-approved policy and retrieve the eligible per-role model pool.
2. Filter by exact route/model/harness compatibility, status, task scope and required capabilities.
3. Filter by supported reasoning effort and remaining authorized resources, while distinguishing reservations from actual hard spend limits.
4. **Manager chooses** among remaining permitted options, with brief rationale and Supervisor-recorded outcome history when available.
5. **Trusted Supervisor** checks the active policy hash, authorization, eligibility, validity, resource constraints and execution route before dispatch.

The Manager can judge **suitability**; it cannot grant **eligibility or authority**. Do not spin up a separate LLM solely to route models. Historical performance should inform, not become a fictitiously confident ranking.

Role names and duties continue to follow the **current authoritative CouncilFlow specification**. This research document does not redefine Tester, Reviewer, Manager, Planner, or Worker.

### E. One shared execution contract, harness-specific edges

Where useful, define common task inputs, outputs, tool results, evidence references and failure categories. Preserve actual Claude Code and Codex differences behind the smallest adapter needed for the **first real harness**. Do not assume a universal adapter can hide harness-specific failures.

Before adding any wrapper, inventory existing CouncilFlow, Claude Code, Codex, and xKiro hooks for selection, permissions, identities, and usage.

### F. Reasoning effort is a distinct configuration

The Manager can choose among **Owner-approved, tested effort settings for that exact model/harness/route**. Unsupported or unverified values should be rejected rather than silently substituted. Do not presume that Claude thinking settings and OpenAI effort levels are identical.

## 4. Switching, retrying, and availability

- Prefer selecting a model **at the task boundary**.
- If a model change is necessary during a Worker attempt, checkpoint the frozen goal, acceptance IDs, scope, source/diff state, tests, authenticated evidence, unresolved issues, and remaining budgets. Begin a new execution session through the approved harness rather than transplanting raw cross-family conversation history.
- Previously produced work is not automatically invalid merely because the model changed. Its evidence must be rechecked for applicability to the new state, spec and environment.
- Gateway retries to an upstream serving the *same requested model* and Manager choices between different models/providers are separate events.
- When a model becomes unavailable, fail closed unless another **already authorized, eligible** model/route is permitted. Preapproved cross-provider choices do **not** require repeat interactive Owner approval.
- Do **not** automatically escalate to a flagship solely because a cheap model failed twice. Signals include missing capabilities, rate limits, incompatible context, verifiable failures, repeated non-progress and architectural ambiguity. Selection is Manager judgment **inside** approved resources.
- No universal fixed retry count was accepted. Approved resource budgets, progress checks, security policy and authorization remain authoritative.
- Track actual model/route/harness/effort selection and returned model identity where exposed; flag any discrepancy instead of inventing certainty about a gateway's hidden upstream.

## 5. Budget truthfulness

Usage endpoint snapshots can lag, concurrent Workers can race, and future output length is unknown. A pre-dispatch budget reservation is an accounting control **only to the extent the route or local execution can enforce it**.

Label limits distinctly:
- **Enforced:** A control known to block or cap an operation at the applicable boundary.
- **Estimated:** A prediction/reservation for uncertain consumption.
- **Reported:** Provider/gateway usage or allowance telemetry, potentially stale.

Do not promise a hard monetary ceiling on the basis of estimated tokens or an advisory `/v1/usage` balance. Treat unapproved pay-as-you-go as disabled, and do not convert subscription exhaustion into wallet spending silently.

## 6. Owner-only vs Manager-autonomous decisions

**Owner-only:** Allowed providers, endpoints, specific routes, pool membership, model permissions, budget ceilings, opt-in pay-as-you-go, protected capabilities/actions, approval of certification suites and thresholds, qualification validity windows, and the active policy.

**Manager within approved bounds:** Select eligible model and supported effort, explain choice concisely, retry/replan within existing security/progress/resource limits, checkpoint model switches, and record outcomes. Supervisor enforces authorization on each dispatch.

The Owner can preapprove a **set** of routes or fallback policies, avoiding repeated permissions for ordinary in-scope selection. A new provider/route or a larger spending exposure requires new approval.

## 7. Dependencies before any future implementation

1. **xKiro surface:** Verify current catalog, account-specific model IDs/tier entitlements, usage behavior, actual gateway routing and billing conditions. Do not expose account secrets in documentation.
2. **Existing hooks inventory:** Inspect current CouncilFlow repo plus actual Claude Code/Codex harness capabilities and permissions. Reuse native hooks; do not build duplicated adapters or enforcement.
3. **Owner revalidation budget:** Determine whether/when to spend on qualification refreshes; avoid automatic recurring expensive probes without permission.
4. **Representative test-class gate:** Owner chooses what evidence suffices to label a pair QUALIFIED, with sparse-sample limitations visible.
5. **Current approved normative constraints:** Recheck architectural and security specifications before any implementation proposal to ensure proposed additions neither weaken nor silently expand authority.

These are **pre-implementation dependencies**, not grounds to start repository changes now.

## 8. Deferred and rejected approaches

**Deferred:** Automated drift probes, adaptive routing/scoring, online bandits, broad benchmarking platform, graph-heavy pools, extensive harness adapters, dynamic discovery that grants eligibility, complex cross-revision evidence reuse, and automatic cross-provider failover not covered by Owner policy.

**Rejected as v1 default:** Selecting any newly discovered model automatically; Manager-only certification; treating proxy compatibility as harness certification; silent effort downgrade; silently consuming pay-as-you-go; changing frozen plan or permissions when switching models; universal fixed retry counts.

## 9. Closure and future recall

GPT-6 and Claude Haiku 5.5 agreed at planning level on: **Owner-approved hashed policy + static exact-route registry + independently produced compatibility evidence + Manager choice within an eligible set + Supervisor authorization per dispatch**, starting with existing tooling rather than creating an elaborate new framework.

There are **no unresolved blocking defects in this paper design**, but xKiro live/API/account behavior, harness/CouncilFlow hooks, testing criteria and revalidation budget remain unresolved before implementation.

**No code, implementation, installation, test expenditure, authorization change, frozen-plan update, or ongoing task was approved by this exchange.** Treat this record as a non-normative reference for a future Owner-directed decision.


## 10. Post-review routing addendum (closed, planning only)

After the initial Council closure, the Owner relayed independent critiques from **DeepSeek and Grok**. Both recognized the security/authorization framework but highlighted a gap: the note explains **which models may run** more completely than **how the Manager should choose among them**. DeepSeek characterized it as permissioning rather than an operationally validated selector; Grok highlighted certification overhead, the growing model × route × harness × reasoning-effort matrix, and weakly specified model suitability. These are critiques, not empirical proof.

GPT-6 and Claude Haiku 5.5 held a focused follow-up and **closed it as a research candidate**, with no remaining blocking paper-design flaw. The outcome **does not authorize implementation**.

### Agreed minimal model-selection procedure

1. Start with the active Owner-approved **role/task-class pool**. Re-check eligibility at **each dispatch**, not only when a session begins.
2. Exclude identities without current **QUALIFIED** evidence for that task class, or with expired qualification; **COMPATIBLE** pairs remain eligible only for explicitly Owner-authorized low-risk experiments.
3. Exclude model/route/harness/effort combinations lacking required tested capabilities, approved reasoning-effort settings, or adequate authorized resource scope. Keep *enforced*, *estimated*, and *reported* spending distinct.
4. Prefer the eligible **Owner-defined fixed default per task class**. With sufficient predeclared evidence, Supervisor-recorded cost per accepted task may inform a tiebreak. If the sample is insufficient, **do not invent a ranking**.
5. Permit the Manager to **override** the default within the authorized eligible set for a recorded task-specific reason. Record both rationale and observed outcome so overrides can be evaluated; Manager discretion does not permit policy changes.
6. The trusted Supervisor validates active policy hash, eligible model, exact provider route, status, validity, scope, budget and effort before dispatch. Block or use an **already authorized** eligible fallback if the default has become ineligible.

**No universal fixed retry count**, automatic cheap-to-flagship escalation, unauthorised provider change, or silent pay-as-you-go fallback was accepted.

### Minimal certification

- **Compatibility gate:** Authenticate and exercise tool calls, structured outputs, and one isolated edit-and-verify workflow for each *exact tested* model + provider route + harness + relevant configuration/effort.
- **Representative task-class gate:** Use a small fixed, Owner-approved set of real tasks and independent acceptance checks for **only** the classes/settings intended for use.
- **Truthful evidence:** Record exact combinations tested, suite version, result, run identity, sample counts and expiry. Untested combinations stay untested. The same display model accessed through xKiro and a native route requires **separate evidence**.
- Experiments can generate valid evidence but **cannot self-promote** models to QUALIFIED. Avoid claiming that sparse data establishes general reliability.

### Baselines and accountable overrides

The follow-up corrected an earlier counting error: compare **three strategies**, not four.

1. Owner-pinned single model.
2. Fixed model per task class.
3. Manager-selected within an approved eligible pool (initially default + logged override).

Predefine per-task-class and per-strategy **minimum sample sizes**, minimum worthwhile effect, evaluation budget and decision rule **with Owner approval before the experiment**. None were set in this discussion. Measure cost per accepted task, acceptance rate (including repeated attempts), latency, and Owner interventions; compare the adaptive strategy against fixed-per-class using sufficient repeats and uncertainty estimates.

Override records must include model/route/effort, rationale, outcomes and relevant verification evidence. Overrides **must be reviewed** for realized benefit, not allowed to accumulate as unexplained discretion. If the more complex approach cannot show a worthwhile improvement over fixed-per-class without reducing quality or increasing Owner burden, do not adopt it.

### Closure and remaining dependencies

**Status: CLOSED, NON-NORMATIVE; IMPLEMENTATION NOT AUTHORIZED.** Selection logic and qualification remain hypotheses until evaluated. Before any development: verify live xKiro catalog, usage and account entitlements; inventory CouncilFlow/Claude Code/Codex support; determine approved qualification thresholds, representative tasks and revalidation budget; preserve all frozen Owner and Supervisor constraints.


---

*This is a synthesized record of the Owner-relayed model exchange, not a verbatim transcript, verified implementation, live xKiro integration test, or signed policy authorization. Reconfirm external facts when revisiting.*
