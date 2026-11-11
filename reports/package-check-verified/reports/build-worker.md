# Worker W001 — installable skill and starter fixture

- Type: `WorkerResult`
- Task: `CF-BUILD-001`, revision 1
- Native role/session identifier exposed by host: `/root/skill_worker`
- Objective: implement the repository-scoped skill, documented role files,
  installation instructions, compact static validation, and a genuinely broken
  starter; leave final application implementation to a fresh demo Worker.
- Scope: `/workspace/CouncilFlow/**`; no global configuration or other project
  files changed; no installation, network runtime, permissions change, ZIP, or
  commit performed by this Worker.
- Implementation status: `BUILD_ARTIFACTS_READY`
- Final disposition: `PENDING_INDEPENDENT_VERIFICATION`; Worker does not approve.

## Implemented files

- `.agents/skills/council-flow/SKILL.md`
- `.agents/skills/council-flow/references/{roles,workflow,acceptance,recovery}.md`
- `.agents/skills/council-flow/agents/openai.yaml`
- `.codex/agents/council-{planner,worker,tester,reviewer}.toml`
- `.gitignore`, `README.md`, `RELEASE.md`
- `demo/README.md`, `demo/starter/receipt_calculator.py`,
  `demo/starter/test_receipt_calculator.py`
- `tests/test_skill_files.py`, `tests/validation_cases.json`
- This report and the three command-output reports linked below.

## Actual developer-side checks

| Command | Exit | Observed result | Evidence |
| --- | --- | --- | --- |
| `python3 -m unittest discover -s tests -v` | 0 | 8 tests, all pass; static only | `reports/build-static-tests.txt` |
| `python3 -m unittest discover -s demo/starter -p 'test_*.py' -v` | 1 | 2 tests, 1 failure; quantity is ignored so total is 73000 rather than 103000 | `reports/starter-failure.txt` |
| `python3 demo/starter/receipt_calculator.py` | 0 | Valid executable fixture prints incorrect rice line total and `Total = Rp73,000` | `reports/starter-output.txt` |

An initial developer static check failed because the literal invocation appeared
in frontmatter but not the skill body. The Worker added the explicit invocation
to the body and reran all eight static checks successfully. This was a
developer-side correction before independent verification, not a claimed fresh
Worker rework demonstration.

The retained starter failure is intentional and meaningful. It is **not** a
passing finished application: the Manager must reject it for final acceptance
and assign completion to a fresh Worker. The fixture also lacks full input
validation and a true multi-entry input interface; these remain demo work.

## Evidence limits and open findings

- No finished receipt application exists from this Worker.
- Static tests validate the actual generated files and instruction coverage;
  they do not establish native discovery, explicit invocation, delegation,
  independent role behavior, or runtime adversarial compliance.
- The Manager is independently testing native discovery/invocation. This Worker
  makes no activation success claim.
- Current official formats were supplied through `reports/environment/`; TOML
  parses with stdlib `tomllib` and avoids model pinning or invented fields.
- Final Tester, Reviewer, Planner acceptance, archive, and commit remain pending.
- No mandatory requirement was changed. Repair decisions and final acceptance
  belong to the Manager after independent evidence.
