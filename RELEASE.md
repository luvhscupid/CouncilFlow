# CouncilFlow release

The primary installable product is `.agents/skills/council-flow/`, with native
custom agents in `.codex/agents/`. Both are ordinary text files; no rebuild or
package installation is required. Current format references and runtime
observations live under `reports/environment/`.

## This build's verification limit

Native Codex app-server discovery succeeded. Successful explicit invocation is
**UNVERIFIED**: the documented structured skill input was accepted, but the
separate CLI could not complete inference because its existing authentication
token could not be refreshed. The active Cloud session's native collaboration
tools did run the actual Planner/Worker/Tester/Reviewer workflow by manually
applying the packaged instructions. That demonstration is not claimed as a
successful end-to-end `$council-flow` invocation. Custom-role-file selection is
also unverified; native subagents received the corresponding role instructions.
See `reports/activation/`, `reports/manager-execution.md`, and final role reports.

Release disposition remains **PARTIAL**, not COMPLETE. An already authenticated
compatible Codex host can install the files and use the documented invocation;
this build does not modify authentication or require a new key or subscription.

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
