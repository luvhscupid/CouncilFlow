# Structured communication

CouncilFlow 1.0 defines **UTF-8 JSON** task packets for the Planner, Manager, Worker,
Tester and Reviewer. The role and workflow source is the
[versioned YAML policy](../../.agents/skills/council-flow/policies/roles.yaml). Codex-native
agents remain TOML. Optional bounded JSONL is for diagnostics only. Owner progress and
results stay in plain language.

The full contract is in the installed skill:
[communication reference](../../.agents/skills/council-flow/references/communication.md),
with exact payloads, causal, candidate and origin checks, limits and examples.

## Validator commands

The installed helper is `contracts.py`. It uses only the standard library:

```sh
python3 .agents/skills/council-flow/scripts/contracts.py message packet.json --root .
python3 .agents/skills/council-flow/scripts/contracts.py sequence plan-packet.json assignment.json report.json --root . --bindings observed-bindings.json
python3 .agents/skills/council-flow/scripts/contracts.py policy .agents/skills/council-flow/policies/roles.yaml
python3 .agents/skills/council-flow/scripts/contracts.py events events.jsonl --root .
python3 -m unittest discover -s tests -v
```

## What the checks do

- Sequence context and externally observed actor bindings are not copied from self-asserted
  sender labels.
- A Worker's output may differ from its assigned input. A Tester and a Reviewer must verify the
  exact output.
- The Reviewer compares the original criteria and the Tester's evidence, then reruns one declared
  deterministic command.
- The Manager assigns the test strategy. A Tester cannot self-approve or substitute its oracle.
- For a Tester assignment, `oracle_ref` is **required**, and the report must echo it exactly. The
  general optional-reference wording applies to other assignments and does not waive this.

## What the checks do not do

These are controlled-file checks. They are not authentication, transport enforcement,
permissions, a database or an agent engine. The policy uses a restricted, documented YAML subset
and does not install a parser. When installing the skill elsewhere, copy the product source and
all subfolders of the skill together.

## Related

- [Requirements traceability](https://github.com/luvhscupid/CouncilFlow/blob/9c59bc3d0f98a818b01ad14d0165d92b236105b0/reports/requirements-traceability.md)
- [Documentation index](README.md)
