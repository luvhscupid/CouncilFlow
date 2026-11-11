# CF-DEMO-001 acceptance map — revision 1

Planner: `/root/demo_planner`. Native plan, no application-code changes.
The immutable contract is [demo.json](demo.json). This map defines evidence to
collect; it does not grant runtime passes before implementation.

| ID | Required observation |
| --- | --- |
| D01 | Run final standard-library CLI offline; inspect imports/dependencies. |
| D02 | Execute exact repeated-item rice/onions command; observe 60,000, 43,000 and 103,000 rupiah amounts. |
| D03 | Execute a different multi-item receipt and empty invocation. |
| D04 | Independently inspect/execute Decimal API and fractional values, including 0.02 and a fraction beyond two places; check supported precision policy. |
| D05 | Execute negative, malformed, and non-finite quantity/price cases; observe nonzero error without traceback; verify zero values. |
| D06 | Check thousands and fractional rupiah display against actual calculations. |
| D07 | Run Worker tests and distinct Tester's independent behavioral probes; retain commands, exits and output. |
| D08 | Distinct Reviewer actually runs help, documented success command and input error; report usability findings. |
| D09 | Compare retained starter, original failed result, Manager rejection and fresh Worker identity. |
| D10 | Record real roles/evidence/decisions and final Planner mapping; keep invocation limitation separate. |

Implementation sequence remains Planner → Manager → fresh Worker → independent
Tester → independent Reviewer → Manager → Planner final check. Technical defects
return to fresh Worker with the unchanged contract. No static check, Worker
self-assessment, review score, or successful application test can establish
successful native skill invocation.
