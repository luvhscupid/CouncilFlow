# CouncilFlow symlink repair and Gate 3 preflight

**Result:** the cross-platform test repair and local release checks are complete. **Gate 3 is NOT RUN and NOT READY**; readiness remains `BLOCKED_WITH_EXACT_PREREQUISITES`. This report is preparation evidence only and claims no Gate 3 E1–E10 outcomes.

## Checkout and change scope

- Repository root: `E:\Saint\PROJECTS\CouncilFlow-main`.
- Starting branch and HEAD: `main` at `9ba41ec06fecb8c1f78d9934295a62826f31baa4`, with expected parents `87271db` and `4b37907`. The initial tree had no staged or tracked edits, four pre-existing untracked paths, and ignored Python cache directories. The branch was already three commits ahead of `origin/main`; nothing was pushed.
- The four pre-existing untracked paths and ignored caches were preserved. The full status inventory captured during this run is [initial-current-git-status.txt](initial-current-git-status.txt).
- Source change is limited to `tests/test_contracts.py`. Production `artifact()` and frozen Gate 3 sources were not changed. Release outputs are `dist/council-flow.zip` and its sibling checksum. New logs and preparation evidence are under this run directory.

## Symlink test diagnosis and result

The original negative fixture made `parent/authorized/escape.txt` point to `parent/outside.txt`, then called `artifact(..., ROOT)`. The target was outside `authorized` but still inside the validator’s supplied repository `ROOT`; expecting a containment rejection was therefore incorrect. On this Windows host, the original test had been skipped before reaching that assertion because link creation raised `WinError 1314`.

The validator is an application-level check: it resolves `(Path(root) / path)`, checks whether the resolved target remains under `Path(root).resolve()`, then checks file existence and SHA-256. It is not an OS sandbox. I recreated the original fixture geometry on Linux with the released validator: its link target was still under the supplied `ROOT`, its digest matched, and `artifact()` accepted it; therefore the original `assertRaises` would fail on a symlink-capable platform. The control is captured in [original-fixture-control.json](integrity/original-fixture-control.json). The corrected test now supplies an isolated `authorized` root, a sibling target outside it, the root-relative POSIX path `escape.txt`, and the target’s correct SHA-256. It asserts the `artifact_path` containment error, ruling out a missing file or stale digest as the reason for rejection. A complementary test allows a digest-correct in-root symlink. Separate tests explicitly reject traversal and a wrong digest.

The independent Tester ran all six current suites on the Windows checkout and a fresh extraction of the content-addressed package. Each root ran 128 tests: 126 passed and two symlink-specific cases skipped because Windows returned `WinError 1314`. All twelve suite commands exited 0. The skips are not security passes. On WSL2 Ubuntu with Python 3.14.4, the four focused path/digest tests ran from a fresh Linux extraction of the same candidate: all four passed with zero skips, including allowed in-root and rejected out-of-root symlinks.

A separate Windows junction negative control also passed: a directory junction led from an isolated authorized root to a sibling outside target; with the correct target digest, the validator rejected it with `artifact_path: resolved path leaves authorized root`. This does not test race resistance or establish real OS isolation. **TOCTOU resistance and OS-level containment remain UNVERIFIED.**

The focused code change, exact commands, executable paths, working directories, exits, skip messages, and raw suite logs are recorded in [tester-result.json](tester/tester-result.json). Linux symlink logs and the Windows junction result are in [integrity](integrity/).

## Candidate and independent verification

The package was rebuilt from the existing explicit allowlist. The new archive has **118 entries** and SHA-256 `0eaa905e0a4c3d34468f6dcce85e83e280287e764133292cb9321ae762f9e9c4`. CRC, safe relative paths, required and excluded inventory, sibling checksum, and exact packaged file hashes against the checkout all passed. The package builder and captured inventory are in [release](release/).

Both operational JSON examples passed `contracts.py message <path> --root .` on the checkout and the extracted package. A deliberately stale digest exited 1 with `artifact_hash`. All 20 Full Plan checksums passed. The Charter, frozen Gate 3 v0.2 specification, and C3 erratum matched the three SHA-256 values in the checklist before and after verification. The independent Tester confirmed exact E1–E10 text fidelity, applying C3 only to E4; this is wording fidelity, not an E10 Owner-fixture comparison or a Gate 3 result.

The Reviewer independently reran the one deterministic command declared by the Tester against the same extraction, executable, arguments, candidate hash, and three input hashes. Both exits were 0. The Tester and Reviewer CRLF-to-LF-only normalized stdout SHA-256 values matched at `9c0e58ec75ef29742d82a29008db9dc6016e44ad3e316963d23533e5bb82b8bd`. Nested and top-level Tester command evidence references resolve to the captured bytes; Reviewer evidence records the same bindings and comparison. See [reviewer-summary.md](reviewer/reviewer-summary.md), [reviewer-result.json](reviewer/reviewer-result.json), and the raw Tester/Reviewer command outputs.

The independent archive audit found no retired standalone component path, source, skill, or configuration entry. Two literals (`recall.json` and `--label observed`) remain only as negative probes in `tests/test_codebase_memory_integration.py`, which asserts their absence from active surfaces; they do not define or implement the retired component. Historical Git text was not rewritten.

## Contract, Codebase Memory, and evidence-chain review

The corrected tests exposed no production contract defect. Existing coverage checks multiline frozen acceptance text, root-bound artifacts, externally supplied sender bindings, evidence references, attempt mismatches, and the selected Tester/Reviewer command evidence at top level. The three focused attempt/evidence regression tests passed in the Tester run. Current static Codebase Memory tests cover exact-root selection, direct source fallback for missing/unavailable/stale indexes, and graph-as-navigation guidance. Those static tests do not simulate a live unavailable or stale MCP server.

For this repair, Codebase Memory selected project `E-Saint-PROJECTS-CouncilFlow-main` with root exactly `E:/Saint/PROJECTS/CouncilFlow-main`. The post-Worker index status was ready and fresh; coverage reported no recorded issue for the four relied-on source files. Graph results were used for navigation only, with source read directly. The coverage API is explicitly best-effort, not proof of source completeness.

The existing evidence-chain risks remain follow-up items, not reasons to reopen accepted work: A005/A006 preserved records include missing or malformed evidence links; prior Planner closeout repeated when evidence bytes changed; and the earlier A014 Reviewer attempt did not match the final A013 Tester attempt. The current A013 Tester/Reviewer records match attempts, and current tests reject wrong attempts and missing top-level command evidence. Keep future evidence-cycle improvement separate; no communication protocol or automatic task-splitting changes were made.

## Read-only host preflight

`codex --version` reported `codex-cli 0.167.0-alpha.4.1`; `codex login status` reported `Logged in using ChatGPT`. No token or credential was read. The local `$council-flow` file and four project TOMLs exist, but the inspected host did not expose a skill picker/discovery result or effective loaded TOML identity. Canonical collaboration task names actually returned for this repair were `/root/planner`, `/root/worker`, `/root/tester`, and `/root/reviewer`; no separate host thread/session IDs were exposed. The executing model identity was not disclosed. These repair activities do not establish Gate 3 E1–E6.

The intended demo-only workspace remains at `reports/gate3-next/disposable-workspace`; its app and test fixture remain present and unfinished. The workspace contains 121 tracked files and is a separate directory copy, but it has no nested `.git`; `git -C` resolves to the parent repository. It is therefore not a Git or OS isolation boundary. The future session must keep all edits inside `demo/gate3-demo/app.py` and `demo/gate3-demo/test_app.py`, and host permissions remain those of the parent environment.

## Gate 3 capture matrix — preparation only

The frozen source is [02-GATE3-v0.2-FROZEN.md](../../docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md), with [C3](../../docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md) governing E4. Rows below use its check names and status/class rules. No row is a result from a Gate 3 run.

| Criterion and frozen requirement | Preparation status | Primary class | Required evidence class and current limitation |
|---|---|---|---|
| **E1 — Native discovery and invocation.** “Record separately (a) listing/picker visibility and (b) direct `$council-flow` selection. PASS requires host-observed successful native invocation. Missing picker entry alone does not invalidate working direct invocation.” | `BLOCKED` | `HOST_CAPABILITY_MISSING` | Required: `HOST-OBSERVED`. No Gate 3 invocation or picker observation was made or exposed. |
| **E2 — Native delegation trigger.** “PASS requires host-observed delegation attributable to the activated skill without an additional explicit spawning instruction. If invocation succeeds but host evidence positively shows non-delegation, FAIL (WORKFLOW_BEHAVIOR). If causation is not observable, UNVERIFIED. Alternative invocation wording requires a subsequent Owner decision, not an instruction added during this experiment.” | `BLOCKED` | `HOST_CAPABILITY_MISSING` | Required: `HOST-OBSERVED`. No frozen activation-trigger observation was performed. |
| **E3 — Actual spawns.** “Record host-observed subagent count, role/agent_type, and thread labels/IDs, without inventing identifiers. The required distinct-role observation is assessed together with E6.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: `HOST-OBSERVED`. Separate task names from this repair do not count as the frozen E3 observation. If a future E3 does not establish distinct native spawning, apply the frozen STOP rule and return evidence before implementation. |
| **E4 — Custom-agent loading (C3).** “PASS: Host-observed configuration identity or agent type confirms that the intended `council-*` custom-agent definitions were loaded for their corresponding role sessions. FAIL: Host evidence affirmatively demonstrates that a different or default agent configuration was used instead. UNVERIFIED: The host exposes only cosmetic thread labels or insufficient information to identify the actual loaded custom-agent definition.” | `BLOCKED` | `HOST_CAPABILITY_MISSING` | Required: `HOST-OBSERVED`. Local TOML files and role labels do not show effective loaded configuration; host telemetry was not exposed. |
| **E5 — Independent Tester command.** “Host evidence shows the Tester executed its commands in its own Tester thread, not merely a Worker report copied to Tester.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: `HOST-OBSERVED` Gate 3 Tester-thread execution. This repair’s Tester evidence is separate mission evidence. |
| **E6 — Distinct role threads.** “Host evidence shows Worker, Tester and Reviewer as three distinct threads. A single model adopting three role names is insufficient.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: `HOST-OBSERVED` three Gate 3 threads. No frozen observation exists. |
| **E7 — Zero Owner courier work.** “Count courier interventions after initial submission. PASS requires exactly zero. Courier work includes the Owner moving any message/output/file content from one agent to another, retyping instructions already available to agents, or being asked to carry data that another agent could hand over. Legitimate host permission prompts and explicit Planner/Manager Owner decisions are logged separately as AUTHORIZATION, not courier work. Evidence: OWNER-LOG and available interaction records.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: `OWNER-LOG` and available interaction records. No Gate 3 interaction log exists. Permission decisions remain authorization, not courier work. |
| **E8 — Reviewer verification rerun.** “The Tester identifies which of its commands are deterministic. Reviewer independently re-executes one deterministic Tester command and compares its exit code and SHA-256 of normalized stdout to the Tester-recorded result. Normalization must be documented, identical on both sides, and must not erase meaningful differences. Evidence must contain recorded commands, exit codes, normalized output hashes and the rerun comparison. No comparable deterministic command = `NOT_COMPARABLE` and E8 does not PASS.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: `RECORDED-EXECUTION` from the Gate 3 Tester and Reviewer. The repair’s deterministic replay is not an E8 observation. |
| **E9 — Plain-English Owner interface.** “Routine agent-generated Owner-directed communication comes only from Planner or Manager and uses plain English. Owner is not required to read, interpret, copy or relay raw inter-agent messages. Optional inspection of agent records does not violate E9. Host-generated permission dialogs and genuine explicit Owner decisions are separately permitted/logged.” | `UNVERIFIED` | `EVIDENCE_INSUFFICIENT` | Required: Gate 3 Owner interface and interaction records. No such observation exists. |
| **E10 — Frozen criteria fidelity.** “Planner reproduces the Owner's saved mandatory acceptance criteria verbatim. PASS requires a direct DIFF or equivalent byte-for-byte/line-preserving comparison against the saved fixture. Separately identifiable metadata such as IDs and traceability references may be added; criteria may not be paraphrased, omitted, weakened, or silently augmented.” | `BLOCKED` | `EVIDENCE_INSUFFICIENT` | Required: authentic `SAVED-ARTIFACT` fixture plus `DIFF`/byte-and-line comparison. No Owner-saved fixture exists; the draft below is not a substitute. |

These preparation labels do not count as Gate 3 outcomes. **Gate 3 is not ready to run.** The exact missing prerequisites are the Owner-saved fixture and a new authenticated local session whose host provides the required skill/delegation and effective-configuration evidence. If the host cannot expose required telemetry, record `UNVERIFIED` or `HOST_CAPABILITY_MISSING` as applicable; do not infer a PASS from role labels.

## Owner actions and exact proposed fixture

`reports/gate3-next/OWNER-TASK-DRAFT.txt` remains **NOT OWNER-APPROVED** (SHA-256 `229b6d26ca0e9e5f5e7d7b5a46a9bb0e304b904991c45bbd9abba86304fd3b72`). The Owner must review and accept it personally, then save the exact task text outside the installed skill as the authentic fixture. Its existing two criteria are:

1. Given a CSV containing a numeric `amount` column with values 2 and 3, selecting `amount` prints `5` and exits successfully.
2. A missing column or a nonnumeric value exits nonzero and reports a clear error without a traceback.

For the separate experiment, start a **new authenticated local Codex session** with `reports/gate3-next/disposable-workspace` as its workspace root. Submit one initial instruction consisting only of `$council-flow` followed by the verbatim Owner-saved fixture text:

```text
$council-flow [paste the exact Owner-saved fixture text here]
```

Do not paste `SKILL.md` or request subagent spawning. After submission, the Owner performs zero courier interventions; genuine permission approvals and explicit decisions are authorization, not courier work. Record host-observed evidence as required by the frozen spec. If E3 does not establish distinct spawned subagents, stop, return the evidence, and do not auto-patch or force delegation. No planted-bug run or Snapshot Vault AC07/AC12 work is authorized by this preflight.

## Evidence index

- [Integrity and frozen-source checks](integrity/before_checks.json)
- [Package build inventory and hash](release/build-package.stdout.json)
- [Independent Tester execution, logs, and evidence references](tester/tester-result.json)
- [Independent Reviewer replay and comparison](reviewer/reviewer-result.json)
- [Read-only host capability observations](host-preflight.json)
- [Starting checkout identity](starting-state.json)
- [Captured Git status inventory](initial-current-git-status.txt)
- [Hash manifest for this run's evidence files](evidence-manifest.json) (the manifest excludes its own bytes)

No Gate 3 experiment was started. No `NATIVE_ROLE_WORKFLOW_OBSERVED` or `COUNCILFLOW_FULLY_VERIFIED` claim is made.
