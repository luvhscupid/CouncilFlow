# Primary Worker implementation evidence — REST-P001 / REST-A001

Actual native Worker: /root/restoration_worker. Manager assignment REST-M005 and
same-attempt developer clarifications REST-M006/M007. Frozen plan SHA-256 remains
4ee180ac24876633d62198fc71488ea82df291dcb25e83a657f900329e87f64b.
Only product implementation and assigned records were changed; no old receipt,
CSV/starter application, historical reports, global settings, external project,
credentials or permission configuration was modified. No dependencies installed.

## Implemented

- Installable scripts/contracts.py: standard-library strict JSON message, ordered
  context, expected-origin, artifact hash/path, restricted YAML policy and bounded
  optional JSONL validation; concise CLI errors. No service/database/runtime.
- Versioned policies/roles.yaml, closed references/message-contract.json and
  communication.md; all eight message purposes and five AI role payloads.
- Concise SKILL integration, every role/workflow/recovery/acceptance reference,
  four native TOMLs with only supported existing keys, README and RELEASE.
- 31 focused deterministic adversarial tests. Original eight static checks are
  retained; the obsolete blanket prohibition on deterministic helper scripts was
  replaced under explicit Owner authorization with stdlib/no-infrastructure
  import checks, not silently weakened.
- Fresh isolated sum-values fixture and four executable tests. It intentionally
  ignores operands after the first and has one genuine mandatory failure.
- Requirements traceability records implementation/static/dynamic layers and
  honestly leaves native rework/review/activation/package acceptance pending.

Manager developer review identified and requested refinements before handoff:
Worker output differs from input (input_candidate_ref echoes supplied input);
Tester/Reviewer remain bound to exact output; Tester must echo Manager-assigned
oracle_ref and cannot pass with failed mandatory checks; nested artifact identity
conflicts and invalid failed-acceptance references are rejected. Additional
negative tests prevent omission of known failed verification and require final
passing Planner check to follow Manager evidence acceptance. These were developer
review corrections, not fabricated independent failure/rework claims.

## Actual checks

| Command | Result |
|---|---|
| python3 -m unittest discover -s tests -v | Exit 0, 39 PASS: 8 existing static + 31 new contract tests |
| python3 -m unittest discover -s demo/receipt -v | Exit 0, 11 PASS |
| python3 -m unittest discover -s reports/demo/verification -v | Exit 0, 5 PASS |
| python3 -m unittest discover -s demo/csv-summary -v | Exit 0, 15 PASS |
| python3 -m unittest discover -s reports/csv-summary/verification -v | Exit 0, 6 PASS |
| python3 -m unittest discover -s demo/structured-flow -v | Exit 1, 4 executed / 1 mandatory failure, actual 2 instead of 4 |
| python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg | Exit 0, Total = Rp103,000 |
| python3 .agents/skills/council-flow/scripts/contracts.py policy .agents/skills/council-flow/policies/roles.yaml | Exit 0, restricted policy valid |
| git diff --check | Exit 0 |

Actual logs are adjacent in this worker directory. Thus all 45 prior checks
remain passing, plus 31 focused checks = 76 passing checks; the deliberately
incomplete fresh demo is separate and NOT passed. Earlier developer logs retain
the intermediate test coverage as it was added, not extra final test counts.
The old starter's expected failure was already recorded by Manager separately.
All test temp fixtures explicitly live inside the repository and clean up.

## Boundary and handoff

The initial pre-schema bootstrap messages remain unchanged. The early
interface-report.json was an in-progress interface announcement using a hash of
the then-current mutable helper; subsequent same-attempt refinements changed
that source. It is historical, not a current immutable accepted candidate or
fully causal validation claim. Final report candidate points to a new immutable
manifest, with actual initial demo bytes preserved in initial_sum_values.py.
Later fresh repair must use a new candidate artifact rather than mutate old
candidate evidence.

Actual fully validated live exchanges should begin with a real new Planner
plan.publish of the unchanged original plan (new message identity; null reply
permitted). Then use candidate_ref, not bootstrap candidate_id. Worker input may
be omitted for new creation; supplied repair input is echoed as
input_candidate_ref while candidate_ref identifies output. Tester assignments
require Manager-approved oracle_ref; report echoes exact candidate and strategy.
Use helpers described in communication.md, external native actor bindings and
ordered context. Structural validation cannot authenticate senders or enforce
native transport, permissions or OS isolation.

No final approval, real independent Tester, Reviewer, native activation result,
fresh Worker repair, ZIP or commit is claimed by this Worker. All Worker
mutations stop after terminal report. Independent T1 must report the actual fresh
demo failure; Manager then assigns a fresh Worker under unchanged criteria.
