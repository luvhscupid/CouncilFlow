# CouncilFlow

CouncilFlow is an installable, instruction-based Codex coding skill. A dedicated
Planner defines acceptance; the parent Manager delegates implementation to a
fresh Worker, requests separate Tester and Reviewer assessments, coordinates
repairs, and asks the Planner for a final objective check. Only the Manager gives
routine progress and results to the human Owner.

**Council Round 6 corrections are implemented and deterministically verified in
the isolated `CouncilFlow-round6` copy. Gate 3b is blocked** because this
workspace has no Git history or recoverable clean pre-test receipt-calculator
fixture: the available candidate already contains the requested `--version`
feature. No fresh activation was claimed. See [Gate 3b results](reports/gate3b-results.md),
[release details](RELEASE.md), and historical results in [reports/final.md](reports/final.md).

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

This suite combines static metadata/reference/native-TOML checks and executable
deterministic JSON/YAML/JSONL validator tests, including synthetic C1/C2 controls. It does not establish native skill
invocation or real role independence. Application and native-agent observations
are tested and recorded separately. The V01–V14 definitions remain in
`tests/validation_cases.json`; T01–T24 are synthetic regression definitions, not
real native-agent execution evidence.

See [RELEASE.md](RELEASE.md) for package contents, portability, and release checks.

## Offline CSV summarizer

The [CSV summarizer](demo/csv-summary/README.md) counts data records and prints
exact totals for explicitly selected numeric columns, with input validation:

```sh
python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity
python3 -m unittest discover -s demo/csv-summary -v
```

It uses only the Python standard library, preserves its input, and works offline.

## Automatic Codebase Memory context

Invoke `$council-flow <coding request>` as usual. Before Planner, Manager
automatically uses the existing DeusData Codebase Memory MCP for relevant
existing-project navigation when its tools are available. It first inspects local
content: an empty directory or one containing only CouncilFlow installation
files makes zero MCP calls. Once meaningful source exists, Manager identifies
the exact project, initializes a useful missing index, checks freshness, and
retrieves task-relevant symbols, files, and dependencies. After implementation
and rework, it updates the index after Worker stops edits. Source reads cover
critical code, uncertain freshness, and index gaps.

Codebase Memory is an optional, separately configured capability. CouncilFlow
does not install or reconfigure it and adds no memory engine, manifest, database,
API key, or manual initialization command. Missing tools or an unreachable
configured server fall back to ordinary repository inspection, with live MCP
use reported as UNVERIFIED. Graph findings support navigation; the existing
independent Tester, Reviewer, and final Planner checks still decide acceptance.

The [lifecycle reference](.agents/skills/council-flow/references/codebase-memory.md)
ships inside the complete skill folder copied during installation. No additional
skill or registration is needed. Focused static instruction checks run with
`python -m unittest discover -s tests -p test_codebase_memory_integration.py -v`;
run the complete suite with `python -m unittest discover -s tests -v`. These
checks do not establish native invocation or live MCP behavior.

## Structured internal communication

CouncilFlow 1.0 now defines **UTF-8 JSON** task packets for Planner, Manager,
Worker, Tester and Reviewer. The role/workflow source is
[versioned YAML policy](.agents/skills/council-flow/policies/roles.yaml);
Codex-native agents remain TOML. Optional bounded JSONL is diagnostics.
Owner progress and results remain concise natural language.

Read the [communication contract](.agents/skills/council-flow/references/communication.md)
for closed payloads, causal/candidate/origin checks, limits and exact examples.
The small installed Python helper is standard-library-only:

~~~sh
python3 .agents/skills/council-flow/scripts/contracts.py message packet.json --root .
python3 .agents/skills/council-flow/scripts/contracts.py sequence plan-packet.json assignment.json report.json --root . --bindings observed-bindings.json
python3 .agents/skills/council-flow/scripts/contracts.py policy .agents/skills/council-flow/policies/roles.yaml
python3 .agents/skills/council-flow/scripts/contracts.py events events.jsonl --root .
python3 -m unittest discover -s tests -v
~~~

Sequence context and externally observed actor bindings are not copied from
self-asserted sender labels. A Worker output may differ from its assigned input;
Tester and Reviewer must verify the exact output. Reviewer also compares original
criteria and Tester evidence and reruns one declared deterministic command.
Manager assigns the test strategy, and a Tester cannot self-approve or substitute
its oracle.
For a Tester assignment, `oracle_ref` is **required** and the report must echo
it exactly. General optional-reference wording applies to other assignments;
it does not waive the Tester's Manager-approved strategy requirement.

These are controlled-file checks, not authentication, transport enforcement,
permissions, a database or a new agent engine. The policy uses a restricted,
documented YAML subset without installing a parser. Product source and all
subfolders of the skill must be copied together when installing elsewhere.

The fresh [structured-flow demo](demo/structured-flow/README.md) supplies a real
mandatory failure/rework path, separate from old demonstrations.
[Requirements traceability](reports/requirements-traceability.md) distinguishes
static, dynamic, native and blocked evidence. The current final classification
and new activation result are recorded by Manager after independent verification
in [reports/final.md](reports/final.md); prior evidence is not a new invocation.
