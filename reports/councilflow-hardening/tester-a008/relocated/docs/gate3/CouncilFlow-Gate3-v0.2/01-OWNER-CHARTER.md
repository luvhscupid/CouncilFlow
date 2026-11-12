# Owner Charter — controlling intent

**Source:** Owner's instructions relayed through Claude in Council Round 2 and accepted by GPT. **Evidence:** CLAIMED as relayed Owner words; treated as controlling project requirements, not as experimental proof.

## Primary goal
The Owner is not a human courier. The Owner supplies the Planner with frozen instructions developed separately in the manual Owner / Claude / GPT / Astra Sol Council. Thereafter, internal Codex agents hand work to each other without relaying by the Owner. Only the Planner or Manager sends routine plain-English output to the Owner.

## Fixed workflow
**Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner**

- **Planner:** Leads; holds the Owner's frozen plan/criteria verbatim; performs the final criteria check. May organize, but not silently rewrite, weaken, omit or add mandatory acceptance criteria.
- **Manager:** Assigns Worker tasks and handles in-scope rework; returns verification results to Planner. Cannot become the coding Worker.
- **Worker:** Implements.
- **Tester:** Tests Worker's output and records executable evidence.
- **Reviewer:** Independently compares the Worker's output, the Tester's output, and the Owner's original frozen plan; re-runs one Tester-declared deterministic command and compares exit code and normalized-stdout SHA-256; submits findings to Manager. **Not a mandatory UX scorer.**
- **Owner:** Submits frozen criteria once; can provide real authorization decisions. Does not move internal outputs, messages or files between agents.

## Scope
Automate only internal Codex role-to-role handoffs. The external cross-model Council remains manual. Maintain the preferred structured communication policy without assuming JSON alone enforces identity or security. Token savings / hallucination reduction are hypotheses that require measurement against a normal Codex baseline; not pass/fail gates in this experiment.

## Supersession
Any earlier CouncilFlow bundle requirement defining Reviewer chiefly as an advisory UX evaluator or requiring Owner to relay agent messages is superseded by this Charter. No additional UX role is introduced.
