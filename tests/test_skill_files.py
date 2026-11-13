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
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "council-flow"


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
        self.assertIn("/council-flow", body)
        self.assertLess(len(body.splitlines()), 110, "Keep the operational skill concise")

    def test_local_reference_targets_exist_and_are_useful(self) -> None:
        source = (SKILL / "SKILL.md").read_text()
        for link in re.findall(r"\]\((references/[^)]+)\)", source):
            target = SKILL / link
            self.assertTrue(target.is_file(), link)
            self.assertGreater(target.stat().st_size, 200)
        for name in ("roles", "workflow", "acceptance", "recovery"):
            self.assertTrue((SKILL / "references" / f"{name}.md").is_file())

    def test_claude_agent_markdown_format_without_codex_metadata(self) -> None:
        paths = sorted((ROOT / ".claude" / "agents").glob("council-*.md"))
        self.assertEqual({p.stem for p in paths}, {
            "council-planner", "council-worker", "council-tester", "council-reviewer"})
        for path in paths:
            with self.subTest(path=path.name):
                source = path.read_text()
                self.assertTrue(source.startswith("---\n"))
                self.assertIn(f"name: {path.stem}\n", source)
                self.assertIn("description:", source)
                self.assertIn("CouncilFlow", source)
                self.assertNotIn(".codex", source)
        self.assertFalse((SKILL / "agents" / "openai.yaml").exists())
        self.assertFalse((ROOT / ".codex").exists())
        self.assertFalse((ROOT / ".agents").exists())
        # This validates repository metadata, not live host loading.

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
        self.assertEqual([row["id"] for row in data["synthetic_regressions"]],
                         [f"T{n:02}" for n in range(1, 25)])

    def test_reviewer_is_comparator_not_ux_evaluator(self) -> None:
        role = (ROOT / ".claude" / "agents" / "council-reviewer.md").read_text()
        policy = (SKILL / "policies" / "roles.yaml").read_text()
        self.assertIn("frozen original plan/criteria", role)
        self.assertIn("Tester execution evidence", role)
        self.assertIn("compare_evidence", policy)
        for forbidden in ("first-time user", "experience_review", "qualitative rubric"):
            self.assertNotIn(forbidden, role + policy)

    def test_review_binds_exact_executable_and_completed_tester_message(self) -> None:
        reviewer = (ROOT / ".claude" / "agents" / "council-reviewer.md").read_text()
        tester = (ROOT / ".claude" / "agents" / "council-tester.md").read_text()
        communication = (SKILL / "references" / "communication.md").read_text()
        for phrase in ("exact `command` executable path", "never substitute a shell alias",
                       "working directory", "candidate", "relevant input references"):
            self.assertIn(phrase, reviewer)
        self.assertIn("exact invoked executable path", tester)
        self.assertIn("exact earlier", communication)
        self.assertIn("exact serialized Tester message", communication)

    def test_planner_failure_requires_explicit_manager_rework(self) -> None:
        skill = (SKILL / "SKILL.md").read_text()
        communication = (SKILL / "references" / "communication.md").read_text()
        recovery = (SKILL / "references" / "recovery.md").read_text()
        self.assertIn("rework must reply to that exact check", skill)
        self.assertIn("decision replies to that exact check", communication)
        self.assertIn("replies to the exact", recovery)

    def test_gate3_e4_erratum_preserves_frozen_specification(self) -> None:
        erratum = ROOT / "docs" / "gate3" / "CouncilFlow-Gate3-v0.2" / "06-COUNCIL-APPROVED-ERRATUM-C3.md"
        self.assertTrue(erratum.is_file())
        text = erratum.read_text()
        for required in ("Gate 3 E4", "PASS", "FAIL", "UNVERIFIED",
                         "cosmetic thread labels", "model or sandbox"):
            self.assertIn(required, text)

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
