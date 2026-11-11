# Frozen CouncilFlow Gate 3 reference

This directory imports the Owner-supplied `CouncilFlow-Gate3-v0.2-Frozen.zip`
into the existing repository as reference and testing documentation. All seven
archive members are preserved byte-for-byte in
[`CouncilFlow-Gate3-v0.2/`](CouncilFlow-Gate3-v0.2/README.md), including the blank
experiment record, example fixture and original checksum manifest. All six
document checksums in that manifest match. [Import provenance](import-record.json)
records the archive digest and each extracted member's digest.

## Authority and scope

For conflicting older CouncilFlow documentation, the controlling order is:

1. [Owner Charter](CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md).
2. [Frozen Gate 3 v0.2 specification](CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md).
3. Earlier CouncilFlow documentation where consistent with those sources.

In particular, the Charter supersedes the older definition of Reviewer chiefly
as an advisory UX evaluator. Its Reviewer compares Worker output, Tester output
and the original frozen Owner plan, and independently reruns one deterministic
Tester command with the specified exit-code/output-hash comparison. The Owner
submits frozen criteria once and performs no internal courier work. The external
Owner/Claude/GPT/Astra Sol Council remains manual.

This precedence records the Owner's requirements; it does not claim the installed
skill already implements them. The current skill, native agent configurations,
policy, code, tests and release archive remain unchanged for evaluation. Read the
[current implementation gap assessment](current-implementation-gaps.md) before
interpreting the older role definitions or release claims.

## Contents and evidence status

Read the imported package in its original order:

1. [Owner Charter](CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md).
2. [Gate 3 E1–E10, evidence rules, outcomes and stop rule](CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md).
3. [Blank experiment record](CouncilFlow-Gate3-v0.2/03-EXPERIMENT-RECORD.md).
4. [Optional fixture example](CouncilFlow-Gate3-v0.2/04-TASK-FIXTURE-EXAMPLE.md).
5. [Council ratification and provenance](CouncilFlow-Gate3-v0.2/05-COUNCIL-RATIFICATION.md).
6. [Original package README](CouncilFlow-Gate3-v0.2/README.md) and
   [SHA256SUMS.txt](CouncilFlow-Gate3-v0.2/SHA256SUMS.txt).

**Gate 3 has not been run by this integration.** The imported experiment record
is still blank, with all ten check rows UNVERIFIED. No run-level outcome is
assigned. Archive integrity checks and source inspection are documentation work,
not evidence of activation, delegation, role effectiveness or Gate 3 success.
Earlier demonstrations and authentication reports are not a fresh Gate 3 run.

Instructions inside the package describe a separately authorized future
experiment. They are not commands executed by this import. The example task is
not Owner-approved acceptance text; it was neither selected nor implemented.
This task authorizes no skill corrections, experiment invocation, demo changes,
new role, planted-bug evaluation or external-Council automation.
