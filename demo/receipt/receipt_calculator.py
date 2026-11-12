"""Offline receipt calculator using exact, bounded Decimal inputs."""

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, MAX_EMAX, MIN_EMIN, localcontext
import re
import sys
from typing import Iterable


MAX_INTEGER_DIGITS = 18
MAX_FRACTION_DIGITS = 12
_INPUT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")
_PRODUCT_PRECISION = 2 * (MAX_INTEGER_DIGITS + MAX_FRACTION_DIGITS)


def _number(value: object, label: str) -> Decimal:
    """Parse a nonnegative plain decimal without float conversion or rounding."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{label} must be a plain decimal string, integer, or Decimal")
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, (str, int)):
        text = str(value).strip()
        if len(text) > 100 or not _INPUT.fullmatch(text):
            raise ValueError(f"{label} must be a plain decimal, e.g. 2 or 30000.50 (no Rp or commas)")
        try:
            number = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"{label} must be a valid decimal") from exc
    else:
        raise ValueError(f"{label} must be a plain decimal string, integer, or Decimal")
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    if number < 0:
        raise ValueError(f"{label} must be zero or greater")
    if number.is_zero():
        return Decimal(0)
    integer_digits = max(number.adjusted() + 1, 0)
    fraction_digits = max(-number.as_tuple().exponent, 0)
    if integer_digits > MAX_INTEGER_DIGITS or fraction_digits > MAX_FRACTION_DIGITS:
        raise ValueError(
            f"{label} supports at most {MAX_INTEGER_DIGITS} integer digits and "
            f"{MAX_FRACTION_DIGITS} fractional digits"
        )
    return number


def _label(value: object, field: str, *, optional: bool = False) -> str:
    if not isinstance(value, str) or (not value.strip() and not optional):
        raise ValueError(f"{field} must be nonblank text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field} must not contain control characters")
    return value.strip()


@dataclass(frozen=True)
class ProductEntry:
    name: str
    quantity: Decimal
    unit_price: Decimal
    unit: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _label(self.name, "product name"))
        object.__setattr__(self, "unit", _label(self.unit, "unit", optional=self.unit == ""))
        object.__setattr__(self, "quantity", _number(self.quantity, "quantity"))
        object.__setattr__(self, "unit_price", _number(self.unit_price, "unit price"))

    @property
    def line_total(self) -> Decimal:
        with localcontext() as context:
            context.prec = _PRODUCT_PRECISION
            context.Emax, context.Emin, context.clamp = MAX_EMAX, MIN_EMIN, 0
            return self.quantity * self.unit_price


def grand_total(entries: Iterable[ProductEntry]) -> Decimal:
    totals = [entry.line_total for entry in entries]
    with localcontext() as context:
        # Exact products need at most 60 places; summation adds at most digits(n).
        context.prec = _PRODUCT_PRECISION + len(str(len(totals))) + 1
        context.Emax, context.Emin, context.clamp = MAX_EMAX, MIN_EMIN, 0
        return sum(totals, Decimal(0))


def format_rupiah(amount: Decimal) -> str:
    if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0:
        raise ValueError("amount must be a finite nonnegative Decimal")
    if amount.is_zero():
        return "Rp0"
    text = format(amount, ",f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "Rp" + text


def _plain(number: Decimal) -> str:
    text = format(number, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


class _VersionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None) -> None:
        sys.stdout.buffer.write(b"1.0.0\n")
        parser.exit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calculate an offline receipt in Indonesian rupiah using exact decimal arithmetic.",
        epilog=(
            "Repeat --item for each product. Use plain decimals without Rp, commas, or exponent notation; "
            "up to 18 integer and 12 fractional digits per quantity/price. Zero is accepted. "
            "Quote names/units containing spaces. Example: --item rice 2 30000 kg --item onions 1 43000 kg"
        ),
    )
    parser.add_argument("--version", action=_VersionAction, nargs=0, help="show program version and exit")
    parser.add_argument(
        "--item", action="append", nargs=4, required=True,
        metavar=("NAME", "QUANTITY", "UNIT_PRICE", "UNIT"),
        help="add one product; UNIT is a nonblank label such as kg or each",
    )
    args = parser.parse_args(argv)
    entries = []
    for index, (name, quantity, price, unit) in enumerate(args.item, start=1):
        try:
            if not unit.strip():
                raise ValueError("unit must be nonblank text")
            entries.append(ProductEntry(name, quantity, price, unit))
        except ValueError as exc:
            parser.error(f"item {index}: {exc}")
    for entry in entries:
        print(f"{_plain(entry.quantity)} {entry.unit} {entry.name} × "
              f"{format_rupiah(entry.unit_price)} = {format_rupiah(entry.line_total)}")
    print(f"Total = {format_rupiah(grand_total(entries))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
