"""Dependency-free route indexing and confidence-gated classification."""
from __future__ import annotations

import math
import re
from typing import Protocol

from .contract import (
    DecisionStatus,
    RouteConfig,
    RouteDecision,
    hash_input,
    hash_route_config,
)

_TOKEN = re.compile(r"[a-z0-9]+")


class Router(Protocol):
    def classify(self, text: str) -> RouteDecision:
        """Return a bounded, non-authoritative route decision."""


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.casefold()))


def _score(query: frozenset[str], example: frozenset[str]) -> float:
    if not query or not example:
        return 0.0
    overlap = len(query.intersection(example))
    return (overlap / max(len(query), len(example))) ** 2


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left or not right:
        raise ValueError("vectors must be nonempty and have equal dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)))


def _decision_common(config: RouteConfig, input_hash: str, encoder_id: str) -> dict:
    return {
        "threshold": config.threshold,
        "margin": config.margin,
        "router_version": config.version,
        "route_config_sha256": hash_route_config(config),
        "input_sha256": input_hash,
        "encoder_id": encoder_id,
    }


class LexicalRouter:
    """Deterministic lexical baseline used without optional dependencies."""

    def __init__(self, config: RouteConfig, *, enabled: bool = True) -> None:
        self.config = config
        self.enabled = enabled
        self._indexed = tuple(
            (route.name, tuple(_tokens(example) for example in route.examples))
            for route in config.routes
        )
        self._config_hash = hash_route_config(config)

    def classify(self, text: str) -> RouteDecision:
        input_hash = hash_input(text)
        common = {
            "threshold": self.config.threshold,
            "margin": self.config.margin,
            "router_version": self.config.version,
            "route_config_sha256": self._config_hash,
            "input_sha256": input_hash,
            "encoder_id": "lexical-v1",
        }
        if not self.enabled:
            return RouteDecision(DecisionStatus.DISABLED, None, 0.0, reason_codes=("router_disabled",), **common)

        query = _tokens(text)
        scores = sorted(
            ((max((_score(query, example) for example in examples), default=0.0), name) for name, examples in self._indexed),
            key=lambda item: (-item[0], item[1]),
        )
        best_score, best_name = scores[0]
        second_score = scores[1][0] if len(scores) > 1 else 0.0
        if best_score == 0.0:
            return RouteDecision(DecisionStatus.NO_MATCH, "unclassified", 0.0, reason_codes=("no_overlap",), **common)
        if best_score < self.config.threshold:
            return RouteDecision(DecisionStatus.NO_MATCH, "needs_information", best_score, reason_codes=("below_threshold",), **common)
        if best_score == second_score or best_score - second_score < self.config.margin:
            return RouteDecision(DecisionStatus.AMBIGUOUS, None, best_score, reason_codes=("insufficient_margin",), **common)
        return RouteDecision(DecisionStatus.MATCHED, best_name, best_score, reason_codes=("threshold_met",), **common)


class VectorRouter:
    """Vector router that treats encoder failure as an explicit unavailable state."""

    def __init__(self, config: RouteConfig, encoder, *, enabled: bool = True) -> None:
        self.config = config
        self.encoder = encoder
        self.enabled = enabled
        self._config_hash = hash_route_config(config)

    def classify(self, text: str) -> RouteDecision:
        input_hash = hash_input(text)
        encoder_id = getattr(self.encoder, "encoder_id", "custom-v1")
        common = _decision_common(self.config, input_hash, encoder_id)
        if not self.enabled:
            return RouteDecision(DecisionStatus.DISABLED, None, 0.0, reason_codes=("router_disabled",), **common)
        try:
            query = self.encoder.encode(text)
            scores = []
            for route in self.config.routes:
                route_score = max((_cosine(query, self.encoder.encode(example)) for example in route.examples), default=0.0)
                scores.append((route_score, route.name))
        except (ImportError, RuntimeError, TypeError, ValueError, StopIteration):
            return RouteDecision(DecisionStatus.UNAVAILABLE, None, 0.0, reason_codes=("encoder_failed",), **common)
        scores.sort(key=lambda item: (-item[0], item[1]))
        best_score, best_name = scores[0]
        second_score = scores[1][0] if len(scores) > 1 else 0.0
        if best_score < self.config.threshold:
            return RouteDecision(DecisionStatus.NO_MATCH, "needs_information", best_score, reason_codes=("below_threshold",), **common)
        if best_score == second_score or best_score - second_score < self.config.margin:
            return RouteDecision(DecisionStatus.AMBIGUOUS, None, best_score, reason_codes=("insufficient_margin",), **common)
        return RouteDecision(DecisionStatus.MATCHED, best_name, best_score, reason_codes=("threshold_met",), **common)
