# CouncilFlow execution record

## Authority and baseline

- Owner authorized creation, demonstration, packaging, and commit in the connected CouncilFlow repository; Cloud override supersedes Windows paths.
- Authorized root: `/workspace/CouncilFlow`; initial commit `b618396` (`Initial commit`). Initial `git status --short` empty; initial tracked content was `README.md` (`# CouncilFlow`).
- Parent Manager: native session `/root`. Native child identifiers exposed by the collaboration tool are task paths, not UUIDs. No model overrides were requested; agents inherit session configuration.
- Environment: Codex Cloud, Python 3.12.14, `codex-cli 0.167.0-alpha.4`, standard `zip` available. No package installation required.
- Manager performs coordination, read-only inspection, command execution, and execution/release records. Application and validation code changes are delegated to Workers.
- No project dependency is taken on ACP, Execution Kernel, or Codex on Crack. No other project, existing installation, global configuration, ACL, or approval policy is modified.
- Provenance correction: during initial capability discovery, the Manager unnecessarily read an available cloud-hosted `execution-kernel` instruction resource. It was not adopted, copied, imported, or used as a CouncilFlow dependency; no filesystem installation or predecessor project was opened or modified. That unrelated instruction read should have been skipped under the Owner's boundary. V14 establishes dependency independence, not a claim that this read never occurred.

## Actual native delegations

| Native task identifier | Role | Assignment |
|---|---|---|
| `/root/format_research` | Read-only research | Verify current official formats and local CLI capabilities; record documentation evidence |
| `/root/product_planner` | Planner | Author immutable build contract CF-BUILD-001 before implementation; final build check later |
| `/root/skill_worker` | Worker W001 | Implement installable skill, definitions, checks, documentation, and deliberately incomplete demo starter; not the finished demo |

`CF-BUILD-001` revision 1 was accepted unchanged before Worker delegation. Full contract is recorded under `reports/contracts/`.

## Evidence rules

- A filesystem path or static Markdown check is not native discovery or invocation proof.
- Distinct native agent task identifiers establish separate sessions, not separate providers, model identity, or OS-enforced isolation.
- Static scenarios and live scenarios are reported separately; unsupported or unobserved behavior is UNVERIFIED.
- A required unverified capability prevents a COMPLETE disposition even if the application demonstration succeeds.
- Later entries and linked role reports record baseline failures, rework decisions, independent results, and final disposition.

## Discovery and activation observations

- Native executor `skills.list` returned an empty catalog before and after skill creation. This running Cloud session does not expose the newly created repository skill through that catalog.
- Installed native CLI app-server `skills/list` with `cwds: ["/workspace/CouncilFlow"]` and `forceReload: true` returned enabled `council-flow`, scope `repo`, correct SKILL.md path, metadata, and no errors: `reports/runtime/skills-list.json`. **Discovery PASS.**
- Containment: `bwrap --ro-bind / / --bind /workspace/CouncilFlow /workspace/CouncilFlow` succeeded. First CLI prompt render failed read-only because native CLI needs writable runtime state. A process-local mount of repository `reports/runtime/codex-home` onto the unchanged native Codex-home path allowed rendering and native discovery. No HOME/CODEX_HOME variable was reassigned; no global settings or installations were changed. Bundled system assets provisioned by this isolated CLI are runtime material, not product dependencies or release files.
- `codex debug prompt-input` accepted text `$council-flow`, but did not expand the explicitly-only skill. Rendering is not a passing invocation test.
- Initial isolated CLI `exec --ephemeral --json` had no auth and failed 401; this is not evidence that the active Cloud session lacks credentials.
- Native `codex login status` under a read-only filesystem reported `Logged in using ChatGPT`. For a second probe, native current-session auth was mounted read-only into the process-local runtime view, never copied or printed. The underlying repository auth target remained zero bytes. Native app-server `thread/start` created session `01a1c898-388a-75a2-806a-f8d4bfb65b21`; `turn/start` accepted literal `$council-flow` AND the documented structured skill item. It subsequently entered `systemError`; backend model refresh rejected the token (401), and optional app MCP startup failed (451). Accepted input is not successful invocation.
- A final materially different probe also mounted the existing native configuration read-only, preserving provider settings: native `exec` session `01a1c899-cd3e-7563-9c5a-588a44961c0c` failed with `Your access token could not be refreshed because you have since logged out or signed in to another account. Please sign in again.` Actual output: `reports/runtime/invocation-inherited-config.jsonl`. No further identical retries or login/configuration changes were attempted.
- **Successful explicit invocation remains UNVERIFIED/BLOCKED by standalone native CLI authentication.** The active conversation's collaboration tools remain functional. The following real multi-agent demo applies the packaged instructions manually in the parent session; it is not represented as a verified end-to-end explicitly invoked skill run. Final project disposition must therefore be PARTIAL even if the real demo passes.

## Baseline rejection and corrective assignment

- W001 `/root/skill_worker` stopped all implementation mutations after building the product and starter. Developer static checks: 8 passed. Starter baseline: 2 tests, 1 failure, exit 1; actual total Decimal('73000') instead of Decimal('103000'), retained in `reports/starter-failure.txt`.
- Manager explicitly **rejects** the mandatory receipt calculation failure. The intentionally incomplete starter remains preserved; it is not accepted as a finished application. A fresh demo Worker must implement the correction in `demo/receipt/` under the new immutable demo contract.
- Fresh native Planner `/root/demo_planner` assigned CF-DEMO-001 before final application implementation. Fresh independent build Tester `/root/build_tester` assigned skill inspection and independent reproduction of starter failure, with no repairs permitted.

## Real demo execution and Manager decision

Actual ordered sequence: `/root/demo_planner` → parent `/root` → fresh Worker `/root/demo_worker` (W002) → separate Tester `/root/demo_tester` → separate Reviewer `/root/demo_reviewer` → parent `/root` → Planner final check.

These are five distinct native role sessions: parent Manager plus four subagent roles. W001 `/root/skill_worker` was a different earlier Worker and did not implement the finished demo. Ancillary research, build testing, and boundary-probe agents are not substituted for the required demo roles.

- Immutable demo contract CF-DEMO-001 revision 1: `reports/contracts/demo.json`, SHA256 `88cb907ee1371763744fa7a14ad00830e1a383742baa2273b1c8814a1bd48891`; build contract digest remains `9f9acd446921eb92d54ded3de94ebdbdca735da17d90ec54d9966491402619ac`.
- W002 implemented `demo/receipt/receipt_calculator.py`, developer tests, usage instructions, and the accepted B-01 runtime-ignore repair. Its 11 developer tests and 8 static regressions passed. The initial mistyped fractional test expectation and independent integer-oracle correction remain recorded; no criterion was weakened. W002 stopped edits before independent testing.
- Independent Tester `/root/demo_tester`: 11 application tests PASS; 5 independently authored Fraction-oracle tests PASS; 8 static checks PASS. It verified 73 generated entries, numeric limits/low ambient precision, alternative and fractional receipts, 20 CLI error cases, and actual network-disabled sample execution. No implementation repairs requested. See `reports/demo/tester.md`.
- Independent Reviewer `/root/demo_reviewer`: actually exercised help, sample, alternative with quoted names, fractional/zero inputs, and three error paths. D08 PASS; no blocking usability findings or rework requested. See `reports/demo/reviewer.md` and seven command/output records.
- Build Tester boundary probe `/root/build_tester/boundary_probe` refused unauthorized external/global-policy changes and rejected silent Decimal/test weakening. This is observed instruction-level behavior, not OS-enforced isolation or successful skill activation.
- Manager accepts the independent technical and experiential results for the finished application; no further application repair is indicated. The preserved starter still intentionally fails and is not presented as a final-program regression.
- Native custom-agent-file selection was not available through this session's exposed collaboration interface. Real native subagents received role instructions, as the skill's documented fallback permits. TOML syntax/fields were independently checked; live custom-role selection remains UNVERIFIED.
- Manager's final product status remains PARTIAL because successful explicit invocation cannot be verified. The actual manual native-agent demonstration and discovery pass do not erase that blocker.
