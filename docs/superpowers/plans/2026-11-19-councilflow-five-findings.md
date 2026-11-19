# CouncilFlow Five-Finding Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the five audit findings, preserve CouncilFlow's approved role workflow, and produce a release package that matches and is verified against the final Codex-native source.

**Architecture:** Keep CouncilFlow as a Codex-native workflow skill. Repair the existing packet-to-dashboard path and bound its optional browser folder reader; reconcile current-facing documentation and automated checks; then rebuild and verify the allowlisted ZIP from the resulting source. Preserve the failed dashboard attempt and frozen Gate 3 records as evidence.

**Tech Stack:** Python standard library, UTF-8 JSON, plain HTML/CSS/JavaScript, Node.js built-in test runner, GitHub Actions on Windows.

**Spec:** `AGENTS.md`; `.agents/skills/council-flow/SKILL.md`; `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`; dashboard Owner request and original acceptance in `.councilflow/runs/cfdash-live-20261119/`.

## Global Constraints

- CouncilFlow is an installable workflow skill; the current implementation is Codex-native. Claude Code support is a possible extension, not a verified existing feature.
- Preserve the approved order: Owner → Planner → Manager → Worker → Tester → Reviewer → Manager → Planner → Owner.
- Manager coordinates and does not implement application code. Reviewer compares the frozen plan, Worker candidate and Tester evidence, then independently reruns one Tester-declared deterministic command; Reviewer is not a UX scorer.
- Keep the original `LIVE-01` through `LIVE-04` criteria and all failed-attempt evidence unchanged. Rework uses a fresh Worker and attempt; do not rewrite packets to manufacture a passing history.
- Frozen Gate 3 records and role policies retain their authority. Do not change or relabel them as current runtime proof.
- Packet validation does not authenticate senders, enforce opaque native transport, or provide OS isolation. Preserve the documented limits and use host-observed evidence for execution claims.
- Keep the dashboard read-only. Do not add a server, daemon, filesystem watcher service, broker, supervisor, provider, external action, or new asset.
- Preserve the current dashboard visual direction. Any changed status/error UI must remain keyboard accessible, visibly focused, readable, responsive, and compatible with reduced-motion preferences; do not add a visual redesign or asset.
- Preserve unrelated working-tree changes. Do not commit, push, publish, or install globally as part of this plan.

## Review Focus

- **Malformed or stale dashboard packets:** malformed JSON, unknown fields, mismatched packet/test-input hashes, or mixed attempts must be shown as incomplete and must never produce a passing acceptance display. Pin in Task 2.
- **Host-blocked browser launch:** local-file browser behavior that cannot be observed remains `BLOCKED` or `UNVERIFIED`; it must not be inferred from HTML inspection. Pin in Task 2.
- **Large or deeply nested selected folders:** exceeding a read limit must stop traversal and show an accessible issue, never silently show partial data as complete. Pin in Task 3.
- **Slow folder refresh:** a second refresh must not overlap an in-progress scan or multiply memory use. Pin in Task 3.
- **Stale release inputs:** a checksum-valid ZIP that omits current skill files or lacks matching extraction evidence must not be labeled current or verified. Pin in Task 5.

---

### Task 1: Reconcile Current Host-Support Claims

**Finding addressed:** Current documentation presents Claude Code as a supported, verified package, while the controlling project contract says it is only a possible, unverified extension.

**Files:**
- Modify: `README.md`
- Modify: `docs/technical/host-packages.md`
- Modify: `docs/research/README.md`
- Modify: `RELEASE.md`
- Test: `tests/test_skill_files.py`
- Preserve: `plugins/councilflow/`, `dist/councilflow-claude-plugin.zip`, and historical smoke-test records unless a separate Owner decision changes their status or distribution.

**Interfaces:**
- Consumes: the Codex-native scope statement in `AGENTS.md` and recorded historical Claude smoke evidence.
- Produces: consistent current-facing language that identifies Codex as the current implementation and any Claude artifacts/results as historical or prospective, without erasing their provenance.

- [ ] Add `test_current_host_claims_match_project_contract` to `tests/test_skill_files.py`. Assert that the current README, host-package page, and research index do not call Claude Code a currently supported or verified feature.
- [ ] Run `python -m unittest discover -s tests -p test_skill_files.py -v` and confirm the new assertion fails against the current conflicting claims.
- [ ] Update the three current-facing documents to match `AGENTS.md`; retain one-run historical evidence with its scope and limits, and do not describe the historical plugin ZIP as a current supported release. Task 4 updates the separate release-guide test matrix after this host-status edit.
- [ ] Rerun `python -m unittest discover -s tests -p test_skill_files.py -v` and confirm it passes.
- [ ] Check that the edits do not alter plugin source, frozen Gate 3 records, or historical outcome files.

### Task 2: Complete or Truthfully Block the Dashboard Acceptance

**Finding addressed:** The saved attempt-02 Manager decision rejects the candidate, and the Planner final check reports `LIVE-02` failed and `LIVE-01` unverified.

**Files:**
- Modify as evidence requires: `.agents/skills/council-flow/scripts/dashboard.py`
- Modify as evidence requires: `.agents/skills/council-flow/dashboard/run-reader.js`
- Modify as evidence requires: `.agents/skills/council-flow/dashboard/app.js`
- Test: `demo/dashboard/tests/test_publisher.py`
- Test: `demo/dashboard/tests/run-reader.test.cjs`
- Preserve unchanged: `.councilflow/runs/cfdash-live-20261119/plan.json`, all attempt-01/02 packets, reports, candidates, and evidence.

**Interfaces:**
- Consumes: the original Owner request, the existing `LIVE-01` through `LIVE-04` criteria, and the current CouncilFlow 1.0 packet validator.
- Produces: a new candidate attempt that either satisfies every original criterion with evidence or records the precise remaining blocker. It does not replace or edit attempt-02 history.

- [ ] Add focused regression cases for the recorded sequence error and stale input hash. The current snapshot must mark those packets incomplete, name the offending file/field, and never promote the run to a complete acceptance chain.
- [ ] Run `python -m unittest discover -s demo/dashboard/tests -p test_publisher.py -v` and `node --test demo/dashboard/tests/run-reader.test.cjs`; confirm the new failure reproduces before the repair.
- [ ] Diagnose the current attempt-02 candidate against its preserved report/evidence. Correct the packet-to-view defect at its source; do not suppress validator errors, alter acceptance IDs, or rewrite old reports.
- [ ] Start a fresh attempt using the original `LIVE-01` through `LIVE-04` criteria. Recheck partial, malformed, complete, and distinct-task packet states against the exact candidate.
- [ ] Observe the generated HTML opening and updating in the supported host browser. If local-file access is blocked, preserve the browser limitation and leave `LIVE-01` `BLOCKED` or `UNVERIFIED`; do not infer a pass from source or a publisher test.
- [ ] Run the two focused commands again and record exact executable paths, arguments, working directory, candidate/input hashes, exit codes, and CRLF-to-LF-only normalized stdout hashes for Tester and Reviewer evidence.

### Task 3: Bound Optional Folder Import and Refresh Work

**Finding addressed:** The user-selected directory reader recursively loads all JSON files and repeats the scan every two seconds without bounds or an overlap guard.

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/app.js`
- Test: `demo/dashboard/tests/auto-connection.test.cjs`

**Interfaces:**
- Consumes: the current folder-picker and manual-import flows.
- Produces: bounded user-selected folder behavior with visible, accessible errors; no changes to packet schemas, publisher behavior, or generated-snapshot semantics.

- [ ] Add tests for an oversized file, more than 1,024 JSON files, a directory depth above 16, aggregate JSON bytes above 16 MiB, and a refresh requested while another scan is active. Each case must stop or defer work and show the run as incomplete.
- [ ] Run `node --test demo/dashboard/tests/auto-connection.test.cjs` and confirm the new tests fail before implementation.
- [ ] Add shared limits: 65,536 bytes per JSON file, 1,024 JSON files, depth 16, and 16 MiB aggregate JSON input. Check file size before reading and hashing; stop traversal when a limit is exceeded.
- [ ] Add a single-flight refresh guard so interval ticks cannot overlap a running directory scan. Keep the pause/resume control and manual file import functional.
- [ ] Render limit and access errors through the existing accessible status/alert region. Do not claim a complete record after any file is skipped or a limit is reached.
- [ ] Rerun `node --test demo/dashboard/tests/auto-connection.test.cjs` and confirm all limit, overlap, pause/resume, and manual-import cases pass.

### Task 4: Synchronize Dashboard Status, Release Instructions, and CI Coverage

**Finding addressed:** Technical/readiness docs still say no dashboard exists, and the release/CI suite lists differ while the new dashboard tests are omitted.

**Files:**
- Modify: `docs/technical/multi-agent-evolution.md`
- Add dated status note, preserving the earlier snapshot: `reports/multi-agent-evolution-readiness-2026-11-19.md`
- Modify: `RELEASE.md`
- Modify: `.github/workflows/verify-portable-release.yml`
- Test: `tests/test_release.py`

**Interfaces:**
- Consumes: the accepted or blocked dashboard outcome from Task 2 and the exact test commands established in Tasks 2–3.
- Produces: aligned current status and one checkout/extraction test matrix for the release.

- [ ] Add `test_release_and_ci_cover_the_documented_suites` in `tests/test_release.py`, checking that the release guide and Windows workflow include `demo/gate3-demo`, the Python dashboard publisher suite, and both Node dashboard suites.
- [ ] Run `python -m unittest discover -s tests -p test_release.py -v` and confirm the new matrix check fails against the current six-suite workflow.
- [ ] Update `docs/technical/multi-agent-evolution.md` to describe the current local dashboard accurately, including its read-only limits and the dashboard task's recorded acceptance status. Add a dated note to the readiness report instead of rewriting its earlier point-in-time P5 statement.
- [ ] Update `RELEASE.md` to list the complete checkout and extracted-package commands: the existing seven suites plus `python -m unittest discover -s demo/dashboard/tests -v` and `node --test demo/dashboard/tests/run-reader.test.cjs demo/dashboard/tests/auto-connection.test.cjs`.
- [ ] Update the Windows workflow to run the same nine commands both in checkout and from the extracted ZIP. Set up Node 22 explicitly for the Node test step; keep the release workflow Windows-only unless a separate platform scope is approved.
- [ ] Rerun `python -m unittest discover -s tests -p test_release.py -v` and confirm the documentation/CI matrix check passes.

### Task 5: Rebuild and Verify the Exact Current Release Candidate

**Finding addressed:** The current 182-entry ZIP has a matching sidecar/manifest but omits dashboard paths and has no verification record for its current digest.

**Files:**
- Regenerate: `dist/council-flow.zip`
- Regenerate: `dist/council-flow.zip.sha256`
- Regenerate: `dist/council-flow.manifest.json`
- Add or update: `reports/` verification record for the exact final archive hash and clean-extraction results.
- Verify: `tools/build_release.py`, `tests/test_release.py`, `.github/workflows/verify-portable-release.yml`

**Interfaces:**
- Consumes: final source and documentation from Tasks 1–4.
- Produces: a reproducible ZIP containing the complete current Codex skill/dashboard and a verification record bound to the final ZIP digest.

- [ ] Extend `tests/test_release.py` with `test_current_release_contains_dashboard_sources_and_tests`; assert the archive includes `scripts/dashboard.py`, all four dashboard assets, and `demo/dashboard/tests/`.
- [ ] Run `python -m unittest discover -s tests -p test_release.py -v` and confirm the package-content assertion fails before rebuilding the ZIP.
- [ ] Build with `python tools/build_release.py`; confirm the ZIP, sidecar, and manifest all report the same SHA-256 and entry inventory.
- [ ] Check the container with `python -m zipfile -t dist/council-flow.zip`; extract to a fresh temporary directory and run all nine commands from `RELEASE.md` there.
- [ ] Rebuild once more and compare ZIP bytes and manifest entries with the first build. Record the exact digest, entry count, commands, exits, skipped tests, and clean-extraction result in the verification report.
- [ ] Do not claim successful native `$council-flow` activation, universal host support, or dashboard browser behavior unless the relevant host-observed evidence exists. Do not release or publish the package as part of this plan.

## Completion Criteria

- Current-facing host-support claims match the controlling Codex-native contract; historical plugin and smoke records retain their provenance.
- The dashboard's original acceptance is either independently accepted from a fresh attempt or left explicitly blocked/unverified with exact evidence; attempt-02 remains unchanged.
- Directory import is bounded and single-flight, and limit failures cannot appear complete.
- Current docs and Windows CI list the same nine test commands, including the Gate 3 demo and dashboard suites.
- The final ZIP includes the current skill/dashboard source; its sidecar and manifest match; clean-extraction tests and reproducibility checks are recorded against that exact digest.
- Gate 3 Run 01 remains `NATIVE_ROLE_WORKFLOW_PARTIAL` with E1/E2/E4 `UNVERIFIED`; no stronger native activation status is claimed.
