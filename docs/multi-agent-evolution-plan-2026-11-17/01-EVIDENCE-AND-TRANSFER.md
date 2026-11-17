# 01 — Upstream evidence, transfer value, and limits

**Research date:** 2026-11-17. Source-code and repository evidence was inspected; this is not a claim that the author executed every suite or independently reproduced published benchmark scores.

## Pinned source snapshots

- CouncilFlow: [`6c4e477`](https://github.com/luvhscupid/CouncilFlow/tree/6c4e4770876c8c86092c3cfca6ef83444adfae6e)
- Forge: [`d0b9cec`](https://github.com/nxtg-ai/forge-orchestrator/tree/d0b9cec0da6a1288433ed06b7e3575cad41ab617)
- Agyn current documentation/platform: [`6a778d3`](https://github.com/agynio/platform/tree/6a778d39828aaf096dbe2b7f2ea676a48957404b)
- Agyn original multi-agent v1 (archived): [`012b14b`](https://github.com/agynio/v1/tree/012b14b93b1adf845b6109717bd123b8e52e49cd)
- Agyn current orchestrator: [`1225cef`](https://github.com/agynio/agents-orchestrator/tree/1225cefd5d2ec3ce1ef1754b9a0f72609d26633a)
- MetaGPT: [`11cdf46`](https://github.com/FoundationAgents/MetaGPT/tree/11cdf466d042aece04fc6cfd13b28e1a70341b1f)

Pinned source links are the evidence anchors. Upstream may have evolved since these snapshots.

## Forge: coordination and operational reality

**Evidence in source.** Forge has typed task phases (`Build -> Verify -> Fix -> UAT -> Ship`), task dependencies, assignment/claim state, file references, state and event persistence, adapters, a quality-gate detector and an MCP surface. Relevant files: [task lifecycle](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/src/core/task.rs), [state](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/src/core/state.rs), [quality gates](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/src/core/quality_gate.rs), [run path](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/src/cli/run.rs), [doctor](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/src/cli/doctor.rs).

**Maturity caveat.** Forge explicitly declares `maturity: alpha` and describes non-atomic, advisory file locks: simultaneous claims can race, autonomous `forge run` can skip lock checks and lock recovery is incomplete. Don't copy these mechanisms as security enforcement. See [upstream README](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/README.md) and [STAGE](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/STAGE). Its CI supports Linux/macOS tests and a Windows compile check; that is not equivalent to full Windows runtime verification.

**Transfer:** task graph, human-readable blocker, doctor/status semantics, event provenance, knowledge taxonomy and release-debt checks. **Do not transfer:** soft locks as an isolation guarantee, aggressive auto-commit, arbitrary headless autonomy or its Rust daemon-like surface when native skill integration suffices.

**License:** FSL-1.1-ALv2, source available with competing-use restrictions, with delayed Apache-2.0 conversion. Don't copy source into CouncilFlow without independent license review: [LICENSE.md](https://github.com/nxtg-ai/forge-orchestrator/blob/d0b9cec0da6a1288433ed06b7e3575cad41ab617/LICENSE.md).

## Agyn: separate generations, separate claims

**Archived v1:** graph-based multi-agent coding team with separate roles, structured messages, workspaces and agent context; [technical overview](https://github.com/agynio/v1/blob/012b14b93b1adf845b6109717bd123b8e52e49cd/docs/technical-overview.md), [atomic graph update](https://github.com/agynio/v1/blob/012b14b93b1adf845b6109717bd123b8e52e49cd/docs/graph/fs-store.md), [rolling summary](https://github.com/agynio/v1/blob/012b14b93b1adf845b6109717bd123b8e52e49cd/docs/summarization.md). Its graph update stages a new tree and uses optimistic version checking; far stronger conflict detection than simply rewriting a shared JSON file.

**Benchmark:** Agyn v1's README reports **72.2% SWE-bench Verified** issue resolution with a GPT-5-based agent team. See its [README](https://github.com/agynio/v1/blob/012b14b93b1adf845b6109717bd123b8e52e49cd/README.md) and [published paper](https://arxiv.org/abs/2602.01465). This is a public report, **not independently reproduced here**; different model/tools/budgets across comparators prevent isolating "more agents" as the causal factor. The paper abstract and results section use slightly different percentages; retain that discrepancy rather than silently selecting the higher number.

**Current platform:** Kubernetes-native agent runtime, not simply the old coding-team app. Control plane (definitions/reconciler/runners) separated from data plane (threads, LLM proxy, secrets, tracing, authorization) and sandboxed workloads. Evidence: [architecture](https://github.com/agynio/platform/blob/6a778d39828aaf096dbe2b7f2ea676a48957404b/docs/introduction/architecture.md), [security](https://github.com/agynio/platform/blob/6a778d39828aaf096dbe2b7f2ea676a48957404b/docs/operate/security.md), [LLM registry](https://github.com/agynio/platform/blob/6a778d39828aaf096dbe2b7f2ea676a48957404b/docs/administer/models.md), [usage](https://github.com/agynio/platform/blob/6a778d39828aaf096dbe2b7f2ea676a48957404b/docs/use/usage.md), [reconciler source](https://github.com/agynio/agents-orchestrator/tree/1225cefd5d2ec3ce1ef1754b9a0f72609d26633a/internal/reconciler). Agyn notes that production network policy requires explicit configuration and isn't enabled by its local bootstrap. A documented boundary is not evidence that every deployment enforces it.

**Transfer:** logical model labels decoupled from endpoints, observed token/cache usage, separate private operational logs and protected trace content, consistent run identities, desired/actual reconciliation, bounded summaries, optimistic concurrency, terminal-state handling. **Do not transfer:** compulsory Kubernetes, OpenFGA, OIDC, per-agent microservices, SaaS billing or a shared provider gateway.

**Licensing:** current platform AGPL-3.0; archived v1 has a custom Apache-with-commons-clause/no-hosting license. Treat both as license-review-required before incorporating source.

## MetaGPT: typed SOPs and learning from comparisons

**Evidence in source.** `Role` has separate observation, reasoning and action, subscribed message tags and private queues; `Team` uses a shared environment and budget guard. `ActionNode` builds structured action output with schemas, human/automatic review and retries. `ExperienceManager` handles retrieval and read/write controls. `AFlow` tests candidate workflow graphs against benchmarks and iteratively optimizes candidates.

- [Team / budget](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/team.py)
- [Role / message buffers](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/roles/role.py)
- [ActionNode / typed output](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/actions/action_node.py)
- [Experience pool](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/exp_pool/manager.py)
- [AFlow documentation](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/examples/aflow/README.md)
- [AFlow optimizer](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/metagpt/ext/aflow/scripts/optimizer.py)

**Maturity caveat.** Large established codebase and ecosystem, but stars are popularity, not benchmark proof. Public release `v0.8.2` dates to March 2025; source updates and tests have their own status. Some MetaGPT review actions rewrite code, which conflicts with CouncilFlow's independent non-mutating Reviewer.

**Transfer:** typed outputs, bounded SOPs, experience taxonomy (SUCCESS/FAILURE/INSIGHT), benchmark-driven comparison, graph candidate search as a *future option*. **Do not transfer:** autonomous rewrites by reviewers, role conversations as authentication, open-ended workflow search without resource bounds.

**License:** MIT at upstream snapshot; retain attribution requirements if any source is actually copied, though the plan proposes conceptual reuse.

## CouncilFlow baseline and gap calibration

Verified by reading [current README](../../README.md), [host packages](../technical/host-packages.md), [efficiency helpers](../technical/efficiency-helpers.md), [recovery rules](../../.agents/skills/council-flow/references/recovery.md) and [role policy](../../.agents/skills/council-flow/policies/roles.yaml). Existing structures already solve a subset of the problem:

- **Already present:** stable acceptance IDs; exact source-fidelity and candidate SHA-256 checks; structured JSON envelopes; Worker, Tester, Reviewer separation; Reporter/Manager evidence; retry/rework instructions; Codebase Memory optional integration; digest/expand; offline token/usage capture.
- **Partially supported, not established end-to-end:** native host invocation across versions, independent model assignment, reliable observed effective provider identity, actual subscription/quota attribution, measurable token/value effect.
- **Absent as guaranteed runtime service:** authenticated agent identity, durable CAS ledger with replay/reconciliation, atomic multi-workspace promotion, independently enforced isolation, complete event-driven scheduler, self-running optimizer.
- **Not a product gap requiring repair:** absence of Kubernetes, standalone app, commercial gateway or universal model router.

## Evidence-quality labels for downstream work

Use `SOURCE_INSPECTED` for seen source, `DOC_CLAIM` for project assertions, `TEST_REPORTED` for upstream CI or test claims, `NATIVE_OBSERVED` for actual CouncilFlow host evidence, `UNVERIFIED` for missing independent checks. Keep all five distinct. Prefer executable negative controls over a pass count alone.

When benchmarking future work, compare against the *same CouncilFlow baseline* under comparable budgets. Don't infer architectural superiority from GitHub stars, demo volume or an unrelated benchmark.
