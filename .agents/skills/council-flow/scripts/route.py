"""Emit one optional, non-authoritative CouncilFlow route decision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))

from routing.contract import RouteDecision, validate_route_config
from routing.core import LexicalRouter, VectorRouter
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--router", choices=("lexical", "vector"), default="lexical")
    parser.add_argument("--encoder", default="hash:64")
    parser.add_argument("--disabled", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = validate_route_config(json.loads(args.config.read_text(encoding="utf-8")))
        text = _read_input(args.input_path)
        decision = _build_router(args.router, config, not args.disabled, args.encoder).classify(text)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(_decision_json(decision), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
