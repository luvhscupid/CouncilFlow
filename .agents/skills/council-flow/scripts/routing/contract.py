"""Bounded, non-authoritative value contracts for optional CouncilFlow routing."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import re
from types import MappingProxyType
from typing import Any, Mapping

MAX_TEXT_LENGTH = 8192
MAX_ROUTES = 128
MAX_EXAMPLES_PER_ROUTE = 128
MAX_METADATA_ITEMS = 32
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")


class DecisionStatus(str, Enum):
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    NO_MATCH = "NO_MATCH"
    DISABLED = "DISABLED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class Route:
    name: str
    examples: tuple[str, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        _identifier(self.name, "route name")
        if not self.examples or len(self.examples) > MAX_EXAMPLES_PER_ROUTE:
            raise ValueError("route examples must be nonempty and bounded")
        normalized = tuple(_text(item, "route example") for item in self.examples)
        if len(set(normalized)) != len(normalized):
            raise ValueError("route examples must be unique")
        if not isinstance(self.metadata, Mapping) or len(self.metadata) > MAX_METADATA_ITEMS:
            raise ValueError("route metadata must be a bounded mapping")
        object.__setattr__(self, "examples", normalized)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class RouteConfig:
    routes: tuple[Route, ...]
    threshold: float
    margin: float
    version: str

    def __post_init__(self) -> None:
        if not self.routes or len(self.routes) > MAX_ROUTES:
            raise ValueError("route config must contain a bounded nonempty route set")
        if len({route.name for route in self.routes}) != len(self.routes):
            raise ValueError("route names must be unique")
        if not 0.0 <= self.threshold <= 1.0 or not math.isfinite(self.threshold):
            raise ValueError("threshold must be finite and between 0 and 1")
        if not 0.0 <= self.margin <= 1.0 or not math.isfinite(self.margin):
            raise ValueError("margin must be finite and between 0 and 1")
        _identifier(self.version, "route config version")


@dataclass(frozen=True)
class RouteDecision:
    status: DecisionStatus
    route: str | None
    confidence: float
    threshold: float
    margin: float
    router_version: str
    route_config_sha256: str
    input_sha256: str
    encoder_id: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.status, DecisionStatus):
            raise ValueError("status must be a DecisionStatus")
        if self.route is not None:
            _identifier(self.route, "decision route")
        for value, label in ((self.confidence, "confidence"), (self.threshold, "threshold"), (self.margin, "margin")):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be finite and between 0 and 1")
        _identifier(self.router_version, "router version")
        _digest(self.route_config_sha256, "route config hash")
        _digest(self.input_sha256, "input hash")
        _identifier(self.encoder_id, "encoder id")
        if not isinstance(self.reason_codes, tuple) or any(not _identifier(item, "reason code") for item in self.reason_codes):
            raise ValueError("reason codes must be a tuple of identifiers")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT_LENGTH:
        raise ValueError(f"{label} must be a bounded nonempty string")
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label} must be valid UTF-8") from exc
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a bounded identifier")
    return value


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def hash_input(text: str) -> str:
    return hashlib.sha256(_text(text, "input").encode("utf-8")).hexdigest()


def _route_payload(route: Route) -> dict[str, Any]:
    return {"name": route.name, "examples": sorted(route.examples), "metadata": dict(sorted(route.metadata.items()))}


def hash_route_config(config: RouteConfig) -> str:
    payload = {
        "version": config.version,
        "threshold": config.threshold,
        "margin": config.margin,
        "routes": sorted((_route_payload(route) for route in config.routes), key=lambda route: route["name"]),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_route_config(value: Any) -> RouteConfig:
    if not isinstance(value, Mapping):
        raise ValueError("route config must be an object")
    required = {"version", "threshold", "margin", "routes"}
    if set(value) != required:
        raise ValueError("route config has unexpected or missing fields")
    routes_value = value["routes"]
    if not isinstance(routes_value, list):
        raise ValueError("routes must be an array")
    routes = []
    examples_seen: set[str] = set()
    for item in routes_value:
        if not isinstance(item, Mapping) or set(item) != {"name", "examples", "metadata"}:
            raise ValueError("each route requires name, examples, and metadata")
        examples = item["examples"]
        if not isinstance(examples, list):
            raise ValueError("route examples must be an array")
        route = Route(item["name"], tuple(examples), item["metadata"])
        if examples_seen.intersection(route.examples):
            raise ValueError("route examples must be unique across routes")
        examples_seen.update(route.examples)
        routes.append(route)
    return RouteConfig(tuple(routes), value["threshold"], value["margin"], value["version"])
