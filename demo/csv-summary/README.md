# Offline CSV summarizer

This program counts the data records in a local CSV file and prints exact totals
for the numeric columns you choose. It is a demonstration inside the CouncilFlow
repository. It does not call an AI model, needs no API key, and uses no network.

## Prerequisites

- Python 3.11 or newer (the commands below were run with Python 3.12.3).
- No third-party packages.
- A terminal opened at the repository root (the folder that contains `demo/`).

On Windows, if `python3` is not found, use `python` or `py -3` instead.

## Run the sample

From the repository root:

```sh
python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity
```

Expected output:

```text
Rows: 3
Total amount: 30
Total quantity: 6
```

The sample file `demo/csv-summary/sample.csv` contains:

```text
item,amount,quantity
rice,10.25,2
onions,20.50,3
refund,-0.75,1
```

## Usage

```text
python3 demo/csv-summary/csv_summarizer.py INPUT --column NAME [--column NAME ...]
```

- `INPUT` is a local file. Use a path you can read.
- Give at least one `--column NAME`. Repeat `--column` for each total you want.
  Output follows the order you give on the command line.
- Only the columns you name are parsed as numbers. Other columns can contain any
  text, or be empty.
- Column names are case-sensitive. They match the header after outer whitespace
  is removed.

Show help:

```sh
python3 demo/csv-summary/csv_summarizer.py --help
```

## Input rules

- The file must be comma-delimited UTF-8. A UTF-8 byte-order mark (BOM) is allowed.
- Standard CSV quoting works: double quotes, escaped quotes, CRLF line endings,
  Unicode text, and quoted multi-line text.
- Every record must have exactly as many fields as the header.
- Blank records are errors.
- The header must be present. A header with no data rows is valid and reports
  zero rows and zero totals. An empty file, or a file that contains only a BOM,
  is an error.
- The header must not contain blank names, duplicate names (after trimming), or
  control characters.
- You cannot request the same column twice, and you cannot request a column that
  is not in the header.

## Number rules

Selected numeric cells accept signed plain decimals, such as `-2`, `+3.5`, `.25`,
and `1.`. Outer whitespace around a cell is ignored.

- Each value supports at most **18 integer digits and 12 fractional digits**,
  counting leading and trailing zeros.
- Rejected: empty values, letters, `NaN`, infinity, exponent notation (`1e3`),
  grouping (`1,000`), currency symbols, and underscores.
- Negative values and zero are valid.
- Totals keep their exact fractional digits, even when a total is larger than any
  single cell can be. Output uses plain decimal notation with no grouping and no
  trailing fractional zeros.

## Errors and exit codes

Invalid input prints an `error:` message to stderr and exits with status `2`. It
prints no partial summary. The message names the file, the logical record number
(the header is record 1), and the numeric column where that applies. For example:

```text
error: demo\csv-summary\sample.csv: record 2, column 'item': expected a finite plain decimal (e.g. -2, +3.5 or .25; no commas or exponents)
```

A CSV parsing problem reports the physical line where it was found. A file that
cannot be read or is not UTF-8 is also reported with exit status `2`.

The program opens input files read-only and never modifies them.

## Run the tests

From the repository root:

```sh
python3 -m unittest discover -s demo/csv-summary -p 'test_*.py' -v
```

There are 15 tests, all expected to pass. The tests create temporary fixture files
inside `demo/csv-summary/` and remove them when each test finishes.

## Use it from Python

The importable function is `summarize(path, columns)`. It returns a `Summary` with:

- `rows`: the number of data records
- `totals`: an ordered tuple of `(column, canonical_decimal_string)` pairs

Validation failures raise `SummaryError`.

## Related

- Overview of all demos: [../README.md](../README.md)
- Repository overview: [../../README.md](../../README.md)
