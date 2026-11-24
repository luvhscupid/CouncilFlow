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


PLUGIN_CLI = ROOT / "plugins" / "councilflow" / "skills" / "run" / "scripts" / "route.py"
ROUTING_DOCS = ("SKILL.md", "references/communication.md", "references/workflow.md", "references/roles.md")


class RoutingLifecycleCliTests(unittest.TestCase):
    """The Manager records accept, ignore, block or override with route.py, not Python imports."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "routes.json"
        self.config.write_text(json.dumps({
            "version": "routing-v1", "threshold": 0.5, "margin": 0.1,
            "routes": [{"name": "docs", "examples": ["write docs"], "metadata": {}}],
        }), encoding="utf-8")
        self.task = self.root / "task.txt"
        self.task.write_text("write docs", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, script=CLI, cwd=ROOT):
        return subprocess.run([sys.executable, "-I", str(script), *args], text=True,
                              capture_output=True, cwd=cwd)

    def base(self):
        return ["--config", str(self.config), "--input", str(self.task)]

    def load_record(self, path):
        sys.path.insert(0, str(CLI.parent))
        try:
            from routing.decision import validate_decision_record
        finally:
            sys.path.remove(str(CLI.parent))
        record = json.loads(path.read_text(encoding="utf-8"))
        validate_decision_record(record)
        return record

    def test_classify_alias_matches_bare_form(self):
        bare = self.cli(*self.base())
        alias = self.cli("classify", *self.base())
        self.assertEqual(bare.returncode, 0, bare.stderr)
        self.assertEqual(alias.stdout, bare.stdout)

    def test_record_each_manager_action(self):
        hint = self.root / "hint.json"
        hint.write_text(self.cli(*self.base()).stdout, encoding="utf-8")
        for action in ("accepted", "ignored", "blocked"):
            with self.subTest(action=action):
                out = self.root / f"{action}.json"
                result = self.cli("record", *self.base(), "--hint", str(hint), "--action", action,
                                  "--evidence-ref", "messages/M1.json", "--out", str(out))
                self.assertEqual(result.returncode, 0, result.stderr)
                record = self.load_record(out)
                self.assertEqual(record["manager_action"], action)
                self.assertEqual(record["route"], "docs")
                self.assertEqual(json.loads(result.stdout)["record_sha256"], record["record_sha256"])

    def test_override_requires_reason(self):
        out = self.root / "override.json"
        blank = self.cli("override", *self.base(), "--reason", "  ", "--out", str(out))
        self.assertEqual(blank.returncode, 2)
        self.assertFalse(out.exists())
        missing = self.cli("override", *self.base(), "--out", str(out))
        self.assertEqual(missing.returncode, 2)
        result = self.cli("override", *self.base(), "--reason", "Owner scope differs", "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        record = self.load_record(out)
        self.assertEqual(record["manager_action"], "overridden")
        self.assertEqual(record["manager_reason"], "Owner scope differs")

    def test_edited_hint_and_existing_output_are_refused(self):
        hint = json.loads(self.cli(*self.base()).stdout)
        out = self.root / "record.json"
        for field, value in (("confidence", 0.51), ("input_sha256", "0" * 64), ("route", None)):
            with self.subTest(field=field):
                edited = self.root / f"edited-{field}.json"
                edited.write_text(json.dumps({**hint, field: value}), encoding="utf-8")
                result = self.cli("record", *self.base(), "--hint", str(edited), "--action", "accepted",
                                  "--out", str(out))
                self.assertEqual(result.returncode, 2)
                self.assertIn("hint does not match", result.stderr)
                self.assertFalse(out.exists())
        out.write_text("{}", encoding="utf-8")
        again = self.cli("record", *self.base(), "--action", "accepted", "--out", str(out))
        self.assertEqual(again.returncode, 2)
        self.assertEqual(out.read_text(encoding="utf-8"), "{}")

    def test_installed_plugin_copy_records_from_another_repository(self):
        if not PLUGIN_CLI.is_file():
            self.skipTest("the portable release archive ships only the Codex skill copy")
        out = self.root / "record.json"
        result = self.cli("record", *self.base(), "--action", "ignored", "--out", str(out),
                          script=PLUGIN_CLI, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.load_record(out)["manager_action"], "ignored")

    def test_docs_never_ask_the_manager_to_import_routing_python(self):
        skills = [ROOT / ".agents/skills/council-flow"]
        if (ROOT / "plugins/councilflow/skills/run").is_dir():
            skills.append(ROOT / "plugins/councilflow/skills/run")
        for skill in skills:
            names = ROUTING_DOCS + (("host-claude.md",) if (skill / "host-claude.md").exists() else ())
            for name in names:
                body = (skill / name).read_text(encoding="utf-8")
                with self.subTest(doc=str(skill / name)):
                    self.assertNotIn("build_decision_record", body)
                    self.assertNotIn("override_route(", body)


if __name__ == "__main__":
    unittest.main()
