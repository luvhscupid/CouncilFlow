import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))

from routing.contract import DecisionStatus, RouteDecision, validate_route_config, hash_input, hash_route_config
from routing.decision import accept_route, build_decision_record, override_route, validate_decision_record


class RoutingDecisionTests(unittest.TestCase):
    def setUp(self):
        config = validate_route_config({
            "version": "routing-v1", "threshold": 0.5, "margin": 0.1,
            "routes": [{"name": "docs", "examples": ["docs"], "metadata": {}}],
        })
        self.decision = RouteDecision(
            status=DecisionStatus.MATCHED, route="docs", confidence=0.9,
            threshold=config.threshold, margin=config.margin, router_version=config.version,
            route_config_sha256=hash_route_config(config), input_sha256=hash_input("private task"),
            encoder_id="lexical-v1", reason_codes=("threshold_met",),
        )

    def test_record_contains_only_hashes_and_bounded_metadata(self):
        record = build_decision_record(self.decision, manager_action="ignored")
        serialized = repr(record)
        self.assertNotIn("private task", serialized)
        self.assertNotIn("api_key", serialized.lower())
        self.assertEqual(record["input_sha256"], self.decision.input_sha256)
        validate_decision_record(record)

    def test_manager_acceptance_is_explicit(self):
        record = build_decision_record(self.decision, manager_action="ignored")
        accepted = accept_route(record)
        self.assertEqual(accepted["manager_action"], "accepted")
        self.assertEqual(accepted["route"], "docs")

    def test_manager_override_requires_reason(self):
        record = build_decision_record(self.decision, manager_action="ignored")
        with self.assertRaises(ValueError):
            override_route(record, "")
        overridden = override_route(record, "Manager chose the documented scope")
        self.assertEqual(overridden["manager_action"], "overridden")
        self.assertEqual(overridden["manager_reason"], "Manager chose the documented scope")

    def test_route_cannot_authorize_dispatch(self):
        record = build_decision_record(self.decision, manager_action="accepted")
        self.assertNotIn("dispatch", record)
        self.assertNotIn("authorization", record)
        self.assertNotIn("tool", record)
        self.assertNotIn("model", record)

    def test_changed_config_invalidates_record(self):
        record = build_decision_record(self.decision, manager_action="ignored")
        record["route_config_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_decision_record(record)
        validate_decision_record(build_decision_record(self.decision, manager_action="ignored"))


if __name__ == "__main__":
    unittest.main()
