import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from experience import select_entries, validate_entry


class ExperienceTests(unittest.TestCase):
    def entry(self, **changes):
        value = {"entry_id": "lesson-1", "kind": "INSIGHT", "project_scope": "demo",
                 "provenance": "owner_reviewed", "evidence_refs": ["report.md"], "superseded_by": None}
        value.update(changes)
        return value

    def test_unreviewed_or_missing_provenance_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_entry(self.entry(provenance="model_generated"))
        with self.assertRaises(ValueError):
            validate_entry(self.entry(evidence_refs=[]))

    def test_selection_is_project_scoped_and_excludes_superseded(self):
        values = [self.entry(), self.entry(entry_id="other", project_scope="other"),
                  self.entry(entry_id="old", superseded_by="lesson-2")]
        selected = select_entries(values, "demo")
        self.assertEqual([item["entry_id"] for item in selected], ["lesson-1"])


if __name__ == "__main__":
    unittest.main()
