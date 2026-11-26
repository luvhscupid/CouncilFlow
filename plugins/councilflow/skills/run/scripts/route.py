"""Optional, non-authoritative CouncilFlow routing hint: classify, then record the Manager's choice.

  route.py [classify] --config routes.json [--input task.txt]       print the hint JSON
  route.py record   --config ... --action accepted|ignored|blocked --out rec.json
  route.py override --config ... --reason "why" --out rec.json

record and override classify the same input again (the routers are deterministic), refuse a
--hint file that differs from that result, and write the sealed decision record once.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))
# Roles must not find __pycache__ written into the installed skill folder.
sys.dont_write_bytecode = True

from routing.contract import RouteDecision, validate_route_config
from routing.core import LexicalRouter, VectorRouter
from routing.decision import build_decision_record, override_route
from routing.encoders import FastEmbedEncoder, HashEncoder

MAX_INPUT_CHARS = 8192


def _decision_json(decision: RouteDecision) -> dict:
    return {
        "status": decision.status.value,
        "route": decision.route,
        "confidence": decision.confidence,
        "threshold": decision.threshold,
        "margin": decision.margin,
        "router_version": decision.router_version,
        "route_config_sha256": decision.route_config_sha256,
        "input_sha256": decision.input_sha256,
        "encoder_id": decision.encoder_id,
        "reason_codes": list(decision.reason_codes),
    }


def _read_input(path: str | None) -> str:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_INPUT_CHARS:
        raise ValueError(f"routing input must be nonempty and bounded to {MAX_INPUT_CHARS} characters")
    return raw


def _build_router(kind: str, config, enabled: bool, encoder_name: str):
    if kind == "lexical":
        return LexicalRouter(config, enabled=enabled)
    if kind != "vector":
        raise ValueError("router must be lexical or vector")
    if encoder_name.startswith("fastembed:"):
        encoder = FastEmbedEncoder(encoder_name.split(":", 1)[1])
    elif encoder_name.startswith("hash:"):
        encoder = HashEncoder(int(encoder_name.split(":", 1)[1]))
    else:
        raise ValueError("encoder must be hash:<dimension> or fastembed:<model>")
    return VectorRouter(config, encoder, enabled=enabled)


COMMANDS = ("classify", "record", "override")


def _parser(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"route.py {command}" if command != "classify" else "route.py",
                                     description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--router", choices=("lexical", "vector"), default="lexical")
    parser.add_argument("--encoder", default="hash:64")
    parser.add_argument("--disabled", action="store_true")
    if command != "classify":
        if command == "record":
            parser.add_argument("--action", required=True, choices=("accepted", "ignored", "blocked"))
        else:
            parser.add_argument("--reason", required=True)
        parser.add_argument("--hint", type=Path, help="the hint JSON the Manager saw; must match exactly")
        parser.add_argument("--evidence-ref")
        parser.add_argument("--out", required=True, type=Path, help="new file for the sealed record; never overwritten")
    return parser


def _write_once(path: Path, record: dict) -> None:
    data = json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(data)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv.pop(0) if argv and argv[0] in COMMANDS else "classify"
    args = _parser(command).parse_args(argv)
    try:
        config = validate_route_config(json.loads(args.config.read_text(encoding="utf-8")))
        text = _read_input(args.input_path)
        decision = _build_router(args.router, config, not args.disabled, args.encoder).classify(text)
        if command == "classify":
            print(json.dumps(_decision_json(decision), sort_keys=True, separators=(",", ":")))
            return 0
        if args.hint is not None and json.loads(args.hint.read_text(encoding="utf-8")) != _decision_json(decision):
            raise ValueError("hint does not match a fresh classification of the same input and config")
        if args.out.exists() or args.out.is_symlink():
            raise ValueError(f"{args.out} already exists; decision records are never overwritten")
        if command == "record":
            record = build_decision_record(decision, manager_action=args.action, evidence_ref=args.evidence_ref)
        else:
            record = override_route(build_decision_record(decision, manager_action="accepted",
                                                          evidence_ref=args.evidence_ref), args.reason)
        _write_once(args.out, record)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"saved": str(args.out), "manager_action": record["manager_action"],
                      "record_sha256": record["record_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
