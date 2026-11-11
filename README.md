# CouncilFlow

CouncilFlow is an installable, instruction-based Codex coding skill. A dedicated
Planner defines acceptance; the parent Manager delegates implementation to a
fresh Worker, requests separate Tester and Reviewer assessments, coordinates
repairs, and asks the Planner for a final objective check. Only the Manager gives
routine progress and results to the human Owner.

This build is **PARTIAL**: native discovery succeeded, but successful explicit
invocation is unverified because the separate native CLI rejected its existing
authentication token. The real-agent demonstration applies the skill manually;
it does not prove successful `$council-flow` activation. See [RELEASE.md](RELEASE.md)
and [execution evidence](reports/manager-execution.md).

It uses native Codex delegation and inherited account/provider permissions. It
needs no API key, subscription, database, server, or custom agent runtime. Role
instructions are expected behavior, not independent OS-enforced isolation.

## Use in this repository

Open Codex at this repository root. The discoverable skill is
`.agents/skills/council-flow/SKILL.md`; custom agent definitions are under
`.codex/agents/`. In a host supporting skills and native subagents, invoke:

```text
$council-flow Implement a small offline CSV summarizer in this repository.
Accept a local input file, validate its columns, print totals, and add tests.
Stay within demo/csv-summary/ and preserve existing files.
```

Supply an ordinary coding request with scope and constraints. The skill creates
compact internal contracts. Native Planner mode is the default. To supply an
external plan, explicitly identify it as Owner-approved and include the original
plan; the Manager preserves it and does not claim to call external ChatGPT.

Codex should detect skill changes automatically. If the selector does not update,
restart Codex in this repository and check `/skills` or type `$` in CLI/IDE. This
guidance is not a claim that discovery or activation succeeded in every host.
If native delegation is missing, the workflow reports the gap instead of
simulating role sessions. See `reports/` for this build's observed verification.

## Install in another repository

Copy the whole `.agents/skills/council-flow/` folder to the destination
repository's `.agents/skills/council-flow/`. Copy the four
`.codex/agents/council-*.toml` files to that repository's `.codex/agents/` if its
Codex version supports standalone custom agents. Preserve existing files and
resolve naming collisions before copying; do not overwrite another installation
silently. No global configuration registration is needed for the current
standalone agent format.

Restart Codex if needed and invoke `$council-flow <your coding goal>`. Where the
host supports native delegation but cannot select custom agent files, the skill
passes role instructions to separate native subagents and reports that limitation.

For an optional later user-wide installation using ordinary user permissions,
copy the skill folder to `~/.agents/skills/council-flow/` and agent TOMLs to
`~/.codex/agents/`, after checking for conflicts. This build does not perform
that installation or modify global settings. Repository installation is enough.

## Demonstration and validation

`demo/starter/` is a deliberately incomplete, valid Python fixture. Its sample
calculation test is expected to fail; it is retained as baseline evidence, not
the finished application. See [demo/README.md](demo/README.md) for its bounded
interface and commands. The completed application's location and actual role
results are recorded by the Manager in `reports/` after the real run.

The finished offline calculator is `demo/receipt/receipt_calculator.py`. Run:

```sh
python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg
python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v
```

See [demo instructions](demo/README.md) for numeric bounds, other examples, and
error handling. This application demonstration does not by itself establish
successful native skill activation; actual host evidence is reported separately.

Static product checks use only Python 3.11+ standard library:

```sh
python3 -m unittest discover -s tests -v
```

These checks validate metadata, references, custom-agent TOML syntax, and workflow
instruction coverage. They do not establish live discovery, invocation, role
independence, or application correctness. The V01–V14 definitions are in
`tests/validation_cases.json`; runtime evidence must be recorded separately.

See [RELEASE.md](RELEASE.md) for package contents, portability, and release checks.

## Offline CSV summarizer

The [CSV summarizer](demo/csv-summary/README.md) counts data records and prints
exact totals for explicitly selected numeric columns, with input validation:

```sh
python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity
python3 -m unittest discover -s demo/csv-summary -v
```

It uses only the Python standard library, preserves its input, and works offline.
