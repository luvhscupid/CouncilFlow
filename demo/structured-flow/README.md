# Structured-communication demo (structured-flow)

This isolated, offline program adds up one or more signed whole numbers. It is a
demonstration inside the CouncilFlow repository, showing a mandatory
failure-and-rework path. It does not call an AI model, needs no API key, and uses
no network.

## Prerequisites

- Python 3.11 or newer (the commands below were run with Python 3.12.3).
- No third-party packages.
- A terminal opened at the repository root (the folder that contains `demo/`).

On Windows, if `python3` is not found, use `python` or `py -3` instead.

## Run it

From the repository root:

```sh
python3 demo/structured-flow/sum_values.py 2 3 -1
```

Expected output (exit status `0`):

```text
4
```

## Usage

```text
python3 demo/structured-flow/sum_values.py VALUE [VALUE ...]
```

- Give one or more values. Each value must be a signed ASCII integer, such as `-2`,
  `0`, `+12`, or `3`.
- Values are summed exactly, including negative values and zero.
- Python's integer conversion limits apply. If a value or the total is too large
  to convert, the program fails with a clear message and prints nothing.

Show help:

```sh
python3 demo/structured-flow/sum_values.py --help
```

Invalid input fails clearly, with no traceback and exit status `2`. For example:

```sh
python3 demo/structured-flow/sum_values.py 1.2
```

```text
sum_values.py: error: argument values: use a signed ASCII integer, for example -2 or 3
```

## Run the tests

From the repository root:

```sh
python3 -m unittest discover -s demo/structured-flow -v
```

There are 5 tests, all expected to pass. They cover:

- summing several signed values
- single values and zero
- invalid values, with no traceback
- missing values and `--help`
- large operands near the conversion limit, and a total that exceeds the output
  bound

The first four tests are the original acceptance coverage. The large-operand test
was added later as a regression for the output bound.

## Why this demo exists: the rework path

The first attempt at this program, made by the primary Worker, was deliberately
incomplete. It returned only the first operand, so `2 3 -1` printed `2` instead of
`4`. A separate Tester observed the multiple-value failure. The Manager rejected
that candidate and assigned a fresh Worker to repair it, with the acceptance
criteria unchanged. The current `sum_values.py` contains that repair.

The evidence is recorded under `reports/restoration/`:

- `reports/restoration/worker/` holds the initial source of the incomplete attempt.
- `reports/restoration/verification/initial/` holds the failed output and the
  verification records.

Actual JSON task packets, independent observations, rework records, and final
outcomes belong in `reports/restoration/`. The unit tests in this folder are
synthetic fixtures. They do not count as agent evidence.

This is a new execution. It is not the older receipt demonstration in
`demo/receipt/`. The independent final verification is recorded separately, in
[../../reports/final.md](../../reports/final.md).

## Related

- Overview of all demos: [../README.md](../README.md)
- Repository overview: [../../README.md](../../README.md)
