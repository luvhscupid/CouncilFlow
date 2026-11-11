# Operational workflow

`Owner → Planner → parent Manager → Worker → Tester → Reviewer → Manager → Planner final check → Owner`

1. Inspect authorized repository, applicable instructions, status, tools, tests,
   and available native delegation. Preserve unrelated work. Do not read other
   projects or global installations to manufacture context.
2. The Manager describes the coding goal to a real Planner. The Planner returns
   a contract defining exact outputs and acceptance before any implementation.
   The Manager may accept routine, authorized plans without asking the Owner to
   coordinate technical steps. Freeze the contract in a project report if useful.
3. External mode accepts an Owner-approved supplied plan as input. Record that
   document and provenance unchanged. The Manager may not claim the external
   conversation was invoked. Native mode works without external integration.
4. Delegate a bounded unit to a fresh Worker. Include allowed paths, unchanged
   criteria, constraints, dependencies, and evidence required. Select relevant
   approved skills only when useful. Use inherited models by default; choose
   alternatives only among actually exposed supported controls.
5. Wait for the Worker to stop mutating the workspace. Inspect its result; assign
   a separate fresh Tester to execute acceptance independently. Worker-authored
   checks help development but do not replace independent verification.
6. Assign a separate fresh Reviewer after technical verification. For a CLI,
   exercise help, a normal invocation, and a relevant error path. For a UI, use
   actual interaction where tools permit. Label unexercised behavior unverified.
7. Reject failures, record reasons, and delegate scoped repairs to fresh Workers.
   Rerun relevant independent checks after changes. A Reviewer concern may require
   repair even when automated tests pass. Preserve the original acceptance.
8. The final Planner compares outcomes with original requirements. The Manager
   reconciles evidence and remaining gaps and reports to the Owner.

## Durable evidence without infrastructure

A small task needs only a contract and concise result record. For a substantial
run, use ordinary files such as `reports/<task>/contract.json`, `events.md`,
`test-output.txt`, and `final.md`. Keep task identity, role/session identifiers,
status, evidence references, open findings, repairs, and disposition. Do not add
a database, message broker, custom supervisor, or pseudo-agent simulator.

## Example invocation

```text
$council-flow Implement an offline receipt calculator in this repository.
Accept multiple products, Decimal-safe quantities/prices, reject invalid inputs,
display rupiah, and include executable tests. Stay inside demo/receipt/.
```

The skill takes an ordinary goal, not a required JSON input. The Manager creates
internal bounded contracts. Routine authorized repairs continue without repeated
Owner approval. Consequential new scope still belongs to the Owner.

## Missing capabilities

Native delegation unavailable: preserve the plan/package and report the actual
multi-agent run BLOCKED. Do not execute one session as pretend five agents.
Custom-role selection unavailable but native subagents available: pass exact role
instructions through native delegation and record that fallback. Discovery and
explicit invocation require host evidence; static file placement and manual
instruction loading are not a runtime activation claim.
