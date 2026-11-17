# Slice 01 | Claude contract compatibility + release determinism

**Status:** READY TO DISPATCH; NOT RUN.  
**Baseline:** `3bf08cde1ae012d3bf6ef483015ca087bd8f420b`.  
**Scope:** AR-01 / AR-02 / AR-03 only. This is a repair slice, not an architecture redesign.

## Problem / inspection targets

1. Plugin `plugins/councilflow/agents/council-reviewer.md` calls for `execution_evidence` and `tester_execution_evidence` inside `independent_rerun`; the canonical validator's closed allowed-field list does not include them. Plugin Tester instructions mention `evidence_type: "output_file"`; this field is absent from the relevant schema. The role files also refer to `SAFETY-PREFLIGHT` without a clear common definition. Reproduce before changing.
2. `tests/test_claude_plugin.py` calls `builder.build()`; the builder currently writes `dist/councilflow-claude-plugin.zip` and checksum. GLM reported tests overwrote tracked artifacts.
3. GLM reported that a pristine rebuild does not byte-match the committed Claude plugin ZIP, even though its entries matched; investigate exact byte/entry-order differences independently.

Inspection paths: canonical `.agents/skills/council-flow/scripts/contracts.py`, plugin copy under `plugins/councilflow/skills/run/scripts/`, shared message contract, both Claude agent files, `tools/build_claude_plugin.py`, `tools/build_release.py`, relevant tests and package sidecars.

## Tasks

- Record clean starting SHA and worktree status. Preserve unrelated changes; isolate this run on a task branch.
- Construct minimum **valid-context** Claude Tester/Reviewer examples showing whether obeying current role files produces valid controlled packets. Verify negative/error paths too; distinguish instructional prose from a JSON field requirement.
- Choose the **smallest spec-compliant** correction: clarify Claude instructions where schema doesn't need extension, or make a narrow typed schema change only where controlling requirements demand it. Keep canonical and plugin copies synchronized and test both.
- Define the behavior of the `SAFETY-PREFLIGHT` reference or remove unsupported language without weakening safety rules.
- Refactor package-test invocation to write to temporary output locations or use another demonstrably non-mutating isolation technique.
- Compare pristine outputs of **both** package builders to committed ZIP bytes and sidecars. Explain differences (archive ordering, metadata, content, permissions, or otherwise). Fix reproducibility with intentional artifact updates only.
- Add regression tests detecting schema drift, build mutation, and committed-vs-rebuilt package disagreement.

## Acceptance gate

- [ ] Reproducing tests capture original defect(s) or explicitly falsify them.
- [ ] Claude Tester/Reviewer packets following approved instructions are valid in a correctly formed sequence.
- [ ] Unknown fields, fabricated evidence, broken causal order and weakened frozen criteria still fail closed.
- [ ] Canonical vs. Claude shared runtime drift check passes.
- [ ] Fresh checkout: full maintained offline suites pass and `git status --porcelain` stays unchanged after tests (other than documented intentional changes made before the test).
- [ ] Codex and Claude ZIPs and SHA-256 sidecars match fresh deterministic rebuilds from the same inputs.
- [ ] No frozen specifications, unrelated code, historical reports or host trust model are changed.

Suggested verification includes every maintained command from `RELEASE.md`, plugin drift/build checks, targeted negative tests, a clean-copy package rebuild, Git diff review and independent Tester/Reviewer checks **only if actual native delegation is available**. Do not report host activation on the basis of static tests.

## Stop / safety rules

Stop rather than silently introduce a new protocol layer, standalone runtime, external dependency, or different authority chain. No direct `main` changes; no push, PR or merge without separate Owner decision. Changes may be committed on a local task branch for review. If cloud delegation is unavailable, declare NATIVE_ACTIVATION_UNVERIFIED; never simulate a CouncilFlow session.

## Run record

- Status: NOT RUN
- Starting SHA / branch:
- Native host capability and role/session evidence:
- Reproductions (commands, expected/actual, log paths and SHA-256):
- Files changed:
- Tests and pristine package comparisons:
- Unresolved issues:
- Commit / push / PR / merge:
- Owner decision / next action:
