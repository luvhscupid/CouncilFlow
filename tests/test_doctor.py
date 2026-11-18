import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from doctor import diagnose, load_evidence


class DoctorTests(unittest.TestCase):
    def test_missing_native_role_evidence_is_unverified_not_pass(self):
        result = diagnose({"native_roles": [], "required_roles": ["planner", "worker", "tester", "reviewer"]})
        native = next(item for item in result if item["check"] == "native_role_sequence")
        self.assertEqual(native["status"], "UNVERIFIED")

    def test_explicit_invalid_evidence_fails_and_optional_skip_is_not_green(self):
        result = diagnose({"source_hash_valid": False, "dashboard": None})
        self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "UNVERIFIED")
        self.assertEqual(next(item for item in result if item["check"] == "dashboard")["status"], "SKIP")

    def test_self_reported_role_names_and_success_booleans_do_not_pass(self):
        result = diagnose({"native_roles": ["planner", "worker", "tester", "reviewer"],
                           "source_hash_valid": True, "tester_evidence": True,
                           "reviewer_rerun": True, "planner_check": True})
        self.assertTrue(all(item["status"] == "UNVERIFIED" for item in result if item["check"] != "dashboard"))

    def test_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            load_evidence('{"source_hash_valid":false,"source_hash_valid":true}')


if __name__ == "__main__":
    unittest.main()
