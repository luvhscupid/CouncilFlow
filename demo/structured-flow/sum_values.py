"""Sum signed ASCII integers offline for CouncilFlow's structured rework demo."""
import argparse
import re


def integer(text):
    if not re.fullmatch(r"[+-]?[0-9]+", text):
        raise argparse.ArgumentTypeError("use a signed ASCII integer, for example -2 or 3")
    try:
        return int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("integer exceeds supported Python input bounds") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sum one or more signed ASCII integers, offline.")
    parser.add_argument("values", nargs="+", type=integer)
    args = parser.parse_args(argv)
    try:
        total = str(sum(args.values))
    except ValueError:
        parser.error("sum exceeds supported Python integer output bounds")
    print(total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
