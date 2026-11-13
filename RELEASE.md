# CouncilFlow release

## Current-checkout release candidate

This section describes the package built from the current verified repository
worktree for the final release audit. The Round 6 statements and reports below are
historical evidence from earlier snapshots; they do not describe the current
checkout or prove that its archive is present.

Archive: `dist/council-flow.zip`. Its sibling SHA-256 file is
`dist/council-flow.zip.sha256`; `dist/council-flow.manifest.json` records every
entry's size and SHA-256. The package preserves repository-relative paths
and is built by `python tools/build_release.py` from an explicit allowlist. It includes the
complete `.claude/skills/council-flow/` skill and the four Claude Code agent Markdown files
under `.claude/agents/`, README, this release guide, demos, tests, the frozen
Gate 3 requirements, the Full Plan supporting documents, and demo verification
reports. Older mission and release reports remain in the checkout but are not
packaged as current verification evidence. It excludes `.git`, caches, bytecode, credentials, native
runtime state, temporary files, the archive itself, and the current hardening
evidence packet. The reproducible builder itself is included; it writes package
inventory and checksum records outside the archive to avoid self-inclusion.

Package verification for this run is recorded outside the archive in
`reports/councilflow-final-release-audit/`. The archive is checked for CRC
integrity, safe relative paths, required and excluded entries, and exact file
hashes against the worktree. It is extracted to a temporary directory for test
execution. Use `python -m zipfile -t dist/council-flow.zip` to check its ZIP
container and verify the sibling digest with SHA-256 before distribution.

Run all six current suites on the checkout and again from a fresh final extraction:

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s demo/receipt -v
python -m unittest discover -s demo/csv-summary -v
python -m unittest discover -s demo/structured-flow -v
python -m unittest discover -s reports/demo/verification -v
python -m unittest discover -s reports/csv-summary/verification -v
```

The starter demo is intentionally incomplete. Archived restoration tests use older
contract fixtures; their outcomes are historical and are reported separately from
these current suites. The prior E10 extraction check omitted CSV and the independent
demo suites; its old full-suite label is retained as historical coverage drift.
Current exact counts, platform skips, raw execution records, independent Reviewer
comparison, frozen-source hashes and final package digest live in the audit report.

This package is an installable source bundle; it does not establish successful
native `/council-flow` activation, custom-agent Markdown loading, or Gate 3 E1-E10
live outcomes. Those remain subject to host-observed evidence and the authentic
Owner fixture.

## Historical Round 6 correction package (retained)

The corrected release is built from the isolated copy at
`E:\Saint\PROJECTS\CouncilFlow-round6`. C1 changes the Reviewer to compare the
frozen plan, Worker candidate and Tester evidence, then independently rerun one
Tester-declared deterministic command. C2 removes `created_at` from new message
envelopes while keeping optional diagnostic timestamps with an explicit
provenance limitation. C3 is recorded as a separate erratum without rewriting
the frozen Gate 3 source or historical outcomes.

Engineering regression checks passed: 64 CouncilFlow tests plus 12 receipt
calculator application tests. The tests use synthetic contract fixtures and do
not demonstrate live native role behavior. Gate 3b is blocked because no
authentic clean pre-test revision/fixture can be recovered from this no-Git
workspace; the available receipt-calculator already has `--version`. The
historical E1–E10 record is retained in the checkout and excluded from this
installable archive.

The corrected distributable is `dist/council-flow-round6.zip`, with a sibling
SHA-256 file. This work did not install the skill into the
Owner's active repository.

The primary installable product is `.claude/skills/council-flow/`, with native
custom agents in `.claude/agents/`. Both are ordinary text files; no rebuild or
package installation is required. Current format references and runtime
observations live under `reports/environment/`.

### Historical verification limit

The communication restoration passed 103 independently executed tests,
separate experiential review and the original Planner's final check.
Fresh native discovery passed; documented explicit structured skill input was
accepted, then the actual native thread entered systemError with HTTP 401
authentication rejection. Successful invocation remains **UNVERIFIED**.

Real native agents executed the corrected JSON-boundary workflow, including
independent failures and fresh-Worker repairs. This does not prove successful
end-to-end `/council-flow` activation. Live custom-role-file selection also remains
unverified; native subagents received the documented role-instruction fallback.
Earlier restoration evidence, including `reports/final.md`, remains in the
checkout as historical context and is excluded from the installable archive.

The truthful release classification is
**CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED**. This build does not alter
authentication or require a new key, provider or subscription. It cannot claim
COUNCILFLOW_FULLY_VERIFIED while the actual activation result is blocked.

### Historical archive and installation

Archive: `dist/council-flow-round6.zip`. It preserves repository-relative `.agents/`
and `.codex/` paths. Source-controlled product, demonstration, tests, and selected
evidence are included. Generated native CLI state under `reports/runtime/`,
credential paths, bundled system assets, schema dumps, caches, `.git`, and the
archive itself are excluded. Repository reports written after packaging may
contain later release verification; the repository is the final evidence source.

Extract to an empty staging directory, then copy `.claude/skills/council-flow/`
and `.claude/agents/council-*.toml` into an authorized target repository after
checking for name collisions. Do not overwrite existing installations. Start
Claude Code at that target root and invoke `/council-flow <ordinary coding goal>`.
Neither the demo nor reports are runtime dependencies of the installed skill.

The distributable ZIP must include the complete skill and four agent Markdown files,
README, this release guide, the demonstration, validation tests, and evidence
reports. Do not package `.git`, Python caches, credentials, runtime state, or
unrelated projects. Use the standard `zip` tool or Python `zipfile`; this product
does not need a package manager merely to archive files.

Before labeling a release verified, run the static checks, actual discovery and
explicit `/council-flow` activation, the native role workflow, independent demo
tests and user interaction, final Planner check, and ZIP integrity check. Keep
failed baseline output and truthful UNVERIFIED results. Record the resulting
archive path and Git commit in the final Manager report. A correct ZIP alone does
not establish functional activation.

Install by extracting into another authorized repository, preserving any existing
files, or copy only `.claude/skills/council-flow/` and the four
`.claude/agents/council-*.toml` files. Run Claude Code from that repository and invoke:

```text
/council-flow Build the approved feature described below, with tests.
```

No global settings, sandbox policies, or credentials need to change. Optional
user-wide installation is documented in README for later use with ordinary
permissions. This build performs no global installation or external publication.

Host compatibility is evidence-specific: standalone `.claude/agents/*.toml`
syntax is based on current official documentation. An older/managed host may
support native delegation without loading custom-role files. The skill then
passes role instructions to native subagents and reports custom-role loading as
unverified. If native delegation or real activation cannot be observed, report
PARTIAL with the exact missing capability; never a simulated success.

### Historical communication-contract restoration

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
invocation and required real role sessions. The historical restoration results
remain in the checkout and are excluded from this archive; they do not describe
this candidate. Current archive verification is recorded in
`reports/restoration/package-verification.json`; the earlier numbered archive
snapshot and its extracted 103-test run remain immutable historical evidence.
