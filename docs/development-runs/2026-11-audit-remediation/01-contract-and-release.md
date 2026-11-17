# Slice 01 | Claude contract compatibility + release determinism

**Status:** ENGINEERING ACCEPTED BY OWNER; NATIVE WORKFLOW UNVERIFIED; MERGE AUTHORIZED.
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

- [x] Reproducing tests capture original defect(s) or explicitly falsify them.
- [x] Claude Tester/Reviewer packets following approved instructions are valid in a correctly formed sequence (schema and role-instruction regression coverage).
- [x] Unknown fields, fabricated evidence, broken causal order and weakened frozen criteria still fail closed (existing negative regression suite).
- [x] Canonical vs. Claude shared runtime drift check passes.
- [x] Full maintained offline suites pass; tests do not mutate tracked release artifacts (intentional package updates are documented below).
- [x] Codex and Claude ZIPs and SHA-256 sidecars match fresh isolated deterministic rebuilds from the same source inputs.
- [x] No frozen specifications, unrelated code, historical reports or host trust model are changed.

Suggested verification includes every maintained command from `RELEASE.md`, plugin drift/build checks, targeted negative tests, a clean-copy package rebuild, Git diff review and independent Tester/Reviewer checks **only if actual native delegation is available**. Do not report host activation on the basis of static tests.

## Stop / safety rules

Stop rather than silently introduce a new protocol layer, standalone runtime, external dependency, or different authority chain. No direct `main` changes; no push, PR or merge without separate Owner decision. Changes may be committed on a local task branch for review. If cloud delegation is unavailable, declare NATIVE_ACTIVATION_UNVERIFIED; never simulate a CouncilFlow session.

## Run record

- Status: ENGINEERING ACCEPTED BY OWNER; NATIVE_ACTIVATION_UNVERIFIED; merge authorized.
- Starting SHA / branch: `f4a6d8e8e1eee07620934bf74a6dac7639c5db96` / `task/slice-01-claude-contract-release`.
- Active host/session evidence: no verifiable native Planner/Tester/Reviewer session provenance was available. Engineering tests and independent shell verification below are not CouncilFlow role-workflow proof.
- Scope: AR-01, AR-02, AR-03 only.
- Reproductions:
  - Baseline Claude build from a pristine `git archive HEAD` snapshot: rebuilt SHA-256 `13a0116e563bcbc6ce00e8017698eddc0be054d5a349a2341a9b0d857cb1e31f`; committed ZIP SHA-256 `ba43a58e7ed25ca63767f6582bfec9353aaaf68e3be243dfbc9f79e2c87e8434`. Both contain the same 24 entry names, bytes and metadata, but the entry order differs, reproducing AR-03 as a byte mismatch.
  - AR-01: existing closed packet schema excludes the extra evidence fields the Claude Reviewer prose requested and excludes Tester `evidence_type`; role instructions now specify schema fields and supported safety constraints without claiming an undefined `SAFETY-PREFLIGHT` syntax. Regression tests pass.
  - AR-02: package tests build Claude archives in temporary directories; release artifact files remained unchanged through the test suites. The final suite run reported only the intentional tracked source/package changes.
- Final tests: `python -m unittest discover -s tests -v` PASS (241, 1 skipped); `python -m unittest discover -s demo/receipt -v` PASS (13); `python -m unittest discover -s demo/csv-summary -v` PASS (15); `python -m unittest discover -s demo/structured-flow -v` PASS (5); `python -m unittest discover -s demo/gate3-demo -v` PASS (9); `python -m unittest discover -s reports/demo/verification -v` PASS (5); `python -m unittest discover -s reports/csv-summary/verification -v` PASS (6); `python -m unittest tests.test_claude_plugin -v` PASS (20); `git diff --check` PASS. Seven maintained-suite counts total 294 tests, including 1 skipped (241 + 13 + 15 + 5 + 9 + 5 + 6).
- Isolated final package verification: from pristine source snapshots with the Slice 1 source patch applied, Codex archive and sidecar match exactly (ZIP SHA-256 `7c56ac117b8f260df8880b2ec90c5a014394225d84f2c33e0e9a07b1cda2533c`; sidecar SHA-256 `6e68dac7db535ff50d7c2065f8392ffc777ef039e37d1dfa4bb9c648ba592cd6`). Claude archive and sidecar match exactly (ZIP SHA-256 `8a6917786741ae5698f2f81d02640579b4c26549b11b926d7790c4269dd4a16a`; sidecar content `8a6917786741ae5698f2f81d02640579b4c26549b11b926d7790c4269dd4a16a  councilflow-claude-plugin.zip`).
- Intentional release artifact update: regenerated only `dist/councilflow-claude-plugin.zip` and its `.sha256` sidecar because packaged role instructions changed and the deterministic builder now emits the correct stable entry order. Codex archive and sidecar were not changed.
- Files changed: `plugins/councilflow/agents/council-reviewer.md`, `plugins/councilflow/agents/council-tester.md`, `tests/test_claude_plugin.py`, `tools/build_claude_plugin.py`, `dist/councilflow-claude-plugin.zip`, `dist/councilflow-claude-plugin.zip.sha256`, and this run record plus `README.md` roadmap index. Final review correction additionally changes only `tests/test_claude_plugin.py` and this run record.
- Additional final-review regressions: focused tests rebuild Codex and Claude packages in an isolated source copy and byte-compare both ZIPs and SHA-256 sidecars against committed artifacts, so stale packages fail. A focused Claude instruction check fails if unsupported `execution_evidence`, `tester_execution_evidence`, or `evidence_type` is directed as packet content. Sequential verification passed. An initial parallel run showed one transient targeted-suite failure; isolated and sequential reruns passed.
- Windows PR verification: initial pull-request Windows CI exposed a previously missed cross-platform ZIP ordering difference. The builder and regression tests were corrected to sort case-sensitively by relative path components, matching canonical POSIX ordering on Windows and Linux. [GitHub Actions run 44037466290](https://github.com/luvhscupid/CouncilFlow/actions/runs/44037466290) completed SUCCESS across checkout suites, release byte-for-byte rebuild, and extracted-install suites. The earlier failing CI attempts are retained in PR #3 history.
- Remaining issues: native CouncilFlow invocation and real native role-session provenance remain UNVERIFIED; no role evidence was fabricated. The previously observed transient parallel test failure is not independently root-caused; the maintained sequential verification and Windows CI completed successfully.
- Commit / push / PR / merge: final-review corrections committed and pushed to `task/slice-01-claude-contract-release`; no merge, PR or release.
- Owner decision / next action: Owner explicitly accepted Slice 1 engineering completion and authorized normal, non-force merge into main on 2026-11-17. PR #3 is the approved merge route. Slice 2 remains NOT AUTHORIZED and not started.
