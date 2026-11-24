import unittest
from copy import deepcopy
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "experiments" / "multi-agent-evolution"  # offline prototype, not shipped
sys.path.insert(0, str(SCRIPT_DIR))

from experience import select_entries, validate_entry


class ExperienceTests(unittest.TestCase):
    def entry(self, **changes):
        value = {"entry_id": "lesson-1", "kind": "INSIGHT", "project_scope": "demo",
                 "review_claim": "owner_reviewed", "evidence_refs": ["report.md"], "superseded_by": None}
        value.update(changes)
        return value

    def test_unreviewed_claim_or_missing_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_entry(self.entry(review_claim="model_generated"))
        with self.assertRaises(ValueError):
            validate_entry(self.entry(evidence_refs=[]))

    def test_selection_is_project_scoped_and_excludes_superseded(self):
        values = [self.entry(), self.entry(entry_id="other", project_scope="other"),
                  self.entry(entry_id="old", superseded_by="lesson-2")]
        selected = select_entries(values, "demo")
        self.assertEqual([item["entry_id"] for item in selected], ["lesson-1"])
        self.assertEqual(selected[0]["review_status"], "UNVERIFIED")

    def test_owner_review_claim_never_becomes_verified(self):
        entry = validate_entry(self.entry())
        self.assertEqual(entry["review_claim"], "owner_reviewed")
        self.assertEqual(entry["review_status"], "UNVERIFIED")

    def test_kind_rejects_unhashable_and_non_string_values_as_value_errors(self):
        for value in ([], {}, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_entry(self.entry(kind=value))

    def test_duplicate_ids_fail_closed_across_scopes(self):
        with self.assertRaises(ValueError):
            select_entries([self.entry(), self.entry(project_scope="other")], "demo")

    def test_poisoned_and_malformed_review_claims_do_not_become_memory_authority(self):
        original = self.entry()
        snapshot = deepcopy(original)
        selected = select_entries([original], "demo")
        self.assertEqual(original, snapshot)
        self.assertEqual(selected[0]["review_status"], "UNVERIFIED")
        self.assertEqual(set(selected[0]), set(snapshot) | {"review_status"})
        for claim in (None, [], {}, "model_verified"):
            with self.subTest(claim=claim), self.assertRaises(ValueError):
                validate_entry(self.entry(review_claim=claim))

    def test_wrong_project_and_superseded_entries_are_never_selected(self):
        values = [self.entry(entry_id="wrong", project_scope="another-project"),
                  self.entry(entry_id="stale", superseded_by="replacement")]
        self.assertEqual(select_entries(values, "demo"), [])


if __name__ == "__main__":
    unittest.main()
