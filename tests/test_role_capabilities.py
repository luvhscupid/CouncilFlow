import unittest

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from role_capabilities import resolve_role, validate_profile


class RoleCapabilityTests(unittest.TestCase):
    def test_valid_profile_is_versioned_and_preserves_preference(self):
        profile = validate_profile({
            "schema_version": 1,
            "roles": {"worker": {"preference": "lower_cost_if_qualified"}},
        })
        self.assertEqual(profile["roles"]["worker"]["preference"], "lower_cost_if_qualified")

    def test_unknown_profile_fields_and_preferences_fail_closed(self):
        with self.assertRaises(ValueError):
            validate_profile({"schema_version": 1, "roles": {"worker": {"model": "fast"}}})
        with self.assertRaises(ValueError):
            validate_profile({"schema_version": 99, "roles": {}})

    def test_profile_rejects_boolean_version_and_unhashable_preference(self):
        with self.assertRaises(ValueError):
            validate_profile({"schema_version": True, "roles": {}})
        with self.assertRaises(ValueError):
            validate_profile({"schema_version": 1, "roles": {"worker": {"preference": []}}})

    def test_unsupported_override_inherits_host_without_model_claim(self):
        result = resolve_role(
            {"schema_version": 1, "roles": {"worker": {"preference": "lower_cost_if_qualified"}}},
            {"explicit_role_selection": False},
            "worker",
        )
        self.assertEqual(result["selection"], "INHERIT_HOST")
        self.assertIsNone(result["effective_model"])
        self.assertFalse(result["route_verified"])

    def test_unobserved_capability_is_not_supported(self):
        result = resolve_role(
            {"schema_version": 1, "roles": {"tester": {"preference": "inherit_host"}}},
            {},
            "tester",
        )
        self.assertEqual(result["selection"], "INHERIT_HOST")
        self.assertEqual(result["capability_status"], "UNKNOWN")

    def test_caller_supplied_capability_cannot_be_promoted_to_verified(self):
        result = resolve_role(
            {"schema_version": 1, "roles": {"worker": {"preference": "inherit_host"}}},
            {"explicit_role_selection": True, "evidence_ref": "claimed-by-caller"},
            "worker",
        )
        self.assertEqual(result["capability_status"], "UNKNOWN")
        self.assertTrue(result["capability_reported"])
        self.assertFalse(result["route_verified"])

    def test_capability_flag_requires_exact_boolean_or_null(self):
        for value in (0, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_role({"schema_version": 1, "roles": {}}, {"explicit_role_selection": value}, "worker")


if __name__ == "__main__":
    unittest.main()
