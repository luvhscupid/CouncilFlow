"""Static instruction and installation checks; no live MCP calls are simulated.

These checks protect the documented lifecycle branches. Runtime automatic use,
index freshness, native activation, and independent roles need host evidence.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "council-flow"


class CodebaseMemoryInstructionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cls.workflow = (SKILL / "references" / "workflow.md").read_text(encoding="utf-8")
        cls.reference = (SKILL / "references" / "codebase-memory.md").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def section(self, title):
        return self.reference.split("## " + title + "\n", 1)[1].split("\n## ", 1)[0]

    def test_retired_standalone_paths_are_absent(self):
        retired_skill = "-".join(("cf", "recall"))
        script_path = "/".join(("scripts", "recall.py"))
        reference_path = "/".join(("references", "recall.md"))
        test_path = "/".join(("tests", "test_recall.py"))
        for path in (ROOT / ".agents" / "skills" / retired_skill,
                     SKILL.joinpath(*script_path.split("/")),
                     SKILL.joinpath(*reference_path.split("/")),
                     ROOT.joinpath(*test_path.split("/"))):
            self.assertFalse(path.exists(), str(path))
        for text in (self.skill, self.workflow, self.readme, self.reference):
            obsolete_command = "$" + retired_skill
            for obsolete in (obsolete_command, script_path, reference_path,
                             "recall.json", "--label observed"):
                self.assertNotIn(obsolete, text)

    def test_council_flow_requires_context_before_planner_and_after_worker(self):
        automatic = self.skill.split("## Automatic project context\n", 1)[1].split("## Execute the goal", 1)[0]
        self.assertIn("Before Planner, Manager follows", automatic)
        self.assertIn("[Codebase Memory](references/codebase-memory.md) automatically", automatic)
        self.assertIn("no separate Owner command", automatic)
        self.assertIn("After Worker stops edits", automatic)
        self.assertLess(self.workflow.index("[Codebase Memory lifecycle]"),
                        self.workflow.index("2. Dedicated Planner"))
        self.assertLess(self.workflow.index("Manager then synchronizes"),
                        self.workflow.index("5. Fresh independent Tester"))

    def test_empty_installation_gate_precedes_mcp_discovery(self):
        local = self.section("1. Inspect local content before MCP discovery")
        self.assertIn("only CouncilFlow installation files", local)
        self.assertIn("**zero MCP calls**, including project listing and index status", local)
        self.assertIn(".claude/skills/council-flow/", local)
        self.assertIn(".claude/agents/council-*.md", local)
        self.assertIn("Continue normal project creation", local)
        self.assertIn("After meaningful source exists", local)
        self.assertLess(self.reference.index("1. Inspect local content"),
                        self.reference.index("2. Discover the actual capability"))

    def test_first_encounter_binds_observed_namespace_and_exact_project(self):
        discovery = self.section("2. Discover the actual capability and bind the project")
        for text in ("supported input/output schemas", "Codebase Memory MCP namespace",
                     "an unrelated\nproject-listing MCP tool", "not this capability",
                     "observed project `name`", "`root_path`", "nested repository",
                     "resolved `root_path` equals the authorized repository root exactly",
                     "A parent path alone never establishes project identity",
                     "If the API cannot establish\nthe exact root, use direct inspection",
                     "never choose a similarly named sibling", "missing index",
                     "`index_repository`, only when present", "authorized root when useful"):
            self.assertIn(text, discovery)

    def test_changed_source_requires_freshness_before_graph_reliance(self):
        freshness = self.section("3. Establish freshness before graph reliance")
        for text in ("current source changes", "actual semantics", "untracked files",
                     "Refresh stale information", "before using remembered relationships",
                     "pending, stale, unknown", "dependencies directly"):
            self.assertIn(text, freshness)
        update = self.section("5. Synchronize resulting source and preserve verification")
        self.assertIn("After Worker stops edits", update)
        self.assertIn("Repeat after fresh-Worker rework", update)
        self.assertIn("checks status and relevant", update)
        self.assertIn("API cannot establish synchronization", update)

    def test_fresh_agents_receive_bounded_context_and_coverage_gaps(self):
        context = self.section("4. Retrieve bounded context and pass it to fresh agents")
        for text in ("Bound result", "trace depth", "relevant result pages",
                     "`check_index_coverage` once", "Read\ncritical source directly",
                     "exact project/root", "index generation/freshness", "qualified symbols",
                     "pagination", "coverage gaps", "unresolved uncertainty",
                     "task `instructions`", "`evidence_refs`", "closed communication schema unchanged",
                     "Do not assume\nchildren inherit MCP access", "child without tools"):
            self.assertIn(text, context)

    def test_missing_or_unreachable_mcp_continues_direct_inspection(self):
        discovery = self.section("2. Discover the actual capability and bind the project")
        self.assertIn("configured server is not proof of availability", discovery)
        self.assertIn("failed startup/handshake", discovery)
        fallback = self.section("Direct inspection fallback and reporting")
        for text in ("configured but unreachable", "continue ordinary CouncilFlow",
                     "No mandatory manual", "Live MCP integration is UNVERIFIED",
                     "Static instruction\ntests do not prove automatic activation"):
            self.assertIn(text, fallback)

    def test_graph_capability_preserves_roles_verification_and_authority(self):
        update = self.section("5. Synchronize resulting source and preserve verification")
        for text in ("frozen acceptance unchanged", "not correctness proof or permission authority",
                     "Independent\ntests, Reviewer comparison/rerun, and Planner acceptance remain required",
                     "Owner-authorized project", "inherited\nnative permissions",
                     "Do not install, replace, or reconfigure a server", "global settings"):
            self.assertIn(text, update)

    def test_installation_includes_reference_without_manual_initialization(self):
        self.assertIn("Copy the whole `.claude/skills/council-flow/` folder", self.readme)
        self.assertIn(".claude/skills/council-flow/references/codebase-memory.md", self.readme)
        self.assertIn("ships inside the complete skill folder copied during installation", self.readme)
        self.assertIn("No additional\nskill or registration is needed", self.readme)
        self.assertIn("manual initialization command", self.readme)
        self.assertIn("checks do not establish native invocation or live MCP behavior", self.readme)


if __name__ == "__main__":
    unittest.main()
