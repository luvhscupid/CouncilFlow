import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / ".agents" / "skills" / "council-flow" / "scripts" / "route.py"


class RoutingCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "routes.json"
        self.config.write_text(json.dumps({
            "version": "routing-v1", "threshold": 0.5, "margin": 0.1,
            "routes": [{"name": "docs", "examples": ["write docs"], "metadata": {}}],
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, input_text="write docs"):
        return subprocess.run(
            [sys.executable, str(CLI), "--config", str(self.config), *args],
            input=input_text,
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    def test_cli_emits_decision_json(self):
        result = self.run_cli("--router", "lexical")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "MATCHED")
        self.assertEqual(payload["route"], "docs")

    def test_cli_rejects_unbounded_input(self):
        result = self.run_cli("--router", "lexical", input_text="x" * 9000)
        self.assertEqual(result.returncode, 2)
        self.assertIn("bounded", result.stderr)

    def test_disabled_mode_preserves_no_route_behavior(self):
        result = self.run_cli("--disabled", "--router", "lexical")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "DISABLED")

    def test_workflow_requires_manager_acceptance(self):
        workflow = (ROOT / ".agents" / "skills" / "council-flow" / "references" / "workflow.md").read_text()
        self.assertIn("Manager validates the route hint", workflow)
        self.assertIn("Preserve that responsibility order", workflow)
        for role in ("Owner", "Planner", "Manager", "Worker", "Tester", "Reviewer"):
            self.assertIn(role, workflow)

    def test_route_output_cannot_claim_provider_identity(self):
        result = self.run_cli("--router", "lexical")
        payload = json.loads(result.stdout)
        self.assertNotIn("provider", payload)
        self.assertNotIn("model", payload)
        self.assertNotIn("dispatch", payload)
        self.assertNotIn("authorization", payload)


if __name__ == "__main__":
    unittest.main()
