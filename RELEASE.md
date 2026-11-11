# CouncilFlow release

The primary installable product is `.agents/skills/council-flow/`, with native
custom agents in `.codex/agents/`. Both are ordinary text files; no rebuild or
package installation is required. Current format references and runtime
observations live under `reports/environment/`.

## This build's verification limit

The communication restoration passed 103 independently executed tests,
separate experiential review and the original Planner's final check.
Fresh native discovery passed; documented explicit structured skill input was
accepted, then the actual native thread entered systemError with HTTP 401
authentication rejection. Successful invocation remains **UNVERIFIED**.

Real native agents executed the corrected JSON-boundary workflow, including
independent failures and fresh-Worker repairs. This does not prove successful
end-to-end `$council-flow` activation. Live custom-role-file selection also remains
unverified; native subagents received the documented role-instruction fallback.
See `reports/restoration/activation/`, `reports/restoration/manager.md`, and
`reports/final.md`. Earlier release reports are historical evidence.

The truthful release classification is
**CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED**. This build does not alter
authentication or require a new key, provider or subscription. It cannot claim
COUNCILFLOW_FULLY_VERIFIED while the actual activation result is blocked.

The integration correction updates the skill's JSON contracts and evidence
handling, four role TOMLs, deterministic validator tests, and the approved Gate 3
E4 erratum. E4 passes only with host-observed configuration identity or agent
type; a role label is insufficient. Insufficient host evidence is UNVERIFIED,
and evidence of a different/default configuration is FAIL. These source changes
do not resolve the existing native activation or custom-agent-loading gaps.

Run the repository suites and receipt regression from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v
```

These local checks establish contract, file and receipt behavior only. They do
not establish live skill activation, native role independence or E4 host identity.

## Archive and installation

Archive: `dist/council-flow.zip`. It preserves repository-relative `.agents/`
and `.codex/` paths. Source-controlled product, demonstration, tests, and selected
evidence are included. Generated native CLI state under `reports/runtime/`,
credential paths, bundled system assets, schema dumps, caches, `.git`, and the
archive itself are excluded. Repository reports written after packaging may
contain later release verification; the repository is the final evidence source.

Extract to an empty staging directory, then copy `.agents/skills/council-flow/`
and `.codex/agents/council-*.toml` into an authorized target repository after
checking for name collisions. Do not overwrite existing installations. Start
Codex at that target root and invoke `$council-flow <ordinary coding goal>`.
Neither the demo nor reports are runtime dependencies of the installed skill.

The distributable ZIP must include the complete skill and four agent TOMLs,
README, this release guide, the demonstration, validation tests, and evidence
reports. Do not package `.git`, Python caches, credentials, runtime state, or
unrelated projects. Use the standard `zip` tool or Python `zipfile`; this product
does not need a package manager merely to archive files.

Before labeling a release verified, run the static checks, actual discovery and
explicit `$council-flow` activation, the native role workflow, independent demo
tests and user interaction, final Planner check, and ZIP integrity check. Keep
failed baseline output and truthful UNVERIFIED results. Record the resulting
archive path and Git commit in the final Manager report. A correct ZIP alone does
not establish functional activation.

Install by extracting into another authorized repository, preserving any existing
files, or copy only `.agents/skills/council-flow/` and the four
`.codex/agents/council-*.toml` files. Run Codex from that repository and invoke:

```text
$council-flow Build the approved feature described below, with tests.
```

No global settings, sandbox policies, or credentials need to change. Optional
user-wide installation is documented in README for later use with ordinary
permissions. This build performs no global installation or external publication.

Host compatibility is evidence-specific: standalone `.codex/agents/*.toml`
syntax is based on current official documentation. An older/managed host may
support native delegation without loading custom-role files. The skill then
passes role instructions to native subagents and reports custom-role loading as
unverified. If native delegation or real activation cannot be observed, report
PARTIAL with the exact missing capability; never a simulated success.

## Communication-contract restoration

The Owner-authorized correction preserves the product and adds a small
standard-library validator inside the complete skill folder. Include:
SKILL.md, references/communication.md, references/message-contract.json,
policies/roles.yaml, scripts/contracts.py, all other references/metadata, and the
four compatible native TOMLs. Do not omit scripts or policy during installation.
No build step, parser dependency, service or key is needed.

Task packets are UTF-8 JSON; role/workflow policy is YAML; native configuration
remains TOML; optional diagnostics are bounded JSONL; Owner updates are prose.
YAML cannot grant permissions and the helper cannot authenticate native senders
or enforce opaque native transport. Ordered supplied context and externally known
actor bindings are necessary for causal/origin validation.

The previous static prohibition on any helper script was superseded by the
Owner's explicit deterministic-validation requirement. Its replacement checks
actual helper imports against the standard library and rejects database/network
infrastructure imports, preserving the original dependency intent.

Three infrastructure retries and two crash recoveries are instruction-only
policy; productive engineering rework has no fixed lifetime cap. No persistent
accounting or crash-safe ledger is claimed. The existing receipt/CSV applications
and historical evidence remain intact.

Fresh release checks must rerun old/new suites and the receipt, exercise actual
JSON role boundaries and mandatory rework, attempt supported native activation,
and inspect corrected ZIP bytes plus relocated installation. Native activation
failure must not be hidden by unit-test totals. Final classification:
CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED if correction passes while native
activation remains unverified; COUNCILFLOW_FULLY_VERIFIED only after genuine
invocation and required real role sessions. Current results belong in final.md
and requirements-traceability.md. Current archive verification is recorded in
`reports/restoration/package-verification.json`; the earlier numbered archive
snapshot and its extracted 103-test run remain immutable historical evidence.
