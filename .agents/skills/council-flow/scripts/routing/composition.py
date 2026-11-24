"""Composable routing and bounded confidence calibration."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .contract import DecisionStatus, RouteDecision


class Chain:
    def __init__(self, first, fallback) -> None:
        self.first = first
        self.fallback = fallback

    def classify(self, text: str) -> RouteDecision:
        result = self.first.classify(text)
        if result.status is DecisionStatus.NO_MATCH:
            return self.fallback.classify(text)
        return result


class Merge:
    def __init__(self, routers) -> None:
        self.routers = tuple(routers)
        if not self.routers:
            raise ValueError("Merge requires at least one router")

    def classify(self, text: str) -> RouteDecision:
        decisions = tuple(router.classify(text) for router in self.routers)
        unavailable = next((item for item in decisions if item.status in {DecisionStatus.DISABLED, DecisionStatus.UNAVAILABLE}), None)
        if unavailable is not None:
            return unavailable
        matched = tuple(item for item in decisions if item.status is DecisionStatus.MATCHED)
        routes = {item.route for item in matched}
        if len(routes) > 1:
            base = max(matched, key=lambda item: item.confidence)
            return RouteDecision(
                status=DecisionStatus.AMBIGUOUS,
                route=None,
                confidence=base.confidence,
                threshold=base.threshold,
                margin=base.margin,
                router_version=base.router_version,
                route_config_sha256=base.route_config_sha256,
                input_sha256=base.input_sha256,
                encoder_id="merge-v1",
                reason_codes=("router_disagreement",),
            )
        if matched:
            return max(matched, key=lambda item: item.confidence)
        return max(decisions, key=lambda item: item.confidence)


@dataclass(frozen=True)
class Calibration:
    points: tuple[tuple[float, float], ...]
    version: str = "calibration-v1"

    def apply(self, confidence: float) -> float:
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not math.isfinite(confidence):
            raise ValueError("confidence must be finite")
        value = max(0.0, min(1.0, float(confidence)))
        if value <= self.points[0][0]:
            return self.points[0][1]
        for (left_x, left_y), (right_x, right_y) in zip(self.points, self.points[1:]):
            if value <= right_x:
                span = right_x - left_x
                fraction = 0.0 if span == 0 else (value - left_x) / span
                return max(0.0, min(1.0, left_y + fraction * (right_y - left_y)))
        return self.points[-1][1]


def fit_calibration(samples: Iterable[tuple[float, bool]]) -> Calibration:
    parsed = []
    for confidence, label in samples:
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not math.isfinite(confidence):
            raise ValueError("calibration confidence must be finite")
        if not isinstance(label, bool):
            raise ValueError("calibration labels must be boolean")
        parsed.append((max(0.0, min(1.0, float(confidence))), 1.0 if label else 0.0))
    if not parsed:
        raise ValueError("calibration requires at least one sample")
    parsed.sort()
    grouped = []
    for confidence, label in parsed:
        if grouped and grouped[-1][0] == confidence:
            previous_x, previous_sum, previous_count = grouped[-1]
            grouped[-1] = (previous_x, previous_sum + label, previous_count + 1)
        else:
            grouped.append((confidence, label, 1))
    points = [(confidence, total / count) for confidence, total, count in grouped]
    # Pool adjacent violations to keep the fitted mapping monotone.
    pooled = []
    for confidence, value in points:
        pooled.append([confidence, value, 1])
        while len(pooled) >= 2 and pooled[-2][1] > pooled[-1][1]:
            left, right = pooled[-2], pooled[-1]
            total = left[1] * left[2] + right[1] * right[2]
            count = left[2] + right[2]
            pooled[-2:] = [[right[0], total / count, count]]
    return Calibration(tuple((item[0], max(0.0, min(1.0, item[1]))) for item in pooled))
