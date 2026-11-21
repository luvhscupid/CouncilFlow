import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))

from routing.contract import (
    DecisionStatus,
    Route,
    RouteDecision,
    RouteConfig,
    hash_input,
    hash_route_config,
    validate_route_config,
)


class RoutingContractTests(unittest.TestCase):
    def config(self, **overrides):
        value = {
            "version": "routing-v1",
            "threshold": 0.6,
            "margin": 0.1,
            "routes": [
                {"name": "documentation_only", "examples": ["write docs"], "metadata": {"kind": "docs"}},
                {"name": "security_sensitive", "examples": ["audit auth"], "metadata": {"kind": "security"}},
            ],
        }
        value.update(overrides)
        return value

    def test_rejects_oversized_or_non_text_input(self):
        with self.assertRaises(ValueError):
            hash_input("x" * 8193)
        with self.assertRaises(ValueError):
            hash_input(42)
        with self.assertRaises(ValueError):
            hash_input("bad\ud800")

    def test_rejects_duplicate_route_names_and_examples(self):
        duplicate_name = self.config(routes=[
            {"name": "same", "examples": ["one"], "metadata": {}},
            {"name": "same", "examples": ["two"], "metadata": {}},
        ])
        with self.assertRaises(ValueError):
            validate_route_config(duplicate_name)

        duplicate_example = self.config(routes=[
            {"name": "one", "examples": ["same"], "metadata": {}},
            {"name": "two", "examples": ["same"], "metadata": {}},
        ])
        with self.assertRaises(ValueError):
            validate_route_config(duplicate_example)

    def test_rejects_invalid_thresholds(self):
        for key, value in (("threshold", -0.1), ("threshold", 1.1), ("margin", -0.1), ("margin", 1.1),
                           ("threshold", math.nan), ("margin", math.inf)):
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    validate_route_config(self.config(**{key: value}))

    def test_config_hash_is_stable(self):
        first = validate_route_config(self.config())
        second = validate_route_config({
            "routes": list(reversed(self.config()["routes"])),
            "margin": 0.1,
            "threshold": 0.6,
            "version": "routing-v1",
        })
        self.assertEqual(hash_route_config(first), hash_route_config(second))
        changed = validate_route_config(self.config(threshold=0.7))
        self.assertNotEqual(hash_route_config(first), hash_route_config(changed))

    def test_decision_does_not_store_raw_input(self):
        config = validate_route_config(self.config())
        decision = RouteDecision(
            status=DecisionStatus.NO_MATCH,
            route=None,
            confidence=0.0,
            threshold=config.threshold,
            margin=config.margin,
            router_version=config.version,
            route_config_sha256=hash_route_config(config),
            input_sha256=hash_input("private task text"),
            encoder_id="lexical-v1",
            reason_codes=("below_threshold",),
        )
        self.assertNotIn("private task text", repr(decision))
        self.assertEqual(decision.input_sha256, hash_input("private task text"))
        self.assertEqual(decision.status, DecisionStatus.NO_MATCH)

    def test_value_objects_are_immutable_and_valid(self):
        route = Route(name="docs", examples=("write docs",), metadata={"kind": "docs"})
        config = RouteConfig(routes=(route,), threshold=0.5, margin=0.1, version="v1")
        with self.assertRaises((AttributeError, TypeError)):
            config.threshold = 0.9


if __name__ == "__main__":
    unittest.main()
