# E10 source-fidelity analysis

This is direct maintenance analysis, not a Gate 3 rerun or certification. No
historical file was modified.

## Recorded reproduction

On Windows, from the isolated maintenance worktree:

`python -B reports/engineering-recovery/analysis/reproduce_e10.py`

Exit: 0. Output: `e10-baseline-reproduction.json` alongside this note.
The actual historical initial progress and plan publication pass normal ordered
sequence validation. They also pass the existing required-fidelity mode when
the actual generated `owner-criteria.json` is supplied as the trusted criteria
reference. Direct comparison to the saved Owner fixture disagrees on AC1 and
AC2: their backticks were removed before publication. The generated fixture and
plan agree with one another; that agreement does not establish source fidelity.

Original fixture SHA-256:
`e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d`.
It is 260 bytes. Criterion payload byte ranges, exclusive end:
AC1 `[65,140)`, AC2 `[146,198)`, AC3 `[204,259)`.

## Ranked causes and falsifiable predictions

1. **Confirmed: derivative-as-authority substitution.** `_authoritative_criteria`
   checks the bytes of a caller-supplied JSON criteria derivative, without an
   original-input reference. Prediction: matching altered derivative and plan
   pass required fidelity while differing from the actual Owner source.
   The reproduction confirms this.
2. **Confirmed: normal validation is source-optional.** Ordinary sequence checks
   need only self-consistent plan IDs and acceptance IDs. Prediction: historical
   publication passes with no original-source reference. Confirmed.
3. **Confirmed: source capture is delegated to instruction-level copying.**
   Workflow instructions specify an Owner-approved JSON artifact but do not
   prescribe pre-Planner byte capture of the saved original. Planner TOML
   requires verbatim preservation but no direct source comparison. Prediction:
   the final check can cite only the altered plan and execution evidence and
   claim original criteria are met. Historical `plan-check.json` does exactly
   that; it contains no direct saved-fixture comparison.
4. **Not established: specific initial transcription/escaping mechanism.**
   Backticks are already missing from the first saved JSON derivative. Available
   historical artifacts do not expose the command that first assembled it.
   Do not attribute this to a specific shell, serializer, or model behavior
   without authentic execution evidence.

## Smallest maintainable correction

Keep the existing JSON protocol, YAML policy, native agents and explicit
instruction workflow. Separate the original raw-input reference from derived
criteria metadata. Pin the raw original identity/hash before Planner dispatch;
read its bytes directly and derive criteria without model transcription.

A source map can record IDs and exact byte ranges, with source identity/hash;
derived criterion text must equal the referenced bytes, including line breaks,
Markdown, punctuation and meaningful whitespace. Require that original source
reference separately whenever frozen-source fidelity is claimed. A generated
criteria JSON cannot satisfy a missing original merely by changing its kind.

For common labelled `ACn:` fixtures, deterministically enumerate every labelled
criterion in source order, rejecting duplicate IDs. Arbitrary agent-selected
ranges alone cannot prove completeness: dropping an original criterion before
constructing the map would otherwise remain possible. Other input formats need
a bounded explicit parser or authentic Owner-approved selection/provenance;
ambiguous unsupported frozen input must fail closed rather than paraphrase.

Make the normal SKILL/workflow/role instructions use this source binding before
dispatch, after changes/rework, and at final Planner acceptance. Preserve the
external Council's full approved source verbatim and reference constraints and
objections separately; do not silently promote synthesis into authority.

Retain clearly labelled structure-only validation for historical/synthetic
records, but never use that mode as proof of frozen-source fidelity. Hashes
prove byte integrity relative to a supplied trusted reference; they cannot
authenticate the Owner, establish immutable storage, or enforce OS isolation.
The caller must supply actual source provenance. This host does not expose an
authenticated raw original chat-input capture API in these artifacts.
