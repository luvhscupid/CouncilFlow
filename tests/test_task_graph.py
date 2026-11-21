import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from task_graph import validate_graph


class TaskGraphTests(unittest.TestCase):
    def test_valid_graph_returns_stable_topological_order(self):
        result = validate_graph([
            {"task_id": "b", "depends_on": ["a"], "plan_revision": 1},
            {"task_id": "a", "depends_on": [], "plan_revision": 1},
        ], plan_revision=1)
        self.assertTrue(result["valid"])
        self.assertEqual(result["order"], ["a", "b"])

    def test_missing_dependency_and_cycle_are_rejected(self):
        missing = validate_graph([{"task_id": "a", "depends_on": ["absent"], "plan_revision": 1}], 1)
        cycle = validate_graph([
            {"task_id": "a", "depends_on": ["b"], "plan_revision": 1},
            {"task_id": "b", "depends_on": ["a"], "plan_revision": 1},
        ], 1)
        self.assertIn("MISSING_DEPENDENCY", missing["errors"])
        self.assertIn("a", missing["blocked"])
        self.assertEqual(missing["order"], [])
        self.assertIn("CYCLE", cycle["errors"])

    def test_blocked_parent_blocks_descendants_and_stale_plan_revision_fails(self):
        result = validate_graph([
            {"task_id": "a", "depends_on": [], "plan_revision": 1, "status": "BLOCKED"},
            {"task_id": "b", "depends_on": ["a"], "plan_revision": 0},
        ], 1)
        self.assertIn("b", result["blocked"])
        self.assertIn("STALE_PLAN_REVISION", result["errors"])

    def test_stale_parent_and_descendants_are_blocked(self):
        result = validate_graph([
            {"task_id": "a", "depends_on": [], "plan_revision": 0},
            {"task_id": "b", "depends_on": ["a"], "plan_revision": 1},
            {"task_id": "c", "depends_on": ["b"], "plan_revision": 1},
        ], 1)
        self.assertEqual(result["blocked"], ["a", "b", "c"])
        self.assertEqual(result["order"], [])

    def test_revisions_reject_booleans_and_dependencies_reject_unhashable_values(self):
        with self.assertRaises(ValueError):
            validate_graph([], plan_revision=True)
        with self.assertRaises(ValueError):
            validate_graph([{"task_id": "a", "depends_on": [], "plan_revision": True}], 1)
        with self.assertRaises(ValueError):
            validate_graph([{"task_id": "a", "depends_on": [[]], "plan_revision": 1}], 1)
        with self.assertRaises(ValueError):
            validate_graph([{"task_id": "a", "depends_on": [], "plan_revision": 1, "status": []}], 1)


if __name__ == "__main__":
    unittest.main()
