"""Count CSV records and sum selected columns exactly, using only local reads."""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence
import unicodedata


_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
_FRACTION_DIGITS = 12
_SCALE = 10 ** _FRACTION_DIGITS


class SummaryError(ValueError):
    """A user-actionable input error, with file and available record context."""


@dataclass(frozen=True)
class Summary:
    rows: int
    totals: tuple[tuple[str, str], ...]


def _numeric_units(cell: str) -> int:
    """Parse bounded plain decimals as exact integer units of 10^-12."""
    text = cell.strip()
    if not _DECIMAL.fullmatch(text):
        raise ValueError("expected a finite plain decimal (e.g. -2, +3.5 or .25; no commas or exponents)")
    sign = -1 if text.startswith("-") else 1
    unsigned = text.lstrip("+-")
    integer, _, fraction = unsigned.partition(".")
    if len(integer) > 18 or len(fraction) > _FRACTION_DIGITS:
        raise ValueError("supports at most 18 integer digits and 12 fractional digits, including zeros")
    return sign * (int(integer or "0") * _SCALE + int(fraction.ljust(_FRACTION_DIGITS, "0")))


def _format_units(units: int) -> str:
    integer, fraction = divmod(abs(units), _SCALE)
    suffix = f"{fraction:012d}".rstrip("0")
    return ("-" if units < 0 else "") + str(integer) + ("." + suffix if suffix else "")


def _headers(raw: list[str], path: Path) -> list[str]:
    if not raw:
        raise SummaryError(f"{path}: record 1: missing CSV header")
    names = []
    for position, value in enumerate(raw, start=1):
        if any(unicodedata.category(character) == "Cc" for character in value):
            raise SummaryError(f"{path}: record 1: header {position} contains a control character")
        name = value.strip()
        if not name:
            raise SummaryError(f"{path}: record 1: header {position} is blank")
        if name in names:
            raise SummaryError(f"{path}: record 1: duplicate normalized header {name!r}")
        names.append(name)
    return names


def summarize(path: str | Path, columns: Sequence[str]) -> Summary:
    """Read a UTF-8 CSV and return a count and ordered, canonical decimal totals.

    Every cell has bounded precision, so integer fixed-point accumulation avoids
    binary floating-point and ambient Decimal context rounding entirely. Totals
    may grow beyond the input-cell bounds without losing fractional digits.
    """
    source = Path(path)
    selected = tuple(columns)
    if not selected:
        raise SummaryError(f"{source}: select at least one numeric column with --column")
    if len(set(selected)) != len(selected):
        raise SummaryError(f"{source}: duplicate requested column; select each column once")
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            try:
                raw_header = next(reader)
            except StopIteration:
                raise SummaryError(f"{source}: missing CSV header (empty file)") from None
            header = _headers(raw_header, source)
            for name in selected:
                if name not in header:
                    raise SummaryError(f"{source}: requested column {name!r} is not in the header")
            indexes = [header.index(name) for name in selected]
            totals = [0] * len(selected)
            count = 0
            for record, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    raise SummaryError(
                        f"{source}: record {record}: expected {len(header)} fields, found {len(row)}"
                    )
                for position, (name, index) in enumerate(zip(selected, indexes)):
                    try:
                        totals[position] += _numeric_units(row[index])
                    except ValueError as exc:
                        raise SummaryError(f"{source}: record {record}, column {name!r}: {exc}") from exc
                count += 1
            return Summary(count, tuple((name, _format_units(total)) for name, total in zip(selected, totals)))
    except csv.Error as exc:
        raise SummaryError(f"{source}: CSV parsing error near physical line {reader.line_num}: {exc}") from exc
    except UnicodeError as exc:
        raise SummaryError(f"{source}: invalid UTF-8 input; save the file as UTF-8: {exc}") from exc
    except OSError as exc:
        raise SummaryError(f"{source}: cannot read input: {exc.strerror or str(exc)}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Count CSV data records and print exact totals for selected numeric columns, offline.",
        epilog=(
            "Use comma-delimited UTF-8 CSV with a unique nonblank header (optional BOM). "
            "Repeat --column for each numeric column; other columns may contain text. "
            "Numbers are signed plain decimals, up to 18 integer and 12 fractional digits including zeros; "
            "no grouping, currency symbols or exponent notation. Header-only files yield zero totals; "
            "empty files and blank records are errors. Inputs are never modified. "
            "Example: csv_summarizer.py sample.csv --column amount --column quantity"
        ),
    )
    parser.add_argument("input", metavar="INPUT", help="local comma-delimited CSV file with a header")
    parser.add_argument(
        "--column", action="append", required=True, metavar="NAME",
        help="numeric header name after trimming outer header whitespace; repeat for multiple totals",
    )
    args = parser.parse_args(argv)
    try:
        result = summarize(args.input, args.column)
    except SummaryError as exc:
        parser.exit(2, f"error: {exc}\n")
    lines = [f"Rows: {result.rows}"]
    lines.extend(f"Total {name}: {total}" for name, total in result.totals)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
