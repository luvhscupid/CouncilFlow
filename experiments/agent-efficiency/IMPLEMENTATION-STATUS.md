# Agent Efficiency Toolkit — Implementation Status and Agent Handoff

> **Read this first before continuing this toolkit.**  
> **Last recorded:** 2026-11-15  
> **Repository:** [luvhscupid/CouncilFlow](https://github.com/luvhscupid/CouncilFlow)  
> **Development branch:** `codex/package-a-phase-1` (not merged into `main`)  
> **Last inspected implementation commit:** `4ceb8b154bad3cf14978193a395c21dadccccd0c`  
> **Implementation state:** Offline prototype for Phases 1–5 present; **live integrations and savings unverified**.  
> **Authority:** Documentation of implementation, **not** authorization to run live trials, change CouncilFlow roles or integrate into the live skill.

## 1. Fast orientation for a fresh AI agent

**Purpose:** Measure coding-agent usage accurately and preserve/condense tool output deterministically, with separate Codex and Claude Code-through-xKiro ingestion paths. This is **not** an automatic model router, provider proxy, Claude Code replacement, completed CouncilFlow integration, or proven token optimizer.

**Start here (in order):**
1. This file, then [README.md](README.md) for CLI usage.
2. [Phased plan](../../docs/research/Agent-Efficiency-Implementation-Phases-DRAFT-2026-11-15.md) and [closed research](../../docs/research/AI-Agent-Token-and-Context-Efficiency-2026-11-15.md).
3. `recorder.py`, `digest.py`, `codex_adapter.py`, `claude_adapter.py`, `evaluate.py`, and their tests.
4. If work might affect CouncilFlow agent roles or the frozen experiment, first consult `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md` and `02-GATE3-v0.2-FROZEN.md`. The newer Owner Charter supersedes older UX-Reviewer descriptions. Do **not** change existing skills/config/Gate 3 as a side effect of efficiency work.

**Established by repository inspection:** the listed modules, tests, fixtures and documentation exist on the feature branch; code and test source were read. **Not independently established by this documentation pass:** execution of the test suite, actual host event compatibility, accurate upstream metering, statistically meaningful savings or end-to-end runtime behavior. Codex's stage completion reports are cited below as **agent-reported**, not independent certification.

## 2. Development history and delivered code

| Phase | Commit | Implemented source | Reported verification |
| --- | --- | --- | --- |
| 1 — usage recorder | `785e4c5` | `recorder.py`, `record.schema.json`, `fixtures/sanitized-runs.jsonl`, `test_recorder.py` | Codex reported 4 tests passing |
| 2 — command digest | `f1d8bb9` | `digest.py`, `test_digest.py`; README expanded | Codex reported 9 total tests; CLI capture/expand smoke test |
| 3 — Codex parser | `48bac65591807c00e1cce21156d93503f4b73a5c` | `codex_adapter.py`, Codex fixture and tests | Codex reported 13 total tests; synthetic adapter smoke test |
| 4 — Claude/xKiro parser | `022e2cc12c2cae972522a807642d2464c9b13a7a` | `claude_adapter.py`, Claude fixture and tests; nullable `gateway` record field | Codex reported 17 total tests; synthetic adapter smoke test |
| 5 — offline evaluator | `4ceb8b154bad3cf14978193a395c21dadccccd0c` | `evaluate.py`, paired fixture and tests; protocol draft CLI | Codex reported **20 total tests** and synthetic evaluator/protocol CLI smoke tests |

**Net repository footprint at the inspected commit:** 16 new/modified files under `experiments/agent-efficiency/` relative to `main`; no CouncilFlow skill, agent TOML, frozen spec or Gate 3 files changed by these five commits. The feature branch was five commits ahead of `main` at inspection. No pull request or merge was performed by this documentation pass.

### Modules and exact responsibilities

- **`recorder.py`**: constructs run records, validates a subset of the record contract, appends JSONL, and includes limited per-event parsers. Fields include harness, gateway (nullable), route, upstream model, usage scope, token counters, cost (nullable), elapsed time, attempt and acceptance provenance. Unknown values remain `null`. The Python validator is **not a complete JSON Schema validator** and does not authenticate evidence references.
- **`record.schema.json`**: documented schema for standalone run records, not the paired evaluator's full input format. Do not infer the framework has validated all schemas end to end.
- **`digest.py`**: opt-in command capture with stdout/stderr artifact bytes, SHA-256, bounded excerpt, heuristic important lines, flags, and explicit hash-checked `expand`. A timeout maps to a CLI exit code of 124. Full artifact capture is **not sandboxing** or proof that no relevant diagnostic was omitted from the abbreviated view. Some outputs may contain secrets.
- **`codex_adapter.py`**: parses supplied Codex `exec --json` JSONL (file/stdin), using recognized events and last completed-turn aggregate token counts; creates a record and a byte-preserving input artifact. **Does not invoke Codex**. Doesn't infer cost, acceptance, total session billing, or success merely from an event.
- **`claude_adapter.py`**: parses supplied Claude Code `stream-json` JSONL (file/stdin); takes an explicit gateway label such as `xkiro`, preserves separately supplied/observed model and route info, and uses the last recognized usage snapshot. **Does not invoke Claude Code/xKiro**. Label is caller supplied, not verified gateway provenance. Does not infer xKiro pricing or cache treatment; unsupported formats and ambiguous models must be handled as unknown.
- **`evaluate.py`**: offline paired baseline-vs-optimized comparisons, counts, simple means/standard deviations, *approximate normal* 95% intervals, reported-cost differences, acceptance rates, attempts, elapsed time, cache fractions, and explicit `digest_review` missed-failure flags. Also drafts a **proposed** protocol. Does **not** run experiments, freeze approved protocol bytes, enforce budget live, or establish causal savings.

### Test and fixture inventory

- `test_recorder.py` — synthetic records, missing values, acceptance provenance and JSONL.
- `test_digest.py` — full artifacts, digests/expansion, blind-spot example, UTF-8/JSON parsing flags, timeouts, file corruption and path/symlink rejects.
- `test_codex_adapter.py` — synthetic Codex completion, partial streams, malformed/unknown events and invalid counters.
- `test_claude_adapter.py` — synthetic Claude/xKiro identity, missing billing/cache fields, model changes/retries and incomplete streams.
- `test_evaluate.py` — synthetic paired data, pairing mismatch and draft protocol state.
- `fixtures/` contains the sanitized Codex, Claude, generic record, and paired-evaluation inputs. **All are synthetic.**

The code is small and self-contained using Python standard-library modules. It has not yet demonstrated real costs or token savings.

## 3. Precise commands for a fresh coding agent

Run from **the repository root** after checking out the correct feature branch:

```powershell
git status --short
git branch --show-current
git log -1 --oneline
python -m unittest discover -s experiments/agent-efficiency -p 'test_*.py' -v
```

Use examples from [README.md](README.md) to exercise **offline** adapter and evaluator commands with bundled synthetic fixtures. Choose a permitted scratch directory for full log artifacts. Do not commit real outputs, especially private code or prompts. Do not run a live `codex exec` or `claude` model call under the assumption that fixture parsing grants spend authorization.

If working from the Owner's Windows PC, **inspect local uncommitted work and local branch divergence before checkout/pull/merge**. Do not auto-reset, stash, force-push, or overwrite local files. Keep the feature branch unmerged until reconciled and approved.

## 4. Important limitations and open validation questions

**A. Actual runtime is not yet verified.** Codex Cloud reportedly had Codex CLI `0.167.0-alpha.4` and could inspect `exec --help`, but did not run a live task. Local Codex version, Claude Code installation, xKiro route/model and supported event surfaces are **unverified**. Gather actual event samples only with Owner-approved bounded calls and appropriate redaction.

**B. Route compatibility is narrower than the conceptual architecture.** The current recorder's `validate` requires Codex route `codex/native-or-configured` and Claude Code route prefix `claude-code/xkiro/`. In contrast, the Claude adapter accepts a configurable `--gateway` and builds `claude-code/<gateway>/stream-json`. Thus **non-xKiro gateway labels may fail validation** in the current code. Do not advertise general gateway support as tested; reconcile the contract before additional providers are enabled.

**C. Paired input is a different shape from the run-record schema.** `evaluate.py` pairs two records with a `task_id` and optional `digest_review`, but the Phase 1 schema does not include `task_id`, and evaluation fixture records are partial. An external matching/enrichment layer would be needed before straightforward evaluation of live JSONL run records. **There is no demonstrated direct end-to-end recorder → evaluator flow yet.**

**D. Statistical and economic claims must remain conservative.** The evaluation reports average savings for known accepted/accepted paired cost observations and simple normal intervals; it is **not yet a full CPAT estimator** (failed attempts and unequal success outcomes can skew interpretation). Unknown cost is not zero, and the budget status is not enforceable with missing billing. The evaluator's `BENEFIT_OBSERVED` is a provisional calculation on user-supplied inputs, **not** proof of statistically significant benefit or authorization to deploy. Sample-size/power, paired confidence procedures, predeclared decision rules and false-negative risk require additional work before conclusions.

**E. Digest summarization can hide critical details.** A test shows a root-cause marker can be outside the excerpt while still recoverable from full artifact. This does **not** prove agents will request expansion when needed. Digests and `important_lines` are heuristic views and must not replace required full independent verification. Treat `SUMMARY_TRUNCATED` and `DIGEST_INCOMPLETE` as reasons to inspect further.

**F. Evidence and host-security boundaries.** An artifact hash checks bytes but does not establish command authenticity, test coverage, safe log content, approval provenance or race-free filesystem containment. The adapters do not safely collect raw host sessions by default. No Supervisor or model-rotation enforcement is included. No automated budget stop occurs in a live agent session.

**G. Compatibility with other providers/apps is a future design intent, not established support.** Adding a new harness/model route requires a deliberate adapter, real fixture, capability and permission review, unit tests and empirical verification. Do not substitute a hard-coded default model or create a separate GUI merely to support routing.

## 5. Next tasks, in the correct order

**Current safe checkpoint:** Pause after offline Phases 1–5; do not automatically integrate into CouncilFlow.

1. **Reconcile the Owner's local checkout** with this Cloud feature branch; protect any unpushed or uncommitted work.
2. **Re-run the existing 20 toolkit tests** in the target execution environment, then confirm actual Codex/Claude Code versions and supported output surfaces. Do not copy credentials or API endpoints into logs.
3. **On a separate, explicitly approved bounded test**, ingest a real sanitized Codex event stream and real Claude Code-through-xKiro stream; record source and model identities and which fields are actually present. Do not assume proxy caching/billing follows native Anthropic rates.
4. **Address observed contract gaps** (e.g., evaluator pairing, route validation, incomplete telemetry handling) **only if needed for a real evaluation**, as separately authorized work.
5. **Prepare and obtain Owner approval** for exact experiment tasks/budget, minimum worthwhile effect, reliability and digest-miss thresholds, sample size/decision rules, maximum time and stop conditions. Freeze the approval artifact by SHA-256 *before* the first controlled experiment. Conduct real paired measurements only after approval.
6. **Evaluate empirical benefit and decide**, with proper uncertainty reporting. Phase 6 integration into CouncilFlow's live skill is **not authorized** here; neither are global hooks or changes to the frozen Gate 3 candidate. The universal model selector is separate work.

For each subsequent agent handoff: identify **actual model and route**, exact branch/commit, files changed, commands run and observed results, remaining unknowns, and whether changes were merely local, pushed to a branch, or merged. Distinguish observed tests from prior agent-reported tests. Never silently rewrite these status claims.

## 6. Owner control and non-normative status

The closed Council research and this prototype do not amend the frozen CouncilFlow architecture, Gate 3 Owner Charter, or security and authorization rules. For current Reviewer duties, use the **newer Charter** (three-way comparator and deterministic command rerun), not historical UX scoring. The existing skill may have documented gaps; do not quietly fix them during an unrelated efficiency task. The toolkit is **optional**, must not delay approved CouncilFlow development by turning into another audit cycle, and requires separate Owner consent for consequential integration or live spend.

**Checkpoint summary:** Five phases have *offline implementation*, with 20 tests *reported* passing by Codex, plus fixture smoke checks. Files/logic were inspected; real CLI/gateway execution, cost and cache observability, statistically defensible CPAT savings, and CouncilFlow runtime integration remain **unverified**.
