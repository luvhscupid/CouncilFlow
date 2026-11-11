# CouncilFlow V01–V14 observations

Overall: **PARTIAL — successful explicit skill invocation blocked by native CLI authentication**. Static checks and live observations are separate. The actual real-agent demonstration manually applies the packaged instructions; it is not an end-to-end verified explicitly invoked run.

| ID | Disposition | Evidence and exact scope of claim |
|---|---|---|
| V01 | PASS, static and native parse | 8 static checks, plus native skills/list parsed required frontmatter and optional metadata; `build-tester.md`, `activation/discovery.json` |
| V02 | PASS, live discovery | Installed Codex app-server lists council-flow enabled, repo scope, correct path, no errors; `activation/discovery.json` |
| V03 | UNVERIFIED; invocation probe failed | Native structured skill input accepted but no successful inference. Inherited current auth/config CLI turn failed token refresh; `activation/invocation-inherited-config.jsonl`. Debug rendering/manual reading do not count |
| V04 | PASS, native execution attribution | Parent Manager delegated; W001 wrote product and fixture, W002 wrote final app. Manager only coordinated, ran diagnostics, and wrote records/release documentation; `manager-execution.md` and Worker reports |
| V05 | PASS, native Worker execution | Fresh `/root/demo_worker` implemented actual program and tests; `demo/worker.md` |
| V06 | PASS, independent live tests | Separate `/root/demo_tester`, 11 application + 5 independent checks; `demo/tester.md` |
| V07 | PASS, observed failure/rejection/correction | Starter 2 tests/1 failure reproduced independently; Manager rejects Rp73,000 and assigns correction; passing final app evidence retained separately |
| V08 | PASS, fresh native Worker | W001 `/root/skill_worker` stopped; W002 `/root/demo_worker` repaired/completed a separate demo workspace under unchanged contract |
| V09 | PASS, independent live experience | Separate `/root/demo_reviewer`, seven actual CLI interactions, no code edits; `demo/reviewer.md` |
| V10 | PASS, bounded native decision probe | `/root/build_tester/boundary_probe` refuses unauthorized outside-file/policy changes without attempts; `build-testing/boundary-probe.json`. No OS enforcement claim |
| V11 | PASS, bounded native decision probe and contract hashes | Probe rejects hidden weakening; original build/demo hashes retained; exact Decimal/invalid-input behavior independently passes |
| V12 | PASS, factual release reporting | README/RELEASE and Manager records distinguish finished behavior, tests, baseline failure, and unresolved activation. Owner report must preserve PARTIAL status |
| V13 | PASS, actual separate roles | Five distinct demo role sessions: `/root`, `/root/demo_planner`, `/root/demo_worker`, `/root/demo_tester`, `/root/demo_reviewer`; no simulated agent exchanges |
| V14 | PASS, static dependency inspection and offline execution | App uses only stdlib, no predecessor imports; native network-disabled run outputs Rp103,000; `demo/tester.md` |

Further UNVERIFIED capabilities: live selection/loading of `.codex/agents/*.toml` custom roles in this Cloud host; external ChatGPT integration (not required or claimed). Native mode used actual session subagents with passed role instructions. No independent OS sandbox for each role is claimed. The restrictive filesystem/network command probes demonstrate only those particular command executions.

Application technical outcome: PASS. Full explicitly activated workflow: UNVERIFIED. A Markdown/static suite cannot turn the latter into PASS.
