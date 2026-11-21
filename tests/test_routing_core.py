import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))

from routing.contract import DecisionStatus, validate_route_config
from routing.core import LexicalRouter


class RoutingCoreTests(unittest.TestCase):
    def config(self, **overrides):
        value = {
            "version": "routing-v1",
            "threshold": 0.5,
            "margin": 0.2,
            "routes": [
                {"name": "documentation_only", "examples": ["write project documentation"], "metadata": {}},
                {"name": "security_sensitive", "examples": ["audit authentication security"], "metadata": {}},
            ],
        }
        value.update(overrides)
        return validate_route_config(value)

    def test_exact_route_match(self):
        decision = LexicalRouter(self.config()).classify("write project documentation")
        self.assertEqual(decision.status, DecisionStatus.MATCHED)
        self.assertEqual(decision.route, "documentation_only")
        self.assertEqual(decision.confidence, 1.0)
        self.assertIn("threshold_met", decision.reason_codes)

    def test_no_match_returns_unclassified(self):
        decision = LexicalRouter(self.config()).classify("make tea for the team")
        self.assertEqual(decision.status, DecisionStatus.NO_MATCH)
        self.assertEqual(decision.route, "unclassified")
        self.assertIn("no_overlap", decision.reason_codes)

    def test_low_confidence_returns_needs_information(self):
        decision = LexicalRouter(self.config()).classify("write project")
        self.assertEqual(decision.status, DecisionStatus.NO_MATCH)
        self.assertEqual(decision.route, "needs_information")
        self.assertIn("below_threshold", decision.reason_codes)

    def test_small_margin_returns_ambiguous(self):
        config = self.config(
            threshold=0.2,
            margin=0.3,
            routes=[
                {"name": "docs", "examples": ["write project documentation"], "metadata": {}},
                {"name": "security", "examples": ["write project security"], "metadata": {}},
            ],
        )
        decision = LexicalRouter(config).classify("write project")
        self.assertEqual(decision.status, DecisionStatus.AMBIGUOUS)
        self.assertIsNone(decision.route)
        self.assertIn("insufficient_margin", decision.reason_codes)

    def test_route_order_does_not_break_ties(self):
        routes = [
            {"name": "first", "examples": ["shared task alpha"], "metadata": {}},
            {"name": "second", "examples": ["shared task beta"], "metadata": {}},
        ]
        decision = LexicalRouter(self.config(routes=routes, threshold=0.1, margin=0.0)).classify("shared task")
        self.assertEqual(decision.status, DecisionStatus.AMBIGUOUS)
        self.assertIsNone(decision.route)

    def test_disabled_router_returns_disabled(self):
        decision = LexicalRouter(self.config(), enabled=False).classify("write project documentation")
        self.assertEqual(decision.status, DecisionStatus.DISABLED)
        self.assertIsNone(decision.route)
        self.assertIn("router_disabled", decision.reason_codes)

    def test_decision_keeps_hashes_from_config_and_input(self):
        router = LexicalRouter(self.config())
        decision = router.classify("write project documentation")
        self.assertEqual(len(decision.route_config_sha256), 64)
        self.assertEqual(len(decision.input_sha256), 64)
        self.assertNotIn("write project documentation", repr(decision))


if __name__ == "__main__":
    unittest.main()
