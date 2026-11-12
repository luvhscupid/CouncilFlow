# 01 — Product contract and five-role workflow

## Observable product

User enters: `$council-flow Build an offline CSV summarizer with validation and tests.`

CouncilFlow must load and organize a **real** coding workflow using Codex capabilities. It must produce the program and tests, verify execution, report blockers and acceptance. A successful package build or static SKILL.md parse does not satisfy this.

```text
Owner goal and approval
        |
        v
Planner (persistent logical planning) -- approved immutable acceptance checklist
        |
        v
Manager (parent Codex, coordinator only) -- selects approved skills/agents
        |
        v
Worker (fresh implementation session) -- writes code
        |
        v
Tester (fresh independent session) -- runs/observes technical checks
        |
        v
Reviewer (fresh independent session) -- evaluates user experience, not security
        |
        v
Manager -- accept / rework / block / escalate
      [rework] ---> fresh Worker, repeat evidence for new candidate
        |
        v
Planner -- final check against original acceptance IDs
        |
        v
Owner receives deliverable, evidence, limits and necessary decisions
```

## Owner

Defines goal and boundary, authorizes consequential operations and subjective acceptance. Does not need to coordinate agents or parse debug logs. Do not request repeated approvals for routine authorized work.

## Planner

Authors explicit objective, ordered tasks, stable acceptance IDs, scope, dependencies, risk and quality criteria; checks completed work against approved plan. No coding, no tool/permission granting. An externally supplied approved plan from ChatGPT is allowed as input; never claim to have contacted that external conversation unless genuinely integrated.

## Manager

Parent Codex coordinator, *not* trusted security enforcement. Chooses suitable available agents/models and pinned approved skills subject to host capability, dispatches, evaluates evidence, orders rework, reports to Owner. Does not implement application code. Manager may perform in-scope engineering rework without a fixed retry count, bounded by resource, safety, progress and authorization. Does not weaken plan. Preserve one writer per workspace; parallel mutation only in isolated workspaces, integrated serially.

## Worker

Fresh coding subagent per attempt. Changes authorized application code and tests inside approved workspace. Returns output paths, checks and limitations. Cannot approve its own work. It may do developer-side testing, but this does not replace Tester.

## Tester

Independent fresh technical verifier, distinct from Worker. Checks actual executable behavior against approved acceptance criteria, with observed commands/results; cannot repair application code or silently change oracle. Model output is not host-enforced isolation or reliable authentication.

## Reviewer

Fresh user-perspective evaluator. Looks at task flow, friction, usability, missing needs and documented limits. Reports whether interaction was real, inspected or simulated. Does not edit product code, replace Tester, or invent human-observed acceptance. Qualitative scores are advisory.

## Manager and Planner closeout

Manager combines evidence, selects rework or acceptance proposal; Planner checks original acceptance IDs and objective; only then report to Owner. Owner approval is mandatory for scope changes, weakening requirements, unapproved capabilities, resource expansions and required subjective taste/branding decisions.

## Demonstration

Fresh invocation should generate a working, simple offline program (receipt calculator is the historical reference, but a *new* CSV summarizer is better for activation test). Include realistic malformed-input tests and a deliberate-failure/rework path if possible. Actual session/call evidence is required for the claim of multiple real agents. Manual role handoffs are not automatic invocation.
