# Independent engineering review

Disposition: no open actionable findings in the scoped final source. This is direct maintenance review, not a CouncilFlow invocation, formal Gate 3 rerun, or retrospective change to historical E10 FAIL.

Reviewed candidate SHA-256: `77702c763e5eb0067fdad3dab3a91f66183d8075d5fdad8a95a29f38651a2a1a`. The complete release-source inventory plus GitHub workflow/newline configuration matches the independent Tester's final snapshot and remained unchanged through this review. `candidate-before.json` and `candidate-after.json` preserve the inventory.

## Findings and resolution

- Original raw Owner input is separately supplied before Planner through `original_source_ref`, with bounded deterministic ACn capture and caller-observed provenance. Required fidelity rejects a derivative alone. Ordered exact criterion content, source reference, and digest are checked at validation boundaries; the normal SKILL, workflow, communication, Planner instructions and README now require this path.
- Generated derivative source lineage must equal the separately pinned original. Original and derivative references cannot silently overwrite one artifact identity. Independent source-identity/lineage probes reject these substitutions.
- A second Worker assignment requires the preserved Manager rework decision; repair cannot bypass it by replying to a failed report. New attempts and fresh Worker identities are enforced against supplied ordered context. Existing complete original-Planner rework tests remain green.
- New integration tests cover a complete materialized source-bound final check, stale source on final revalidation, unmet mandatory final acceptance, real behavioral oracle failure despite weakened candidate tests, real deterministic-output mismatch, and an observed subprocess timeout. Synthetic packet actors are labelled as contract fixtures, never actual native role proof.
- The new source-fidelity reference requires pre-Worker pristine oracle snapshots, a bounded external Council handoff inventory, and honest correlated-error/provenance/runtime limitations. The runtime is not expanded into a security supervisor.
- Diff scope is targeted. Frozen specifications, historical reports, YAML policy and original root newline rules were not edited by the product change. The Windows CI change adds only the authorized recovery branch trigger. Parent separately owns package/frozen-preservation/checkout/remote verification.

## Independent executions

`run_review_verification.py` directly invoked the exact executable, arguments and working directory from the Tester's `readonly-command-declaration.json`; it verified the executable and input hashes first. It captured separate raw stdout/stderr without writing Tester evidence.

- Tester exit: 0. Reviewer exit: 0.
- Both stdout SHA-256 after CRLF-to-LF replacement only: `66efbe32da24299975ba2520b4d912958564888120a5e61c7992d33f7998d515`.
- Comparison: MATCH. This establishes repeatability for that command and those recorded inputs only.
- Reviewer-authored source controls: 8/8 passed, including original/derivative artifact-ID collision, matching altered internal plan/derivative, missing caller provenance, stale source, relabelled generated JSON, and same-bytes source-identity substitution.
- Inspected independent Tester evidence: six Windows suites, 166 run / 164 passed / 2 platform skips / 0 failures / 0 errors; 22 source controls; two protection mutations caught through named assertion failures, not import/setup errors; two real behavioral defects caught by preserved baseline oracles while weakened candidate tests passed.
- `git diff --check` executed successfully. Review execution did not alter product source.

Raw commands, argument text, exits, stdout/stderr artifacts, hashes, candidate and input references are preserved in `review-result.json`. Reviewer-owned scripts are rerunnable from the repository root using the recorded Python executable.

## Limits retained

Caller-observed provenance is an explicit trust input, not authentication or sealed storage. ACn text is the supported unambiguous input format; unsupported formats fail closed. Oracle execution, external handoff completeness and infrastructure retry accounting remain instruction-level responsibilities, with explicit unverifiable outcomes when evidence is unavailable. Distinct sessions do not prove diverse model weights, independent reasoning, effective custom-agent TOML loading, or formal E1/E2/E4. No formal Gate 3 result is certified here.

External reviewer findings in the Owner mission are pooled. No source supports attributing individual concerns to DeepSeek, Grok, Claude, Gemini, GLM, GPT High or the unidentified reviewer separately; the final report should preserve that attribution limit.
