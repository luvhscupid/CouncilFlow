"""Sum a named numeric CSV column from the command line."""
import argparse
import csv
from decimal import Decimal, DecimalException
import sys


def sum_column(path, column):
    """Return the Decimal sum, rejecting missing or nonfinite numeric values."""
    total = Decimal(0)
    with open(path, newline="", encoding="utf-8-sig") as source:
        rows = csv.DictReader(source, strict=True)
        if rows.fieldnames is None or column not in rows.fieldnames:
            raise ValueError(f"Column {column!r} is missing from the CSV header")
        for row in rows:
            raw = row[column]
            try:
                value = Decimal(raw.strip()) if raw is not None else Decimal("NaN")
            except DecimalException:
                raise ValueError(
                    f"Nonnumeric value {raw!r} in column {column!r} at CSV line {rows.line_num}"
                ) from None
            if not value.is_finite():
                raise ValueError(
                    f"Expected a finite numeric value in column {column!r} at CSV line {rows.line_num}: {raw!r}"
                )
            total += value
    return total

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", metavar="CSV_PATH")
    parser.add_argument("column", metavar="COLUMN")
    args = parser.parse_args(argv)
    try:
        total = sum_column(args.path, args.column)
    except (OSError, UnicodeError, csv.Error, ValueError, DecimalException) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    display = format(total, "f")
    if "." in display:
        display = display.rstrip("0").rstrip(".")
    print(display)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
