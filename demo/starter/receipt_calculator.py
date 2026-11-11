"""Valid, intentionally incomplete receipt fixture; see demo/README.md."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class ProductEntry:
    name: str
    quantity: Decimal
    unit_price: Decimal
    unit: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", Decimal(str(self.quantity)))
        object.__setattr__(self, "unit_price", Decimal(str(self.unit_price)))

    @property
    def line_total(self) -> Decimal:
        # Deliberate starter defect: ignores quantity. A fresh Worker must fix it.
        return self.unit_price


def grand_total(entries: Iterable[ProductEntry]) -> Decimal:
    return sum((entry.line_total for entry in entries), Decimal("0"))


def format_rupiah(amount: Decimal) -> str:
    return f"Rp{amount:,.0f}"


def main() -> None:
    entries = [ProductEntry("rice", "2", "30000", "kg"),
               ProductEntry("onions", "1", "43000", "kg")]
    for entry in entries:
        print(f"{entry.quantity} {entry.unit} {entry.name} × "
              f"{format_rupiah(entry.unit_price)} = {format_rupiah(entry.line_total)}")
    print(f"Total = {format_rupiah(grand_total(entries))}")


if __name__ == "__main__":
    main()
