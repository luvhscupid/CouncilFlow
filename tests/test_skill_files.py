"""Static repository checks only; never certify native runtime behavior.

The dependency-free metadata reader accepts this skill's deliberately small
frontmatter subset: unquoted name plus a JSON-compatible quoted description.
It is not a general YAML parser. Native Codex discovery/invocation is separate.
"""

import ast
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "council-flow"


class SkillFilesTests(unittest.TestCase):
    def test_required_frontmatter_subset(self) -> None:
        source = (SKILL / "SKILL.md").read_text()
        self.assertTrue(source.startswith("---\n"))
        _, frontmatter, body = source.split("---", 2)
        fields = dict(line.split(":", 1) for line in frontmatter.strip().splitlines())
        self.assertEqual(fields["name"].strip(), "council-flow")
        description = json.loads(fields["description"].strip())
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 30)
        self.assertIn("$council-flow", body)
        self.assertLess(len(body.splitlines()), 100, "Keep the operational skill concise")

    def test_local_reference_targets_exist_and_are_useful(self) -> None:
        source = (SKILL / "SKILL.md").read_text()
        for link in re.findall(r"\]\((references/[^)]+)\)", source):
            target = SKILL / link
            self.assertTrue(target.is_file(), link)
            self.assertGreater(target.stat().st_size, 200)
        for name in ("roles", "workflow", "acceptance", "recovery"):
            self.assertTrue((SKILL / "references" / f"{name}.md").is_file())

    def test_optional_metadata_small_yaml_subset(self) -> None:
        source = (SKILL / "agents" / "openai.yaml").read_text()
        self.assertIn("interface:\n", source)
        for field in ("display_name", "short_description", "default_prompt"):
            line = next(line for line in source.splitlines()
                        if line.strip().startswith(field + ":"))
            self.assertIsInstance(json.loads(line.split(":", 1)[1].strip()), str)
        self.assertIn("$council-flow", source)
        self.assertIn("policy:\n  allow_implicit_invocation: false", source)

    def test_native_agent_toml_format_without_model_pinning(self) -> None:
        paths = sorted((ROOT / ".codex" / "agents").glob("*.toml"))
        self.assertEqual({p.stem for p in paths}, {
            "council-planner", "council-worker", "council-tester", "council-reviewer"})
        for path in paths:
            with self.subTest(path=path.name):
                data = tomllib.loads(path.read_text())
                self.assertEqual(data["name"], path.stem)
                for key in ("description", "developer_instructions"):
                    self.assertIsInstance(data[key], str)
                    self.assertTrue(data[key].strip())
                self.assertEqual(set(data), {"name", "description", "developer_instructions"})
        # This validates TOML and documented fields, not loading by the host.

    def test_separate_contract_types_are_documented(self) -> None:
        source = (SKILL / "references" / "roles.md").read_text()
        for role in ("Planner", "Manager", "Worker", "Tester", "Reviewer"):
            self.assertIn(role + "Request", source)
            self.assertIn(role + "Result", source)
        for field in ("task_id", "objective", "scope", "acceptance",
                      "implementation_status", "evidence", "open_findings",
                      "repair_decisions", "final_disposition"):
            self.assertIn(field, source)

    def test_validation_manifest_does_not_claim_runtime_passes(self) -> None:
        data = json.loads((ROOT / "tests" / "validation_cases.json").read_text())
        self.assertEqual([row["id"] for row in data["scenarios"]],
                         [f"V{n:02}" for n in range(1, 15)])
        for row in data["scenarios"]:
            self.assertIn(row["evidence_kind"], ("static", "runtime", "static_and_runtime"))
            self.assertTrue(row["required_observation"])
        self.assertEqual(data["runtime_default"], "UNVERIFIED")

    def test_fixture_is_valid_python_without_executing_expected_failure(self) -> None:
        fixture = ROOT / "demo" / "starter"
        for name in ("receipt_calculator.py", "test_receipt_calculator.py"):
            ast.parse((fixture / name).read_text(), filename=name)
        self.assertIn("test_multiple_product_quantities",
                      (fixture / "test_receipt_calculator.py").read_text())

    def test_product_has_no_runtime_or_external_dependency(self) -> None:
        # Owner restoration explicitly authorizes deterministic stdlib validators.
        # Replace the obsolete blanket no-scripts assertion, retaining dependency protection.
        self.assertTrue((SKILL / "scripts" / "contracts.py").is_file())
        for path in SKILL.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                self.assertIn(path.suffix, (".md", ".yaml", ".json", ".py"))
                source = path.read_text()
                self.assertNotIn("import acp", source.lower())
                self.assertNotIn("import execution_kernel", source.lower())
                if path.suffix == ".py":
                    imports = set()
                    for node in ast.walk(ast.parse(source)):
                        if isinstance(node, ast.Import):
                            imports.update(item.name.split(".")[0] for item in node.names)
                        elif isinstance(node, ast.ImportFrom):
                            imports.add(node.module.split(".")[0])
                    self.assertTrue(imports <= sys.stdlib_module_names)
                    self.assertFalse(imports & {"sqlite3", "http", "socket", "urllib"})
        # Static dependency inspection only; independent offline execution is separate.


if __name__ == "__main__":
    unittest.main()
