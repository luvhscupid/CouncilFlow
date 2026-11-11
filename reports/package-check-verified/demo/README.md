# Receipt-calculator demonstration

## Finished application

Run the offline program from the repository root with Python 3.11 or newer:

```sh
python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg
```

```text
2 kg rice × Rp30,000 = Rp60,000
1 kg onions × Rp43,000 = Rp43,000
Total = Rp103,000
```

Repeat `--item NAME QUANTITY UNIT_PRICE UNIT` for each product. Supply a nonblank
unit such as `kg`, `box`, or `each`; quote names/units that contain spaces.
Quantities and prices are plain decimals without `Rp`, commas, or exponent
notation. Zero is accepted; negative, malformed, and non-finite inputs are
rejected with a usage error. Inputs support up to 18 integer and 12 fractional
digits each; larger precision is rejected explicitly. All accepted line totals
and sums are exact, and fractional rupiah remain visible (for example `Rp0.02`).
The comma thousands/dot decimal convention follows the Owner's examples.

```sh
python3 demo/receipt/receipt_calculator.py --help
python3 demo/receipt/receipt_calculator.py --item tea 3 12500 box --item sugar 1.5 14000 kg
python3 -m unittest discover -s demo/receipt -p 'test_*.py' -v
```

The second receipt totals `Rp58,500`. No network access or third-party packages
are needed. Importable API: `ProductEntry(name, quantity, unit_price, unit="")`,
its `line_total` property, `grand_total(entries)`, and `format_rupiah(Decimal)`.
Use strings, integers, or Decimal inputs; floats are rejected to avoid silently
introducing binary floating-point values. The Python API permits an omitted
unit; the CLI requires the unit argument.

## Preserved failing baseline

`starter/` is an intentionally incomplete but valid offline Python fixture.
Its `ProductEntry.line_total` currently ignores quantity, so the executable
rice/onions calculation test fails with an actual wrong result. Keep this
fixture unchanged to reproduce the starting defect:

```sh
python3 -m unittest discover -s demo/starter -p 'test_*.py' -v
python3 demo/starter/receipt_calculator.py
```

The finished program lives separately in `demo/receipt/`, leaving `starter/` as
baseline. The Planner froze CF-DEMO-001 before the fresh Worker implemented it.

Starter API available for extension:

- `ProductEntry(name, quantity, unit_price, unit="")`: decimal string quantities
  and prices are appropriate inputs; quantities and prices are stored as Decimal.
- `ProductEntry.line_total`: quantity times unit price, currently defective.
- `grand_total(entries)`: sum entry totals.
- `format_rupiah(amount)`: `Rp` prefix and comma thousands separator; retain
  fractional money visibly where needed. The Owner's example uses `Rp103,000`.
- `main()`: executable program entry point, currently only the fixed sample.

The finished program must accept multiple actual input entries, validate negative
quantities and invalid prices (including non-finite values), use Decimal-safe
arithmetic, show line totals and the grand total in rupiah, work offline, and have
executable automated tests. The implementation must not hardcode the sample.
The Manager's run reports must identify the actual final path, invocation,
Planner/Worker/Tester/Reviewer sessions, test outputs, failures/repairs, and final
acceptance evidence. The fixture's expected failure is not a final app failure.
