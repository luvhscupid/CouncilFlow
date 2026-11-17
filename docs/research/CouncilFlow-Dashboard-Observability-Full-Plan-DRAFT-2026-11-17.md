# CouncilFlow Dashboard and Observability — Full Development Plan

**Status:** DRAFT_NOT_AUTHORIZED — planning record, Owner review required before experiments, implementation, installation, spending, merge, or release.  
**Date:** 2026-11-17  
**Council participants:** Owner, GPT-6 (OpenAI), Claude Sonnet 5.5 (Anthropic)  
**Repository baseline inspected:** main at 3bf08cde1ae012d3bf6ef483015ca087bd8f420b  
**Document authority:** NON-NORMATIVE research/design proposal. It does not supersede the Gate 3 Owner Charter, frozen Architecture Specification v1.0/Security Annex v1.0-A, approved Owner decisions, role policy, source-fidelity rules, or current installed skill.  
**Scope:** Optional observability and user interface for the existing CouncilFlow host-native workflow skill; no change to the execution authority chain.

**2026-11-17 implementation addendum:** The Owner subsequently authorized the offline, read-only dashboard, presentation projection, synthetic fixtures, tests and associated documentation in a one-shot implementation request. That narrowly supersedes this document's original implementation pause for those deliverables only. The original planning record below remains historical and NON-NORMATIVE; hooks, host experiments, persistent services, security/workflow changes, paid APIs, deployment, release, merge and push remain outside this authorization. See section 17 for the implemented scope and verification.

## 0. Decision summary

**Council consensus:** Pursue a removable, read-only dashboard. Existing CouncilFlow contracts and evidence remain the source of truth. Examine optional live telemetry from official host lifecycle events in a bounded experiment before promising real-time features. Do not adopt a persistent backend merely to animate a UI. No automatic model switches, role control, permissions, billing, or approvals through the dashboard.

**What was decided in the discussion versus what is still proposed:**

| Topic | Design-council resolution | Verification/authorization state |
| --- | --- | --- |
| Viewer derived from existing records | Base architecture A | Concept accepted; implementation NOT authorized |
| Optional host-event recorder | B is a bounded experiment | Experiment NOT authorized |
| Always-on server, gateway, new orchestration runtime | C deferred | No implementation |
| Truthful, separately labeled live activity | Required design invariant | Awaiting host feasibility |
| Acceptance criteria and phases displayed independently | Preferred progress semantics | UI not built |
| Tokens, model identities, cost, ETA | Show only genuinely measured and correctly attributed values | Many fields UNKNOWN |
| Owner-facing approvals | Display needs-action only; do not approve from viewer | No control surface |
| Hosted/public dashboard | Out of scope | Not authorized |

**Success definition:** An unfamiliar Owner can answer: What is happening? Which role is involved? Which evidence supports progress? What failed or needs attention? What is verified versus merely reported? The UI has no influence on CouncilFlow when turned off, closed, stale, or crashed.

## 1. Controlling sources and current evidence

Read these in order before any approved implementation:

1. ../../AGENTS.md — product identity and fixed role chain.
2. ../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md — controlling role responsibilities and independent Tester/Reviewer duties.
3. ../../.agents/skills/council-flow/SKILL.md and references/roles.md, references/communication.md, references/source-fidelity.md, references/recovery.md.
4. ../../.agents/skills/council-flow/policies/roles.yaml and scripts/contracts.py.
5. ../../README.md, ../../RELEASE.md, ../technical/host-packages.md, ../technical/structured-communication.md.
6. ../../reports/documentation-release-sync/gate3-run-01.md and claude-calc-001.md.

Snapshot facts at the baseline: CouncilFlow is a workflow skill using host-native subagents, not an agent platform or sandbox. Codex's recorded Gate 3 run is NATIVE_ROLE_WORKFLOW_PARTIAL (E1/E2/E4 unverified). One separate Claude Code plugin smoke run is recorded VERIFIED_ACCEPT, with native role sessions and an 11-message validated sequence; that is one run, not universal host proof. Existing JSON packets, optional JSONL diagnostics and contract validation provide a starting point, but none authenticates host transport or forces an event recorder to run. Local .councilflow/runs/calc-001 records were referenced in a separate smoke-test checkout; they are NOT assumed present in every installation or included in main.

Historical reports and draft research are not authorization for new behavior. For implementation, recheck the active target branch and compare against this pinned baseline; do not silently treat the baseline as the latest live host state.

## 2. User experience brief

### The intended experience

A compact, responsive mission-control page inspired by a live development console, with:
- Project/task title, run identity, current phase, active role, last observed event and staleness.
- A clearly defined progress indicator (not a fictional universal 0–100 completion estimate).
- Separate role cards: Planner, parent Manager, Worker, Tester, Reviewer; actual reported model slug or UNKNOWN.
- A human-readable activity timeline, with optional safe tool-category events and evidence links.
- Acceptance criteria matrix: pending, implemented, checked, reviewed, finally accepted, failed, blocked.
- Files changed, candidate/attempt history, tests, failed checks, Reviewer rerun comparison, warnings, and Owner decisions needed.
- Elapsed time and last-event time when timestamps are observed; ETA/cost/tokens only with qualifying evidence.
- A lightweight code activity panel only if sanitized diffs or safe changed-file metadata are explicitly available.

The aesthetic can be animated, but animation must be driven only by new observed data or labeled demonstration fixtures. No simulated typing or false progress for actual runs.

### What the UI must distinguish

1. **Run status:** queued, active, waiting-for-Owner, blocked, failed, completed, cancelled, unknown/stale.
2. **Role lifecycle:** not observed, started, active, stopped, failed, waiting, unknown.
3. **Evidence/verification:** unverified, claimed, structurally validated, execution observed, final Planner accepted, rejected/blocked.
4. **Data source:** host event, validated packet, file/hash record, agent assertion, UI derivation.
5. **Freshness:** last observed event time; a missing stop event does NOT establish that the role is still running.

The dashboard never changes CouncilFlow's role sequence:
Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner.

## 3. Architecture alternatives and selection

| Architecture | Input | Strength | Limitation | Decision |
| --- | --- | --- | --- | --- |
| A: offline read-only viewer | Explicitly imported, validated, sanitized snapshot of existing records | Host-neutral, easy to remove, no service | Manual refresh; not necessarily live | **Permanent foundation** |
| B: optional event observer | Supported local hooks / approved host notifications + immutable existing records | Real role activity and measured timing | Host-specific gaps, trust prompts, overhead | **Feasibility experiment only** |
| C: dedicated service/WebSocket/backend | Server-owned event system | Rich continuous streaming | New runtime, auth, attack surface, operational burden | **Defer** |

**Logical pipeline:**

Existing host execution + CouncilFlow packets/evidence (authoritative)  
→ bounded parser and host-specific observer (optional; not authoritative)  
→ allowlisted, versioned presentation projection (derived)  
→ read-only viewer (file-import v1; optional refresh mechanism if separately proven).

Observer failures must never alter, block, retry, approve, reroute, or terminate execution. The dashboard cannot become another Manager, Supervisor, security guard, event authority, or source of acceptance.

Use an explicit project-local opt-in for a later observer. Do not add global hooks, persistent daemons, remote network services, API keys, or mandatory dependencies to the base install. Do not alter the existing contracts to make a UI easier; adapt the projection to the contracts.

## 4. Feasibility gates: inspect hosts before writing hooks

### Codex

Official hooks reference (reconfirm installed version and surface): https://learn.chatgpt.com/docs/hooks

Documented capabilities at research time: SessionStart, SubagentStart/Stop, PreToolUse/PostToolUse, turn/session IDs and common model field, trust review via /hooks, project .codex trust. **Critical constraint:** Codex documentation says command-hook async is parsed but not yet supported; do not assume async:true makes Codex hooks nonblocking. Codex tool events may not supply agent_id; parent session_id alone is insufficient for role attribution. Some tools bypass local-function hooks. This must be measured.

**Unverified:** per-subagent model identity, direct per-role token usage, applicability to the precise interactive Codex Desktop/CLI version, and whether every role is visible. In the inspected hooks reference, PostModelRequest/token_usage was NOT located: treat the claim as unverified, check a versioned schema before planning usage capture. Do not adopt codex exec --json or app-server merely to get telemetry if that would replace the Owner's normal interactive workflow.

### Claude Code

Official reference: https://code.claude.com/docs/en/hooks

Documented: SubagentStart/Stop carry agent_id and agent_type; plugin agents can have namespaced agent_type; supported tool hooks can expose an agent_id; async command hooks exist. Even asynchronous hook output can be delivered as model context on a later turn, so an observer must emit **no stdout or stderr** and no decision fields. Avoid storing prompt/transcript/tool input/last assistant message. Claude's plugin-scoped hook behavior and installed version must be checked. Whether hooks expose accurate per-role model or token usage remains unverified.

### Hook trust and scope

For Codex, manually inspect proposed hooks via /hooks, trust exact reviewed hashes, and use only a trusted scratch .codex/ layer. No --dangerously-bypass-hook-trust. For Claude, review the plugin/project hook source and commands first. Hooks execute with the host user's privileges; consider path controls and permissions. No broad read/write permissions, no network callbacks, no access to unrelated repositories.

## 5. Phase 0 — preflight and registered experiment protocol

**Goal:** decide if the event-observation approach is safe enough even to test.

1. Record exact host binary/app versions, OS, Python, active repository, working root, host surface, plugin source and loaded configuration. Do not print secrets or full provider settings.
2. Ensure a separate scratch repository and a clean baseline. The main CouncilFlow checkout and existing efficiency experiments remain untouched.
3. Read controlling source/role policies and check current native integration documentation.
4. Pre-register expected normal path: Planner publishes → Manager assigns → Worker reports → separate Tester reports → separate Reviewer reports → Manager decision → Planner checks → Manager reports to Owner. Rework may loop through fresh Worker/Tester/Reviewer attempts. Only actual observed events count.
5. Pre-register hypotheses: Claude role start/stop attributable by agent_id + namespaced agent_type; Codex subagent start/stop likely attributable; Codex individual tool events might be unattributable; model and usage often UNKNOWN.
6. Pre-register controls and measurements before observing results. Separate hook-disabled baseline and hook-enabled run. Do not demand identical LLM outputs.
7. Fix storage location outside tracked source, local-only permissions, duration/event cap, cleanup procedure, and abort thresholds.
8. Owner approval must precede ANY hook installation or live trial; documenting this phase is not approval.

**Deliverable:** a short preflight record and experiment specification with version/surface matrix and no installed hooks.

## 6. Phase 1 — minimal telemetry experiment (one host at a time)

**Allowed source:** host-documented lifecycle metadata only. Start with Claude Code (known working plugin smoke baseline), then Codex if installed hooks can be safely tested. A negative or partial result on one host must not cancel useful static-viewer work on the other.

**Instrumentation proposal (not code):**
- Minimal local recorder command with bounded input; parse one hook JSON object in memory.
- Extract by explicit field allowlist: observed event type; locally acquired wall-clock timestamp; host type/version; opaque run/session/turn ID; agent ID and agent type *where present*; model field only as host-reported and separately scoped; tool category/name only.
- Never persist raw stdin, full paths, prompts, transcripts, tool_input, tool_response, source code, command arguments, environmental variables, credential material, or chat history. Hash IDs only if correlation remains possible and salts/keys do not leak; do not imply a hash anonymizes secrets.
- Write a bounded sanitized event record to a scratch, untracked location, ideally append-only with atomic/serialized writes and safe filesystem checks. No shell quoting of untrusted stdin, arbitrary filepath reads, or symlink traversal.
- Recorder writes nothing on stdout/stderr. It does not return a hook decision, extra context, or any permission/continue field. It should finish with success on telemetry failure without blocking host execution; record only a safe local failure counter when possible.
- Codex command hooks might be synchronous: enforce a tight measured deadline, measure overhead and rejection/failure effects. If non-interference cannot be demonstrated, reject Codex live hooks for now.
- Claude async command hook is eligible, but does not confer a guarantee of zero overhead; account for cancellation and missing tail events.
- No broad file watches or transcript scraping as a shortcut.

**Baseline/control:** run the same small authorized task and acceptance fixture in scratch with recorder disabled and enabled; compare structural invariants (role order, actual native delegation, validated packets, required evidence, no extra prompts/permissions, declared outputs) rather than identical generated code. At least one trial per condition per host is a feasibility smoke test, not statistical proof. Report exact trial count, any incomplete trials, and budget consumed.

**Capture metrics:** events emitted/received; per-event delay where a trustworthy origin timestamp exists; monotonic local receive order; unknown attribution; duplicate/missing IDs; max/median hook wall time; added workflow duration (indicative only); stdout/stderr silence; unauthorized fields retained (must be zero); observed hook failures; retention bytes.

**Pass:** role starts/stops map to native identities with traceable evidence; metadata arrives during the run; no model-facing output; bounded storage; required trust followed; no structural regression observed in measured trials; recorder can be fully disabled.

**Partial:** role-level observability works but tool-level attribution, usage, model, or some events are missing. Keep those fields UNKNOWN, do not infer them.

**Fail/STOP:** unexpected model-facing output; behavioral/control side effects; credential/prompt/content retention; untrusted or global hook requirement; measurable stall outside pre-registered tolerances; reliance on undocumented transports or replacements for interactive execution.

**Fallback:** build only the static evidence viewer; do not escalate automatically to a server, SDK-owned agent harness, or cross-host interception proxy.

## 7. Role identification and event correlation

A host event carrying agent_type is not proof of CouncilFlow role unless the mapping is externally established.

- Claude plugin agents: verify exact namespaced agent_type against observed loaded plugin agent definitions.
- Codex custom agents: verify exposed profile/type against loaded .codex/agents; fallback-to-generic native agents may be **unattributable**.
- Link host agent_id to assignments using host-observed invocation metadata where available, never packet sender.role alone.
- Manager is the parent host session; Manager activity may not be emitted as a named subagent.
- Keep separate run_id, attempt_id and native agent instance fields. A fresh Worker on rework must appear as a new attempt; never merge histories merely because role names match.
- If mapping is ambiguous, UI displays “unattributed agent” or “reported role, host identity unknown.”
- Tool events without agent_id stay **session-level activity** rather than being falsely attached to Worker or Tester.
- Model: show host-reported model only at the granularity actually observed. Parent model inheritance may be real; do not invent role-specific routing.
- Token use: capture only documented counters with explicit scope (model-request attempt, session, turn, agent). Treat retries and duplicate cumulative counters carefully; never add incomparable counters or infer dollars from subscription usage.

## 8. Presentation projection (derived; never a second authority)

Introduce a versioned **view format**, e.g. councilflow-dashboard-view/0.1 (working name only), generated from validated input records and allowlisted host events. Do not change the council-flow 1.0 task contract or redefine its evidence. Projection is disposable and rebuildable.

Proposed safe sections:
- source: project/run IDs, source host, observed version, source snapshot digest and ingestion timestamp (all nullable where unsupported).
- task: sanitized display title, phase, reported status, last-update timestamp, stale flag.
- roles: role, host-agent mapping status, lifecycle state, host-reported model (nullable), attempts.
- acceptance: original criterion identifiers, current stage, final_check outcome and bound candidate/attempt identifiers.
- timeline: event ID, normalized type, receive timestamp, source kind, attribution confidence, safe caption.
- evidence: identifiers/digests, validation tier, command result summary; never embedded raw artifacts.
- metrics: elapsed observed seconds, safe token counters with scope and coverage, file count, check count, no unsupported cost.
- warnings: missing evidence, unmatched role IDs, stale events, failed checks, telemetry gaps, corrupted records.

Sample **illustrative presentation object**, not CouncilFlow wire protocol and not runtime evidence:

~~~json
{
  "view_schema": "councilflow-dashboard-view/0.1",
  "synthetic": true,
  "run_id": "demo-001",
  "host": {"name": "claude-code", "version": null},
  "task": {"title": "Synthetic example", "phase": "testing", "last_observed_at": null},
  "roles": [{"role": "tester", "state": "unknown", "host_agent_id": null, "model_reported": null}],
  "progress": {"final_accepted": 0, "criteria_total": 3, "ratio": 0},
  "activity": [{"kind": "synthetic", "label": "Example only", "observed_at": null}],
  "metrics": {"tokens": null, "cost": null, "eta_seconds": null}
}
~~~

All nullable fields render “Unknown / Not reported”, never default to 0. The projection builder and viewer must reject unknown schema versions safely, render untrusted strings as text rather than HTML, limit size/depth/count, and avoid executing any code from imported data. Do not use file:// dynamic-script injection as a generic real-time transport: serialized executable JavaScript is a content-injection hazard. Prefer a deliberate local JSON file import for offline v1; investigate host-approved file access or a tiny loopback-only reader only if live update requirements justify it later.

## 9. Progress mathematics and temporal truthfulness

**Primary number:** N_final_accepted / N_original_required criteria; if total is 0 or original criteria are unavailable, show Not assessable, not 0%. Count unique immutable original criterion IDs, not duplicate messages or agent self-reports.

**Secondary per-criterion lifecycle:** not started → Worker reported → Tester reported pass/fail → Reviewer compared/reran → Planner final accepted/rejected. Intermediate states are not “verified completed”; show their distinct icons and stage counts. A later candidate/rework can supersede earlier passing observations. Preserve the prior result in attempt history, never silently mutate it.

**Percent design:** show exact fraction always. Percentage is optional and must be labeled “final acceptance” with denominator. With 3 criteria, 1/3 = 33.3%; do not imply precise time completion. Display a separate phase/role strip that tracks observed events rather than estimated percent.

**Rework:** if a previously accepted criterion becomes invalidated by a new candidate or changed original scope, do not carry its acceptance automatically; show supersession and fraction changes, with provenance. Never change frozen Owner acceptance silently.

**Timing:** elapsed from trustworthy observed start to current observed end or live-now; viewer clock cannot prove activity. Last-event age is displayed independently. Without observed start, elapsed UNKNOWN. Stale threshold is a labeled heuristic, not proof of crash. ETA and expected finish initially **Not available**. Only explore ETA after a separately approved dataset and calibrated prediction method; show ranges, sample count, confidence and errors, never a precise unearned countdown.

**Usage:** per-role tokens and rates only if origin, scope, cumulative/delta semantics and retry handling can be established. No implied paid API billing from subscription telemetry. Costs require actual billing evidence or a clearly labeled rate assumption and must not be shown as charged dollars.

## 10. Frontend scope and UI layout

**Desktop:**
- Header: project/run selector (one run in v1), verification badge, last observation, elapsed time.
- Main progress: accepted-criteria fraction and phase rail.
- Left column: Planner/Manager/Worker/Tester/Reviewer cards, expandable attempts with host/model attribution label.
- Center: newest-first human-readable activity timeline and optional safe command category feed.
- Right: acceptance matrix, warnings/blockers, evidence summaries, next expected checkpoint.
- Bottom drawer: candidate history, test summaries, captured-safe changed-file counts, source/provenance details.

**Mobile:**
- First viewport: current status, “Action needed”/blocker, last event and accepted fraction.
- Collapsible role status list, phase strip, timeline, criterion chips, evidence drawer.
- Do not make tiny five-column tables mandatory on a phone.

**Visual design:** restrained developer-console theme with crisp hierarchy, compact readable typography, gentle event-driven transitions, no constant pulsing for stale/unknown state. Light/dark support, keyboard navigation, focus rings, semantic text labels, reduced-motion preference, and no color-only signaling. Use fixture-driven preview labels (“DEMO DATA”) permanently visible in demos.

**Recommended skills when the UI phase is approved:** domain-modeling for projection, codebase-design for non-invasive data boundary, frontend-design/ui-ux-pro-max for interface, react/tailwind only if interaction complexity justifies them, playwright-cli for responsive/accessibility smoke checks. None is required for Phase 0–1.

## 11. Phased delivery with explicit acceptance tests

| Stage | Deliverable | Entry gate | Exit criteria |
| --- | --- | --- | --- |
| 0. Read-only research/preflight | Exact host capability inventory, baseline, threat model, pre-registered protocol | Owner authorizes preflight | Supported hooks and surface/version documented; no host changes |
| 1. Optional event feasibility | Sanitized events in scratch + comparison report for Claude and/or Codex | Separate Owner approval for hook test, trust review | Pass/Partial/Fail per host; no secret retention or model-facing output; measured overhead |
| 2. Projection library | Versioned rebuildable view from existing fixtures/evidence | Owner chooses scope after Stage 1 | Strict allowlist, schema/version/error tests, provenance boundaries, no contract mutation |
| 3. Static/offline MVP | File-import dashboard with role cards, criteria progress, timeline, blockers | Stage 2 passes | Works offline on packaged sample, mobile+desktop tests, labels synthetic/unknown honestly |
| 4. Optional live adapter | Local safe refresh/poll against verified sanitized projection | Stage 1 passes for that host; Owner approves | Low-latency observed updates, partial attribution shown correctly; no persistent service required |
| 5. Polish and portability | UX refinements, multi-run, diff summaries, usage charts where reliable | Real user feedback and measured value | Cross-host regression, UI accessibility/security checks, documented install/uninstall |

Each stage is its own independently reviewable slice. Do not combine telemetry, backend, UI and model-selection changes in one code change. Pause for Owner acceptance and budget review between stages.

### Acceptance IDs for a future approved implementation

- **DASH-AC01:** Base CouncilFlow runs identically without the dashboard installed.
- **DASH-AC02:** Viewer cannot dispatch role packets, change role state, approve changes, or modify source/evidence.
- **DASH-AC03:** Every displayed activity item has visible source/provenance and never promotes agent text into host observation.
- **DASH-AC04:** Final acceptance fraction derives solely from original criteria and valid final Planner evidence, with stale/rework states handled.
- **DASH-AC05:** Unknown model, token, cost, ETA and event attribution show as unknown, never zero or fabricated.
- **DASH-AC06:** Observer emits no stdout/stderr, raw data persistence, or decision/control fields.
- **DASH-AC07:** Hook trust is explicitly reviewed; no global configuration or trust bypass.
- **DASH-AC08:** Malformed, oversized, path-traversal, symlink, duplicate and injection inputs fail safely at viewer/projection boundaries.
- **DASH-AC09:** Recorder crashes, permission failures, disk-full and missing event scenarios leave CouncilFlow execution unaffected and UI honest.
- **DASH-AC10:** Responsive mobile/desktop behavior, keyboard navigation, screen-reader labels and reduced motion verified.
- **DASH-AC11:** Host-specific event coverage table and measured latency/overhead included in every live-feature claim.
- **DASH-AC12:** Installation, disablement, uninstall, local retention and data cleanup documented and exercised.

## 12. Security, privacy and failure model

Threats: malicious tool arguments/prompts embedded in hook stdin; misleading agent reports; forged attribution; symlink/path traversal and concurrent writes; file contents or secrets leaking through timelines; HTML/script injection; unsafe localhost endpoint; unbounded logs; project-level hook privilege; stale artifacts; incorrect attribution leading to false acceptance.

Mandatory controls:
- Allowlist only scalar metadata from known event types. Exclude raw prompts, tool arguments/outputs, environment, hidden instructions, transcripts, command lines and file content by default.
- Keep records local, opt-in, outside Git/source and with configured size/count/age limits. Use private OS file permissions where possible. No cloud sync or telemetry export by default.
- Explicit recorder output silence and non-decision behavior. On failure, fail open for *workflow execution* but fail closed for *telemetry claims*: mark unknown/stale, never invent continuity.
- Never follow artifact paths from untrusted packets into arbitrary filesystem locations. If a future evidence viewer opens an artifact, require validated, authorized, immutable handles/root checks and avoid TOCTOU assumptions.
- Parsed view fields must be escaped as text; no arbitrary HTML/JS/eval or raw Markdown execution from imported events.
- Browser or local helper must not accept arbitrary remote connections, cross-origin writes or destructive actions. No exposed server in v1.
- Provenance labels do not imply sender authentication. Hash integrity does not imply correct test execution. Host observation does not imply semantic acceptance.
- Do not alter frozen plans, accepted oracles, role responsibilities, Owner authorizations, Supervisor controls or existing security annex.

Negative controls: inject synthetic secret-shaped strings in ignored fields and prove they never appear in output; malformed JSON and oversized nested input; missing/duplicate events; swapped agent IDs; forged packet sender; stale/modified candidate; crash in recorder; writable/log path escape; hostile HTML labels; disconnected viewer.

## 13. Measurement and go/no-go rubric

Record a compact experiment report containing host/version/surface; scratch repo and commit; exact tested event names; tool-level coverage; role-mapping basis; observed vs missing metadata; sample count; elapsed/latency/hook overhead; on/off structural invariants; safety test results; storage volume; failure/partial reasons; remaining uncertainty.

A **PASS** is limited to the capabilities actually observed on that host. A **PARTIAL** is acceptable when role start/stop works but individual tool events or usage attribution is missing. A **FAIL** rejects the unsafe live mechanism but does not reject offline viewer architecture A.

**Do not claim “real-time Codex support” from a hook schema alone. Do not claim “per-role billing” from model-token counters alone.** Any observed performance comparison with N=1 per condition is descriptive, not proof of zero impact or improved productivity.

Abort the active experiment if it exceeds the explicitly Owner-approved time/usage budget, needs global config changes, triggers unexpected prompts, retains restricted fields or requires work outside scratch. No unbounded iteration just to make hooks pass.

## 14. Deliverables and file organization (proposed, not created)

Prefer preserving the current canonical skill and Claude plugin structure. Possible future paths, only after scope approval:

- docs/research/this-plan and a separate docs/research/experiment-results/... evidence report.
- docs/technical/dashboard-observability.md **after** implementation is verified.
- tools/dashboard/ for a strictly offline projection/fixture generator, if justified.
- viewer/ for a separately removable static frontend, if approved.
- Optional project-scoped observer scripts/config under host-specific integration directories only after trust review; not in global settings.
- tests/ for projection/security/compatibility controls; UI smoke tests via Playwright if practical.
- Untracked local .councilflow-observer/ scratch output (example location only, not an existing guaranteed directory).

Do not bundle test recordings, raw hooks, credentials or private host logs into public release archives. Do not modify the canonical JSON message protocol merely for a display view. Update public README/release claims only when actual evidence changes.

## 15. Decision log from GPT/Claude design council

- Claude initially recommended static-only A. GPT challenged exclusion of B due to documented host event mechanisms.
- Both accepted A as foundation, B as experimental, C as deferred.
- Claude acknowledged Codex/Claude lifecycle hooks and the recorded Claude smoke run. Both agreed role/model/usage mapping needs actual validation.
- Claude added six guardrails: silent hook output; Codex tool attribution may be missing; host model value may describe parent; explicit Codex trust; structural rather than deterministic outcome comparisons; pre-registered role path and retry-aware usage semantics.
- GPT accepted the guardrails, refined provenance and progress: host-observed event ≠ semantic success; artifact hash ≠ successful test; finalized Planner acceptance is the primary count.
- **Additional post-debate documentation correction:** Current Codex hooks reference states async command hooks are parsed but not yet supported. The plan does not assume Codex async. The inspected reference did not substantiate PostModelRequest token_usage; keep it unverified pending version-specific docs.
- Full dashboard plan requested by Owner for storage; this request **authorizes documenting the proposal only**. It does not automatically approve hook tests or implementation.

## 16. Owner checkpoints and next action

1. **Owner review of this document:** accept, reject, or amend scope and caps; do not treat saving it as freezing normative architecture.
2. **If approved, Stage 0 only:** collect exact host/version capabilities and pre-register an observational test, without modifying source or hooks.
3. **Owner explicitly approves Stage 1:** run the smallest safe per-host scratch experiment with trust review.
4. **After observed evidence:** select A-only, A+Claude live, A+Codex live, or A+both. It is acceptable to keep asymmetric capabilities.
5. **Only then design/build the viewer** using truthful observed data and clearly labeled synthetic presentation fixtures.

**Immediate next deliverable:** preflight and feasibility protocol; no dashboard code or hook installation yet.

### External references inspected for this plan

- Codex hooks and trust reference: https://learn.chatgpt.com/docs/hooks
- Codex plugin-bundled hooks: https://developers.openai.com/plugins/build/plugins
- Claude Code hooks/events/async reference: https://code.claude.com/docs/en/hooks
- Codex programmatic host integration context (not authority to replace current workflow): https://developers.openai.com/blog/codex-as-a-platform

**End of plan.**

## 17. Design and Implementation Skill Matrix

**Implementation scope:** Optional offline dashboard in `dashboard/`, based on the planning branch `docs/dashboard-observability-plan-20261117` at `12a4e366bb50245de44ab0ce3363541633c8a16b`. Implemented on `feat/dashboard-observability-mvp-20261117`. This section records engineering choices and observed verification, not a change to the frozen CouncilFlow workflow or security specifications. Sections 4–7's hook feasibility experiments were not performed or implicitly authorized.

| Skill | Selection rationale | Actual invocation/application and limits |
| --- | --- | --- |
| codebase-memory | Confirm project/root and package/source scope | Read SKILL.md; list_projects, get_graph_schema, search_graph and check_index_coverage invoked. Exact Windows root mapped to E-Saint-PROJECTS-CouncilFlow-main. Bounded symbol queries returned no matches; direct source inspection supplied the package/contract facts. Clean coverage is best-effort, not proof of completeness. |
| frontend-design | Deliberate hierarchy and visual identity | Read and applied: three composition directions considered, graphite/blue token system, acceptance ledger selected as anchor, responsive review of actual screenshots. |
| ui-ux-pro-max | Coherent dashboard and accessible interaction | Read; ran search.py design-system for developer operations dashboard, density 8. Used responsive, focus, target and readability guidance; did not blindly copy marketing-pattern output. |
| taste-skill | Restraint, one system, actual visual QA | Read. Applied restrained surfaces, no decorative effects, consistent edges and screenshot critique. Marketing hero/photography/palette-deal/one-section-per-screen and its marketing finish gate were unnecessary for this dense offline Operate surface; the Owner's dashboard brief takes priority. No claim of a taste-skill GATE: PASS. |
| impeccable | Operate-mode craft and mechanical quality scan | Read SKILL.md and relevant new-work/init/craft-floor guidance; context launcher, direction seed and detector actually ran. Fixed tiny functional text, skip-link hover contrast and mobile overflow/inset. Used supplied Owner brief rather than a new interview or selection gate because the Owner explicitly delegated those decisions and requested one continuous build. No hooks installed. |
| domain-modeling | Separate candidate, attempt, claim and acceptance | Read and applied; dashboard/GLOSSARY.md records precise presentation vocabulary without redefining normative roles. |
| codebase-design | Keep complexity at the parser/projection seam | Read and applied; parseSnapshot and project isolate bounded validation/acceptance derivation from DOM rendering. No speculative adapter platform. |
| react | Assess stateful frontend requirements | Read; implementation unnecessary. Native modules, details, dialog and selects cover the interaction surface with no build/runtime dependency. |
| tailwind | Assess styling approach | Read; unnecessary for a single removable static surface. Semantic CSS variables and a scoped stylesheet avoid a build pipeline. |
| vercel-react-best-practices | Assess framework/rendering costs | Read; React-specific rules not applicable to the chosen stack. Applied the general intent of bounded lists and no unnecessary dependencies; no claim of React implementation. |
| web-design-guidelines | Review semantics, focus, responsiveness and motion | Read and fetched the current guideline source. Applied native controls, labels, focus, reduced motion, long-content handling and visible import feedback. No full accessibility certification claimed. |
| playwright-cli | Actual browser interaction and screenshots | Read; CLI 0.1.24 executed against installed Edge. 40 smoke assertions passed, responsive widths 320–1440, screenshots captured and inspected. CLI obtained in npm cache, no global install. System CA verification used, never TLS bypass. |
| product-design:audit | Screenshot-led product review | Read and applied to locally served dashboard with Playwright capture. Actual screenshots exposed offscreen event-painting and mobile layout issues, repaired before final capture. Audit and limits recorded in dashboard/evidence/verification.md; no Figma/canvas or deployment. |
| product-design:ideate | Evaluate visual exploration before commitment | Read; image generation not run. Its multi-option generation and user-selection pause were unnecessary under the Owner's explicit creative delegation/no-stop instruction. Textual composition exploration preceded implementation. No external image service or paid call used. |

### Stack and design decision

Native ES modules and CSS, no production dependencies, build, server-side application or framework. A temporary loopback static-file server is only a local launch/test aid. The repository has a Python skill/package structure and no incumbent frontend dependency set; the bounded single-page interactions do not justify adding React/Tailwind. Self-contained modules, local fonts/icon and restrictive CSP keep the viewer offline. Source, tests, fixtures and docs can be removed together without changing CouncilFlow installation.

Graphite console surfaces and cool blue acceptance segments emphasize evidence rather than apparent agent motion. Desktop uses a navigation rail, overview/phase strip, five expandable role summaries, candidate acceptance ledger and activity console, then trust/resources. Mobile elevates recorded operation, acceptance, blockers and active-role summary; evidence is progressively disclosed. Light theme, explicit textual statuses, native keyboard controls, focus restoration and reduced motion are implemented. No event generator or perpetual animation pretends to be live.

### Delivered, verified and unverified

Implemented: bounded explicit JSON import, unknown-version rejection, duplicate-key/reference checks, safe text rendering, candidate-bound acceptance, preserved rework, six provenance labels, role details, combined event filters, timeline paging, evidence drawer, metrics scope details, demonstration scenario switching, long/empty/interrupted/failing fixtures and responsive themes.

Verification: 12 projection tests passed; existing Python regression suite ran 239 tests, OK with 5 skips; 40 Playwright/Edge browser assertions passed. All evidence is Windows-local. Browser checks include long titles at 1440/1024/820/768/390/320 widths, a 1,000-event timeline, import negative controls, keyboard focus and reduced motion. Final screenshots, a screenshot-led audit, reproduction commands and limits are in `dashboard/evidence/` and `dashboard/README.md`.

Not implemented or verified: live telemetry, hooks, host lifecycle attribution, real model identity/counters/billing, native packet-to-view conversion, automated source authenticity, Firefox/Safari or full assistive-technology conformance. Existing sanitized efficiency records and human-readable smoke summaries were inspected as documentation context, not relabeled into fresh dashboard execution evidence. A future separately authorized adapter can target the view format without altering CouncilFlow packets.

Launch: `python -m http.server 4173 --bind 127.0.0.1 --directory dashboard`, then open `http://127.0.0.1:4173/`. Import via the visible JSON button; bundled `dashboard/fixtures/*.json` are synthetic examples. Reload clears imported memory. Stop the server and remove `dashboard/` to disable/remove; no native/global configuration or canonical package content depends on it. The original release allowlist is unchanged and does not bundle this optional frontend.
