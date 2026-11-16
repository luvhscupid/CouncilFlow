# Original input and verification oracles

## Capture before Planner

For every supplied frozen plan or mandatory acceptance list, Manager obtains the
actual Owner input from the host-exposed attachment/message or Owner-identified
file before Planner transforms it. Preserve those bytes, provenance location and
artifact identity/SHA-256. If an authorized-root copy is needed, compare its bytes
to the original and retain the original reference/hash in the run evidence.
Keep this reference separate from agent-generated plans and `owner-criteria.json`.
A digest establishes integrity; actual observed Owner input establishes the
provenance claim. A role, filename, kind label or matching hash is not approval.

The existing helper supports bounded UTF-8 text with column-zero `ACn: ` labels
(`n` is a positive integer). It enumerates every label in source order, rejects
duplicates and ambiguous/indented/list-prefixed labels, and preserves criterion
text exactly. A record ends before the next label, or at EOF; exactly one final
LF or CRLF separator is outside its text. Additional blank lines, tabs, spaces,
punctuation, Markdown, Unicode and internal LF/CRLF remain unchanged. Put task
context before the first AC label. The entire original file is hash-bound.
Unsupported or ambiguous source formats fail closed; an agent-selected subset
or reformatted copy cannot silently replace the original. An arbitrary external
prose plan needs an actually approved unambiguous criteria source, not an
AI-invented claim of completeness. Preserve the full prose plan as well.

Manager creates an ordinary artifact reference of kind `owner-original-source`
to the preserved raw input, based on observed input provenance. For example:

```sh
python3 .agents/skills/council-flow/scripts/contracts.py capture original-ref.json --root . --owner-provenance original-input
```

Here `original-input` must be the actual original reference's artifact_id, and
the caller supplies `--owner-provenance` only for input it actually observed.
Capture prints a derivative `{source_ref, criteria}`. Save it as a new file;
never rewrite the source. Planner copies captured strings into `acceptance`
unchanged and preserves `original_source_ref` in its plan metadata. Add IDs,
traceability or planning notes separately from criterion text.

Before first role dispatch and at every subsequent controlled boundary, including
rework and the original Planner's final check, Manager validates the full ordered
context with the same separately retained original reference:

```sh
python3 .agents/skills/council-flow/scripts/contracts.py sequence plan-publish.json assignment.json --root . --require-criteria-fidelity --original-source-ref original-ref.json --owner-provenance original-input
```

Add actual binding/context files as available. `--authoritative-criteria-ref`
may additionally check a generated JSON derivative, but it cannot replace
`--original-source-ref`. Any derivative source_ref must match the pinned original.
Missing, stale, substituted or text-mismatching sources block dispatch/acceptance;
preserve rejected plans instead of rehashing a rewrite into authority. Repeat the
same validation with final evidence; a successful earlier check is not sufficient.

This is caller-checked provenance and byte fidelity, not authenticated capture,
immutable storage or native transport enforcement. If the host cannot expose the
actual input or its provenance, mark frozen-source fidelity BLOCKED/UNVERIFIED
and continue only independent authorized work. Never infer it from a derivative.
Ordinary requests without supplied frozen criteria may retain native planning;
preserve the actual request and distinguish generated acceptance from Owner text.

## Manual Council handoff completeness

Preserve the actual approved external plan and its provenance verbatim. Before
dispatch, Planner provides a bounded handoff inventory identifying each approved
requirement/constraint by source location and its plan/verification destination.
List objections, tradeoffs and rejected alternatives separately with their recorded
disposition; they do not become new mandatory criteria by synthesis. Manager
checks every approved item has a destination, and unresolved approval/completeness
is explicit. This is a traceability check, not proof of semantic completeness or
automation of the manual cross-model Council. The Owner supplies inputs once;
Manager transfers internal references and packets without Owner courier work.

## Preserve accepted oracles before Worker

Before Worker dispatch, Manager snapshots the accepted test/strategy files and
records their inventory, paths and SHA-256 in its approved oracle artifact.
Keep those pristine copies separate from candidate-editable tests. After Worker
stops, Tester verifies those identities and independently exercises original
behavior against the exact candidate; Worker-modified tests are untrusted input.
Authorized new tests may supplement this oracle, but cannot silently replace it.
If pristine checks cannot run against the candidate, report an explicit
unverified/blocked check; a green weakened candidate suite is insufficient.
Record the preserved oracle references among deterministic command input_refs.
Reviewer receives them unchanged and independently reruns the declared command.
The helper binds oracle_ref identity and report echo; it does not understand
arbitrary strategy prose or enforce test execution. Objective behavioral negative
controls are needed. Distinct native sessions may share model weights and errors;
their labels alone do not establish independent reasoning or provider diversity.
