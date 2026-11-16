# Gate 3 reference package

This directory holds the Owner-supplied CouncilFlow Gate 3 v0.2 package, imported into the repository as **reference and testing documentation**. It is not an experiment record, an implementation, or evidence that Gate 3 has run.

## Status at a glance

- **Gate 3 has not been run by this integration.** The experiment record in the package is blank. All ten checks (E1 to E10) are UNVERIFIED, and no run-level outcome is assigned.
- Archive integrity checks and source inspection are documentation work. They are not evidence of skill activation, delegation, role effectiveness or Gate 3 success.
- Earlier demonstrations and authentication reports are not a fresh Gate 3 run.
- The installed skill, native agent configurations, policy, code, tests and release archive are unchanged for evaluation. Read the [current implementation gap assessment](current-implementation-gaps.md) before relying on older role definitions or release claims.

## Import provenance

The seven members of `CouncilFlow-Gate3-v0.2-Frozen.zip` are preserved byte-for-byte in [`CouncilFlow-Gate3-v0.2/`](CouncilFlow-Gate3-v0.2/README.md). All six document checksums in that package's original [`SHA256SUMS.txt`](CouncilFlow-Gate3-v0.2/SHA256SUMS.txt) match. [`import-record.json`](import-record.json) records the archive digest and each extracted member's digest.

The later addition [`06-COUNCIL-APPROVED-ERRATUM-C3.md`](CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md) is not listed in the original checksum manifest or in `import-record.json`. It is a separate Council record, and it is not covered by those integrity checks.

## Authority and precedence

For conflicting older CouncilFlow documentation, the controlling order is:

1. [Owner Charter](CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md). Controlling Owner intent.
2. [Frozen Gate 3 v0.2 specification](CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md). Council Round 6's approved E4 erratum is recorded separately at [06-COUNCIL-APPROVED-ERRATUM-C3.md](CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md). The frozen source and its historical outcomes are unchanged, and the erratum changes only E4.
3. Earlier CouncilFlow documentation, where it is consistent with those sources.

The Charter supersedes the older view of the Reviewer as mainly an advisory UX evaluator. Under the Charter, the Reviewer compares Worker output, Tester output and the original frozen Owner plan. It also independently reruns one deterministic Tester command with the specified exit-code and output-hash comparison.

The Owner submits frozen criteria once and performs no internal courier work. The external Owner, Claude, GPT and Astra Sol Council remains manual.

This precedence records the Owner's requirements. It does not claim that the installed skill already implements them.

## Reading order

Read the imported package in its original order:

1. [Owner Charter](CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md).
2. [Gate 3 E1 to E10, evidence rules, outcomes and stop rule](CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md).
3. [Blank experiment record](CouncilFlow-Gate3-v0.2/03-EXPERIMENT-RECORD.md).
4. [Optional fixture example](CouncilFlow-Gate3-v0.2/04-TASK-FIXTURE-EXAMPLE.md). This is not Owner-approved acceptance text. The Owner must freeze its exact criteria before any use.
5. [Council ratification and provenance](CouncilFlow-Gate3-v0.2/05-COUNCIL-RATIFICATION.md).
6. [Original package README](CouncilFlow-Gate3-v0.2/README.md) and [SHA256SUMS.txt](CouncilFlow-Gate3-v0.2/SHA256SUMS.txt).
7. [Council-approved erratum C3](CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md), which controls E4 wording for the Gate 3b run.

Instructions inside the package describe a separately authorized future experiment. They are not commands executed by this import. This import authorizes no skill corrections, experiment invocation, demo changes, new role, planted-bug evaluation or external-Council automation.

## Evidence labels

- `RAN`: executed and observed in a specific run.
- `READ`: inspected document or artifact.
- `CLAIMED`: relayed or unverified assertion.

Import checks are `READ` and integrity-check work. They are not `RAN` evidence of any Gate 3 check.

## Related

- Root project contract: [`../../AGENTS.md`](../../AGENTS.md).
- Non-normative research and planning records: [`../research/README.md`](../research/README.md). These do not change the Gate 3 authority order above.
- Full planning bundle: [`../CouncilFlow-Full-Plan/README.md`](../CouncilFlow-Full-Plan/README.md). Historical and superseded where it conflicts with this package.
