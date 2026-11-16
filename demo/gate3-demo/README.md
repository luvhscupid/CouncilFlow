# Gate 3 column sum

This maintained offline example sums a named CSV column with Python `Decimal`.
The positional CLI prints one total and exits 0; missing columns, nonnumeric or
nonfinite values, missing files, invalid encoding and CSV errors produce a clean
stderr message and nonzero exit. Input files remain unchanged.

```sh
python demo/gate3-demo/app.py demo/gate3-demo/inputs/amount.csv amount
python -m unittest discover -s demo/gate3-demo -v
```

The sample prints `5`. The original seven deterministic tests remain, adapted
only to local fixture paths and maintained-test wording; separate edge cases
cover BOM input, exact fractional totals, missing/blank values and bad encoding.
`provenance.json` records selected source paths/hashes. No original Owner task
or criteria fixture is duplicated or rewritten. Existing source-fidelity and
workflow contracts remain authoritative for handoffs.

Historical Run 01 classification remains **NATIVE_ROLE_WORKFLOW_PARTIAL**:
seven E-checks passed, while E1, E2 and E4 remain **UNVERIFIED**. Original
independent Tester/Reviewer records remain in the Gate 3 worktree checkpoint,
separate from current release tests. This example and its unit tests do not
establish native skill activation, causal delegation or TOML loading.
