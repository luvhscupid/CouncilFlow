# CouncilFlow hardening and verification

**MODEL:** NOT_DISCLOSED  
**REPOSITORY:** `E:\Saint\PROJECTS\CouncilFlow-main`  
**BRANCH:** `main` (tracked `origin/main`)  
**BASELINE:** `2d695a22a1bb596a527b0d118edc073d6d25553f` (`git ls-remote origin refs/heads/main` matched at final check)  
**RESULT:** PARTIAL

## Result

Confirmed contract, example, security-documentation, and release-distribution defects were corrected in the verified repository. The current package was built and independently checked after extraction. Current applicable suites passed, with one Windows privilege-dependent symlink test skipped. The original Planner's final check is **blocked** because live Gate 3 acceptance was not run and additional MCP fallback/stale-context and OS-boundary probes were unavailable or untested.

No commit, push, merge, external-repository change, frozen-spec edit, or `cf-recall` recreation occurred. The source edits and package remain uncommitted on `main`.

## Confirmed defects and corrections

- `contracts.py` rejected line breaks in frozen multiline acceptance text. A narrowly scoped plan-criterion validator now permits LF/CRLF while still rejecting tabs, NUL, DEL, and malformed CR controls. Regression coverage checks allowed and rejected cases.
- Operational Full Plan JSON examples were rejected by the active validator: `created_at` was obsolete, the assignment lacked required `instructions`, and the report used legacy fields and a fabricated digest. The examples now use the current contract and a real synthetic fixture digest. Tests cover root-bound success and stale-digest rejection; the Full Plan checksum list was updated.
- The contract helper's resolved-path check could be mistaken for a security boundary. `communication.md` now states the TOCTOU and Windows junction/reparse limitations and forbids using it as OS containment.
- `RELEASE.md` described a Round 6 archive absent from this checkout. It now labels Round 6 evidence historical and describes the current `dist/council-flow.zip` package. Existing historical reports were not rewritten.
- A004's Worker execution record had a conflicting top-level manifest hash. A005 corrected it in a fresh evidence attempt. A005's Tester report then omitted its selected command output reference at top level; Reviewer rejected that chain. A006 also retained that earlier failure in its context and was rejected. An initial Manager rework packet was likewise rejected because it lacked a preceding failed verification/Planner check. These failures were preserved. A clean Planner boundary M046 and A009 Workerâ€“Testerâ€“Reviewer chain validated; the final ordered sequence through Planner M055 passed.

## Changed files

Tracked source/doc changes:

- `.agents/skills/council-flow/scripts/contracts.py`
- `.agents/skills/council-flow/references/communication.md`
- `tests/test_contracts.py`
- `docs/CouncilFlow-Full-Plan/02-PROTOCOL-AND-POLICY.md`
- `docs/CouncilFlow-Full-Plan/examples/job.assign.json`
- `docs/CouncilFlow-Full-Plan/examples/job.report.json`
- `docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt` (new)
- `docs/CouncilFlow-Full-Plan/prompts/ONE-SHOT-CODEX-CLOUD.md`
- `docs/CouncilFlow-Full-Plan/SHA256SUMS.txt`
- `RELEASE.md`
- `dist/council-flow.zip` and `dist/council-flow.zip.sha256`

All detailed packet, test, review, package, and Planner evidence is under `reports/councilflow-hardening/`. Frozen Gate 3/Owner Charter/C3 files are unchanged. The deleted `cf-recall` component remains absent.

## Tests and verification

The independent A009 Tester ran these commands from the extracted package directory `reports/councilflow-hardening/tester-a009/relocated`, using `C:\Users\cupid\AppData\Local\Programs\Python\Python312\python.exe`:

| Command arguments | Result |
|---|---:|
| `-m unittest discover -s tests -v` | 83 tests: 82 passed, 1 skipped |
| `-m unittest discover -s demo/receipt -v` | 12 passed |
| `-m unittest discover -s demo/csv-summary -v` | 15 passed |
| `-m unittest discover -s demo/structured-flow -v` | 4 passed |
| `-m unittest discover -s reports/demo/verification -v` | 5 passed |
| `-m unittest discover -s reports/csv-summary/verification -v` | 6 passed |

Total: **125 tests; 124 passed, 1 skipped**. Windows denied symlink creation with `WinError 1314`; the skip is not evidence that symlink escapes are safe. Both operational JSON examples passed root-bound validation from the extracted package. The stale-digest negative control exited 1 as expected. All 20 Full Plan checksums matched.

The 118-entry package passed independent SHA-256/sibling-checksum, ZIP CRC, safe-path, required/excluded-content, and exact worktree-byte checks. Package SHA-256: `7f3a22fa27a374f2805f019d62488c98a7b68bf225dd535ad313ace077ec5384`.

Reviewer independently reran the Tester command `contracts.py message docs/CouncilFlow-Full-Plan/examples/job.report.json --root .` from the extracted package. Exit code was 0 and both normalized stdout hashes matched: `9c0e58ec75ef29742d82a29008db9dc6016e44ad3e316963d23533e5bb82b8bd`. The clean A009 plan/Worker/Tester/Reviewer and Planner sequence validated; evidence is in `reviewer-a009/` and `planner-final/`.

A004's historical restoration suites were also executed once and failed: `reports/restoration/verification/initial` had 3 errors of 8 and `final` had 2 errors of 7. The archived fixtures contain obsolete `created_at` fields; the initial run also hit Windows symlink privilege denial. These historical files were left unchanged and were not treated as current product-suite failures.

Codebase Memory MCP was available and bound to project `E-Saint-PROJECTS-CouncilFlow-main` at the exact repository root. The index was refreshed after implementation/package changes and reported ready with no parse errors. `docs/`, `dist/`, and generated report artifacts are excluded by index rules and were inspected directly. Forced stale-context and unavailable-MCP simulations were not run; fallback behavior has static instruction coverage only.

## Frozen Gate 3 and E1â€“E10

The frozen experiment was **not run**: no authentic Owner-saved fixture or experiment setup was supplied, and the host evidence available here did not expose successful skill activation or loaded TOML identity. P004 E1â€“E10 text matched the frozen sources; E4 used the approved C3 erratum. This is text fidelity, not live Gate 3 evidence.

| Criterion | Status | Reason |
|---|---|---|
| E1 | BLOCKED | No host-observed skill picker/direct activation record for the frozen procedure. |
| E2 | BLOCKED | No activated-skill trigger trial; native subagents in this mission were explicitly requested. |
| E3 | NOT RUN | Native Planner/Worker/Tester/Reviewer sessions were observed in this mission, outside the frozen experiment. |
| E4 | BLOCKED | Host did not expose the loaded custom-agent TOML identity. |
| E5 | NOT RUN | No Gate 3 Tester-thread observation; current Tester activity was a separate mission. |
| E6 | NOT RUN | Distinct role agents ran here, but not in the frozen experiment. |
| E7 | NOT RUN | No frozen-procedure Owner courier log was created. |
| E8 | NOT RUN | A separate Reviewer rerun matched, but it was not a Gate 3 outcome. |
| E9 | NOT RUN | No Owner-interface observations from the frozen experiment. |
| E10 | BLOCKED | Authentic Owner-saved criteria fixture was unavailable. |

## Final Planner map

The original P004 Planner check at `reports/councilflow-hardening/planner-final/plan-check.json` mapped all 15 criteria once: **HF-01, HF-02, HF-05 passed; HF-03 and HF-04 blocked; E1, E2, E4, E10 blocked; E3, E5â€“E9 unverified.** It did not change or weaken criteria.

## Unresolved risks, ranked

| Severity | Unresolved issue | Evidence / impact |
|---|---|---|
| High | Live native activation and Gate 3 outcomes remain unverified; E1/E2/E4/E10 are blocked. | Requires host-observed activation/configuration evidence and an authentic Owner fixture; prevents a full Gate 3 PASS. |
| Medium | The helper is not OS containment. Symlink execution was skipped; junction/reparse and TOCTOU behavior were not tested. | Do not use record-path validation to authorize attacker-controlled filesystem access. Native permissions/boundaries must enforce containment. |
| Medium | Codebase Memory stale-context and unavailable-MCP fallback behavior were not dynamically exercised. | MCP was available and fresh in this run; direct-inspection fallback has static instruction checks only. |
| Low | Historical archived restoration suites remain incompatible with the current contract. | Old fixtures use `created_at`; they remain unchanged as historical evidence. |

No Owner decision was needed for the completed local fixes or package. A future frozen Gate 3 run requires the authentic saved fixture and host capabilities to observe the invocation and loaded agent configuration.
