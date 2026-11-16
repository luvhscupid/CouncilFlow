# Demo programs

This folder holds small, offline Python programs that demonstrate and test the
CouncilFlow workflow. They are examples inside the CouncilFlow repository, not a
standalone AI application or product. None of them calls an AI model, needs an
API key, or uses the network.

| Folder | What it shows | Guide |
|---|---|---|
| `receipt/` | The finished receipt calculator (exact decimal arithmetic, rupiah output). | This file |
| `starter/` | A deliberately incomplete fixture kept as a failing baseline. | This file |
| `csv-summary/` | An offline CSV summarizer that totals selected numeric columns. | [csv-summary/README.md](csv-summary/README.md) |
| `gate3-demo/` | A maintained Gate 3 example that sums one CSV column with `Decimal`. | [gate3-demo/README.md](gate3-demo/README.md) |
| `structured-flow/` | A small integer-summing program used to show a failure-and-rework path. | [structured-flow/README.md](structured-flow/README.md) |

## Prerequisites

- **Python 3.11 or newer.** The repository documents 3.11+ as the requirement.
  The commands below were run with Python 3.12.3.
- **No third-party packages.** Only the Python standard library is used.
- **A terminal opened at the repository root** (the folder that contains `README.md`,
  `AGENTS.md`, and `demo/`). Every command in this guide assumes that location.

Check your Python version first:

```sh
python3 --version
```

On Windows, if `python3` is not found, use `python` or `py -3` in place of
`python3` in every command. The commands in this guide use `python3`.

If Unicode characters such as `×` print as garbled text on Windows, run the
program with UTF-8 output enabled. The text output is otherwise unchanged.

- Git Bash: `PYTHONUTF8=1 python3 demo/receipt/receipt_calculator.py ...`
- PowerShell: `$env:PYTHONUTF8 = "1"` before running the command.

## Receipt calculator (`receipt/`)

This is the finished program. It reads products from the command line and prints
each line total and a grand total in rupiah.

Run the Owner's example from the repository root:

```sh
python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg
```

Expected output:

```text
2 kg rice × Rp30,000 = Rp60,000
1 kg onions × Rp43,000 = Rp43,000
Total = Rp103,000
```

Each `--item` takes four values: `NAME QUANTITY UNIT_PRICE UNIT`. Repeat `--item`
for each product.

- Quantities and prices are plain decimals with no `Rp`, no commas, and no
  exponent notation. `1e3` is rejected; write `1000`.
- Zero is accepted. Negative, malformed, and non-finite values are rejected.
- Each quantity or price supports up to 18 integer digits and 12 fractional digits.
  Larger precision is rejected with an explicit error.
- The unit is required and must not be blank (for example `kg`, `box`, or `each`).
  Quote names or units that contain spaces.
- Fractional rupiah stay visible. For example, `--item x 1 0.02 each` prints `Rp0.02`.

A second example:

```sh
python3 demo/receipt/receipt_calculator.py --item tea 3 12500 box --item sugar 1.5 14000 kg
```

This prints a total of `Rp58,500`.

Show help:

```sh
python3 demo/receipt/receipt_calculator.py --help
```

Run the receipt tests (13 tests, all expected to pass):

```sh
python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v
```

Invalid input exits with status `2` and a usage message, for example:

```text
receipt_calculator.py: error: item 1: quantity must be zero or greater
```

Importable API (for code that wants to reuse the calculation):
`ProductEntry(name, quantity, unit_price, unit="")` with a `line_total` property,
`grand_total(entries)`, and `format_rupiah(Decimal)`. Pass strings, integers, or
`Decimal` values. Floats are rejected on purpose, so binary floating-point values
do not enter the calculation. The Python API allows an empty unit; the command
line requires one.

## Starter fixture (`starter/`): a preserved failing baseline

`starter/` is an intentionally incomplete but valid Python program. Its
`ProductEntry.line_total` ignores the quantity, so the rice and onions calculation
is wrong. It is kept unchanged so the starting defect can be reproduced. Do not
fix it in place; the finished program lives in `receipt/`.

Run the tests. One test is expected to fail:

```sh
python3 -m unittest discover -s demo/starter -p 'test_*.py' -v
```

The failure looks like this:

```text
FAIL: test_multiple_product_quantities
AssertionError: Decimal('73000') != Decimal('103000')
```

Run the starter program. It exits with status `0` but prints the wrong total:

```sh
python3 demo/starter/receipt_calculator.py
```

```text
2 kg rice × Rp30,000 = Rp30,000
1 kg onions × Rp43,000 = Rp43,000
Total = Rp73,000
```

This failure is the expected baseline. It is not a failure of the finished
application.

## Other demos

- CSV summarizer: [csv-summary/README.md](csv-summary/README.md)
- Gate 3 column sum: [gate3-demo/README.md](gate3-demo/README.md)
- Structured-flow rework demo: [structured-flow/README.md](structured-flow/README.md)

## Related documents

- Repository overview and how the CouncilFlow skill is used: [../README.md](../README.md)
- Release contents and checks: [../RELEASE.md](../RELEASE.md)
- Final reports: [../reports/final.md](../reports/final.md)
