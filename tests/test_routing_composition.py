import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))

from routing.composition import Chain, Merge, fit_calibration
from routing.contract import DecisionStatus, RouteDecision, validate_route_config, hash_input, hash_route_config


class StubRouter:
    def __init__(self, decision):
        self.decision = decision

    def classify(self, text):
        return self.decision


def decision(status, route=None, confidence=0.0, encoder_id="stub-v1"):
    config = validate_route_config({
        "version": "routing-v1", "threshold": 0.5, "margin": 0.1,
        "routes": [{"name": "docs", "examples": ["docs"], "metadata": {}}],
    })
    return RouteDecision(
        status=status, route=route, confidence=confidence,
        threshold=config.threshold, margin=config.margin, router_version=config.version,
        route_config_sha256=hash_route_config(config), input_sha256=hash_input("input"),
        encoder_id=encoder_id, reason_codes=("fixture",),
    )


class RoutingCompositionTests(unittest.TestCase):
    def test_chain_falls_back_only_on_no_match(self):
        first = StubRouter(decision(DecisionStatus.NO_MATCH, "unclassified"))
        fallback = StubRouter(decision(DecisionStatus.MATCHED, "docs", 0.9, "fallback-v1"))
        self.assertEqual(Chain(first, fallback).classify("input").route, "docs")

    def test_chain_does_not_hide_unavailable_encoder(self):
        first = StubRouter(decision(DecisionStatus.UNAVAILABLE))
        fallback = StubRouter(decision(DecisionStatus.MATCHED, "docs", 0.9))
        self.assertEqual(Chain(first, fallback).classify("input").status, DecisionStatus.UNAVAILABLE)

    def test_merge_preserves_disagreement(self):
        left = StubRouter(decision(DecisionStatus.MATCHED, "docs", 0.9, "left-v1"))
        right = StubRouter(decision(DecisionStatus.MATCHED, "security", 0.9, "right-v1"))
        result = Merge((left, right)).classify("input")
        self.assertEqual(result.status, DecisionStatus.AMBIGUOUS)
        self.assertIsNone(result.route)
        self.assertIn("router_disagreement", result.reason_codes)

    def test_calibration_is_deterministic(self):
        calibration = fit_calibration(((0.0, False), (0.5, True), (1.0, True)))
        self.assertEqual(calibration.apply(0.5), calibration.apply(0.5))
        self.assertGreaterEqual(calibration.apply(-2.0), 0.0)
        self.assertLessEqual(calibration.apply(2.0), 1.0)

    def test_empty_calibration_fails_closed(self):
        with self.assertRaises(ValueError):
            fit_calibration(())


if __name__ == "__main__":
    unittest.main()
