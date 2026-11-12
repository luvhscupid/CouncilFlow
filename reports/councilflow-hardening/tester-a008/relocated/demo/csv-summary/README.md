# Offline CSV summarizer

Run with Python 3.11 or newer from the repository root:

```sh
python3 demo/csv-summary/csv_summarizer.py demo/csv-summary/sample.csv --column amount --column quantity
```

```text
Rows: 3
Total amount: 30
Total quantity: 6
```

Supply a local file and at least one `--column NAME`. Repeat `--column` for more
totals; output follows the requested order. Select numeric columns explicitly:
other columns can contain arbitrary text or be empty. Repeated selections and
unknown names are errors. Names are case-sensitive and match the header after
its outer whitespace is removed. Blank, duplicate normalized, and control-character
headers are rejected.

The file must be comma-delimited UTF-8 CSV, optionally with a UTF-8 BOM. Normal
double-quote CSV quoting, escaped quotes, CRLF records, Unicode descriptors, and
quoted multiline text work. CSV parsing uses Python's strict CSV reader; no
dialect guessing or custom stricter parser is used. Every logical record must
have exactly the header's field count. Blank records are errors. An empty or
BOM-only file is invalid; a valid header-only file reports zero rows/totals.

Selected numeric cells accept signed plain ASCII decimals, including `-2`,
`+3.5`, `.25`, and `1.`. Outer cell whitespace is ignored. Each value supports
at most **18 integer digits and 12 fractional digits**, including leading and
trailing zeros. Empty, malformed, non-finite (`NaN`/infinity), exponent,
grouping (`1,000`), currency and underscore notation are rejected. Negative
values and zero are valid. Unsupported precision is rejected explicitly.

Totals retain exact accepted fractional values, even when sums exceed the
individual-cell magnitude limit. Integer fixed-point arithmetic avoids binary
floating-point and Decimal context rounding. Output uses plain decimal notation
without grouping, redundant fractional zeros, or negative zero.

No network access, extra packages, API keys, or services are required. The
program opens input files read-only. Invalid input exits with status 2, an
actionable stderr error and no partial summary. Data errors identify the file,
logical record number (header is record 1), and numeric column where applicable.
CSV parser errors label their physical-line context separately.

```sh
python3 demo/csv-summary/csv_summarizer.py --help
python3 -m unittest discover -s demo/csv-summary -p 'test_*.py' -v
```

The tests create and clean temporary fixtures inside this demo directory. The
importable `summarize(path, columns)` function returns a `Summary` containing
`rows` and an ordered tuple of `(column, canonical_decimal_string)` totals;
validation failures raise `SummaryError`.
