# Gate 3 column sum

This maintained, offline example sums one named column of a CSV file using Python
`Decimal`. It is a demonstration inside the CouncilFlow repository. It does not
call an AI model, needs no API key, and uses no network. Input files are never
modified.

## Prerequisites

- Python 3.11 or newer (the commands below were run with Python 3.12.3).
- No third-party packages.
- A terminal opened at the repository root (the folder that contains `demo/`).

On Windows, if `python3` is not found, use `python` or `py -3` instead. The
commands in this guide use `python`, which matches the repository root README.

## Run the sample

From the repository root:

```sh
python demo/gate3-demo/app.py demo/gate3-demo/inputs/amount.csv amount
```

Expected output (exit status `0`):

```text
5
```

The input file `demo/gate3-demo/inputs/amount.csv` contains a header `amount`
followed by the values `2` and `3`.

## Usage

```text
python demo/gate3-demo/app.py CSV_PATH COLUMN
```

- `CSV_PATH` is a local CSV file with a header row.
- `COLUMN` is the exact header name to sum.
- The program prints one total and exits with status `0`.

## Error behavior

Errors print a message to stderr, print no total, and exit with status `1`. No
traceback is shown. The cases covered are:

- the requested column is missing from the header
- a value is not a number, or is not finite (`NaN` or infinity)
- the file does not exist
- the file is not valid UTF-8 or is not readable CSV

Example, using the included nonnumeric fixture:

```sh
python demo/gate3-demo/app.py demo/gate3-demo/inputs/nonnumeric.csv amount
```

```text
Error: Nonnumeric value 'not-a-number' in column 'amount' at CSV line 2
```

Note that this program uses exit status `1` for errors. The CSV summarizer in
`demo/csv-summary/` uses exit status `2` for its input errors.

A UTF-8 byte-order mark (BOM) at the start of a file is accepted. Fractional
values are summed exactly.

## Run the tests

From the repository root:

```sh
python -m unittest discover -s demo/gate3-demo -v
```

The suite has 9 tests, all expected to pass:

- 7 deterministic tests carried over from the Gate 3 run. They were adapted only
  to use local fixture paths and maintained test wording.
- 2 separate edge-case tests in `test_edge_cases.py`. They cover BOM input, exact
  fractional totals, blank or missing values, and invalid encoding.

## Provenance and historical status

`provenance.json` records the source paths and SHA-256 hashes of the files that
were imported into this folder, and the source branch and commit they came from.
No original Owner task or criteria fixture is copied or rewritten here.

The historical Gate 3 Run 01 classification is **NATIVE_ROLE_WORKFLOW_PARTIAL**.
Seven E-checks passed. E1, E2, and E4 remain **UNVERIFIED**. The original
independent Tester and Reviewer records stay in the Gate 3 worktree checkpoint,
separate from the current release tests.

This example and its unit tests do not establish native skill activation, causal
delegation, or TOML loading. Those claims are covered by the workflow evidence
described in the repository documents.

## Related

- Overview of all demos: [../README.md](../README.md)
- Repository overview: [../../README.md](../../README.md)
