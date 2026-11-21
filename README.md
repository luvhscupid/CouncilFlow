# CouncilFlow

CouncilFlow is an installable **Codex-native workflow skill**. It is
not a standalone AI application, assistant, runtime, provider, or service.

## What it is

When you ask for a coding change, CouncilFlow organizes the work into roles, so the
change is planned, implemented, tested and reviewed by separate steps:

- a **Planner** writes the acceptance criteria,
- the **Manager** (the main session) hands implementation to a fresh **Worker**,
- a separate **Tester** and **Reviewer** check the result independently,
- the Planner makes a final check against the original criteria.

Only the Manager reports progress and results to you, the Owner. These roles are
workflow responsibilities carried out with the host's own models, tools,
permissions and native agent delegation. They are not independent servers or
processes.

CouncilFlow does not replace Codex, Claude Code, or their native delegation. It may be
packaged as a plugin where the host supports plugins.

## Why it exists

Coding agents are easy to over-trust. CouncilFlow keeps acceptance criteria separate
from the implementation, requires independent verification, and records every step
as structured evidence, so a claimed result can be checked.

## Start here

| If you want to... | Read |
| --- | --- |
| Install and use it in Codex | [Use in this repository](#use-in-this-repository-codex) below |
| Understand the internal message format | [Structured communication](docs/technical/structured-communication.md) |
| Try a small, offline example | [Demonstrations](#demonstrations) below |
| Understand the optional efficiency helpers | [Optional efficiency helpers](docs/technical/efficiency-helpers.md) |
| Find every technical document and its authority | [Documentation index](docs/technical/README.md) |
| Check release contents and verification commands | [RELEASE.md](RELEASE.md) |

## Authority and status

The [Gate 3 Owner Charter](docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md),
existing Owner decisions, frozen specifications and role policies keep their authority.
This page clarifies identity only. It does not simplify or change the approved
architecture. [Research proposals](docs/research/README.md) are non-normative and do not
authorize implementation or experiments on their own.

This Git repository contains the current source, regression tests, and the installable
`dist/council-flow.zip` release candidate. Current host evidence and historical archive navigation are indexed in
[reports/README.md](reports/README.md). Earlier integration and audit records
remain historical in the verified local archive.
Round 6 and Gate 3b reports describe earlier workspaces and are kept unchanged, so they
do not show how this checkout is activated or configured. Software release verification is
separate from the frozen Gate 3 experiment, and no new Gate 3 experiment is included.

## Host packages

| Host | Package | How to invoke | Status |
| --- | --- | --- | --- |
| Codex | `.agents/skills/council-flow/` and `.codex/agents/*.toml` (`dist/council-flow.zip`) | `$council-flow <goal>` | Supported native skill and role workflow. Run 01: **NATIVE_ROLE_WORKFLOW_PARTIAL**; E1/E2/E4 UNVERIFIED, other seven checks PASS |

See the [Gate 3 Run 01 summary](reports/documentation-release-sync/gate3-run-01.md).
Historical Claude Code work is documented in [Host packages](docs/technical/host-packages.md).
Claude Code remains a possible extension. The historical calc-001 smoke run applies to its recorded candidate.
Agent Efficiency helpers are offline-tested and opt-in; live adapter and billing compatibility
remain unverified. Package D remains **DRAFT_NOT_AUTHORIZED**.

## Use in this repository (Codex)

1. Open Codex at this repository root.
2. The skill is `.agents/skills/council-flow/SKILL.md`. Custom agent definitions are in
   `.codex/agents/`.
3. Invoke it with a coding request. Include scope and constraints:

```text
$council-flow Implement a small offline CSV summarizer in this repository.
Accept a local input file, validate its columns, print totals, and add tests.
Stay within demo/csv-summary/ and preserve existing files.
```

The skill creates compact internal contracts. Native Planner mode is the default. To supply
an external plan, say explicitly that it is Owner-approved and include the original plan. The
Manager keeps that plan unchanged and does not claim to call an external ChatGPT.

The production Planner follows `.agents/skills/council-flow/references/planner.md`.
Manager validates each READY plan and the selected task's exact instruction transfer before
Worker dispatch with `scripts/planner_contract.py`; non-ready plans remain nondispatchable.

Frozen criteria you supply are captured from your original input before the Planner runs.
The original bytes and their hash are kept, and their provenance is recorded. Generated
criteria cannot replace them. Missing, stale, substituted or altered input fails closed.
The supported format and exact comparison rules are in
[source fidelity](.agents/skills/council-flow/references/source-fidelity.md). A matching
hash proves integrity, not Owner approval.

Codex should detect skill changes automatically. If the selector does not update, restart
Codex in this repository and check `/skills` or type `$` in the CLI or IDE. This does not
guarantee that discovery or activation worked in every host. If native delegation is missing,
the workflow reports the gap instead of simulating role sessions. Observed results for this
build are in `reports/`.

## User-wide bootstrap

From PowerShell 7 (`pwsh`) in a CouncilFlow checkout, inspect the intended user paths first:

```powershell
./scripts/bootstrap.ps1 -Install -DryRun
```

Install, inspect status, refresh safe managed copies, or remove only recognized installations:

```powershell
./scripts/bootstrap.ps1 -Install
./scripts/bootstrap.ps1 -Status
./scripts/bootstrap.ps1 -Update
./scripts/bootstrap.ps1 -Uninstall
./scripts/bootstrap.ps1 -CheckRemote
./scripts/bootstrap.ps1 -UpdateRemote
./scripts/bootstrap.ps1 -Rollback
./scripts/bootstrap.ps1 -EnableAutomatic -DryRun
./scripts/bootstrap.ps1 -EnableAutomatic
./scripts/bootstrap.ps1 -DisableAutomatic
```

The Codex skill targets `~/.agents/skills/council-flow`; role files target
`~/.codex/agents/council-*.toml`. When the Claude CLI and the optional
`plugins/councilflow/.claude-plugin/plugin.json` source are both present, the bootstrap
synchronizes that tree to `~/.claude/skills/councilflow`. This file sync alone does not
prove Claude plugin discovery or role dispatch. Directory junctions and file
symlinks keep these installations synchronized with the checkout. Where a link cannot be
created, the bootstrap records managed copies and updates them only while their installed
hashes still match. Existing destinations are treated as collisions; the agent directory is
never replaced. Restart the host if it does not reload changed instructions.

`-Update` synchronizes from the currently installed local or managed source. `-CheckRemote`
checks the pinned `https://github.com/luvhscupid/CouncilFlow` `main` branch without activating
it. `-UpdateRemote` clones that branch into a separate managed checkout, confirms the branch
and commit, rejects non-fast-forward changes, runs deterministic package tests, and swaps only
bootstrap-owned destinations. It preserves the prior source and supports `-Rollback`. Failed
checks leave the active installation unchanged. Git operations never fetch or merge into the
development checkout.

Daily updates are opt-in with `-EnableAutomatic`; `-EnableAutomatic -DryRun` only previews the
current-user, limited-privilege Task Scheduler registration. No task was registered during
implementation. `-DisableAutomatic` removes only a task whose action matches this bootstrap.
The updater requires network access to the configured upstream when run and refuses dirty
managed checkouts or an unexpected default branch.

## Install in another repository

1. Copy the whole `.agents/skills/council-flow/` folder to the same path in the destination
   repository.
2. Copy the four `.codex/agents/council-*.toml` files to that repository's `.codex/agents/`,
   if its Codex version supports standalone custom agents.
3. Keep existing files. Resolve name collisions first, and do not overwrite another install
   silently. No global configuration registration is needed for the current agent format.
4. Restart Codex if needed, then run `$council-flow <your coding goal>`. If the host supports
   native delegation but cannot select custom agent files, the skill passes role instructions to
   separate native subagents and reports that limitation.

A user-wide install (`~/.agents/skills/council-flow/` and `~/.codex/agents/`) is optional. Check
for conflicts first. This build does not perform that installation or change global settings.

## Codebase Memory context (optional)

Invoke `$council-flow <coding request>` as usual. Before the Planner runs, the Manager uses the
existing DeusData Codebase Memory MCP for existing-project navigation when its tools are
available. An empty directory, or one with only CouncilFlow installation files, makes zero MCP
calls. The full lifecycle is in [Codebase Memory context](docs/technical/codebase-memory.md).

The lifecycle reference, `.agents/skills/council-flow/references/codebase-memory.md`, ships inside the complete skill folder copied during installation. No manual initialization command is required. No additional
skill or registration is needed. Focused static instruction checks run with `python -m unittest discover -s tests -p test_codebase_memory_integration.py -v`. These checks do not establish native invocation or live MCP behavior.

## Demonstrations

All demonstrations are offline examples inside this repository. They are not a standalone
application.

- **Receipt calculator (finished):** `demo/receipt/receipt_calculator.py`.

  ```sh
  python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg
  python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v
  ```

  See [demo instructions](demo/README.md) for limits and error handling.
- **Starter fixture (intentionally incomplete):** `demo/starter/`. Its sample calculation test is
  expected to fail. It is kept as baseline evidence, not as a finished application.
- **CSV summarizer:** [demo/csv-summary/README.md](demo/csv-summary/README.md).

  ```sh
  python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity
  python3 -m unittest discover -s demo/csv-summary -v
  ```

  It uses only the standard library, does not modify its input, and works offline.
- **Gate 3 column-sum example:** [demo/gate3-demo/README.md](demo/gate3-demo/README.md).

  ```sh
  python demo/gate3-demo/app.py demo/gate3-demo/inputs/amount.csv amount
  python -m unittest discover -s demo/gate3-demo -v
  ```

  Historical Run 01 remains NATIVE_ROLE_WORKFLOW_PARTIAL: seven E-checks passed, and E1, E2 and E4
  remain UNVERIFIED.
- **Structured-flow demo:** [demo/structured-flow/README.md](demo/structured-flow/README.md). It
  shows a mandatory failure and rework path.

Running a demo does not prove that the skill was activated natively. Host evidence is reported
separately.

## Testing

Static product checks use only Python 3.11 or newer with the standard library:

```sh
python3 -m unittest discover -s tests -v
```

This suite covers static metadata, references and native TOML checks, plus deterministic
JSON/YAML/JSONL validator tests, including synthetic C1/C2 controls. It does not establish native
skill invocation or real role independence. The V01–V14 definitions are in
`tests/validation_cases.json`. T01–T24 are synthetic regression definitions, not evidence of real
native-agent execution.

Release packaging and portability checks are described in [RELEASE.md](RELEASE.md).

## Where to go next

- [Documentation index](docs/technical/README.md): every technical document, with its purpose.
- [Requirements traceability](https://github.com/luvhscupid/CouncilFlow/blob/9c59bc3d0f98a818b01ad14d0165d92b236105b0/reports/requirements-traceability.md) and [final report](https://github.com/luvhscupid/CouncilFlow/blob/9c59bc3d0f98a818b01ad14d0165d92b236105b0/reports/final.md).
