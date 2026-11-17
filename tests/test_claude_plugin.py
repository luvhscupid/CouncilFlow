"""Offline structure/contract tests for the Claude Code plugin package.

These are static checks; they do not prove native Claude Code subagent execution.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/councilflow"
RUN = PLUGIN / "skills/run"
ROLES = ("planner", "worker", "tester", "reviewer")


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("cc_builder", "tools/build_claude_plugin.py")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert match, path
    return dict(line.split(": ", 1) for line in match.group(1).splitlines()), text


def py(cwd, *args):
    return subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, capture_output=True,
                          timeout=60, env={**os.environ, "PYTHONPATH": ""})


class ManifestTests(unittest.TestCase):
    def test_manifest(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "councilflow")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual([p.name for p in (PLUGIN / ".claude-plugin").iterdir()], ["plugin.json"])
        self.assertTrue((PLUGIN / "agents").is_dir() and (PLUGIN / "skills").is_dir())

    def test_skill_invocation_format(self):
        meta, text = frontmatter(RUN / "SKILL.md")
        self.assertEqual(meta["name"], "run")  # namespaced as /councilflow:run
        self.assertIn("/councilflow:run", text)
        self.assertIn("$ARGUMENTS", text)
        self.assertEqual(meta["disable-model-invocation"], "true")
        self.assertIn("${CLAUDE_SKILL_DIR}", text)
        self.assertEqual(sorted(p.name for p in (PLUGIN / "skills").iterdir()), ["run"])

    def test_no_hardcoded_paths_or_global_config(self):
        for path in PLUGIN.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".py"}:
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("E:\\Saint", text, path)
                self.assertNotIn("E:/Saint", text, path)
        for name in ("hooks", "settings.json", ".mcp.json"):
            self.assertFalse((PLUGIN / name).exists(), name)


class AgentTests(unittest.TestCase):
    def test_agents_and_tool_boundaries(self):
        names = sorted(p.stem for p in (PLUGIN / "agents").glob("*.md"))
        self.assertEqual(names, sorted(f"council-{r}" for r in ROLES))
        for role in ROLES:
            meta, text = frontmatter(PLUGIN / "agents" / f"council-{role}.md")
            self.assertEqual(meta["name"], f"council-{role}")
            self.assertIn("fresh", text)
            self.assertIn("roles.yaml", text)
            tools = {t.strip() for t in meta["tools"].split(",")}
            self.assertNotIn("Agent", tools)  # subagents cannot delegate
            self.assertEqual("Edit" in tools, role == "worker")  # only Worker edits code

    def test_claude_instructions_do_not_require_unsupported_packet_fields(self):
        tester = (PLUGIN / "agents/council-tester.md").read_text(encoding="utf-8")
        reviewer = (PLUGIN / "agents/council-reviewer.md").read_text(encoding="utf-8")
        unsupported = ("execution_evidence", "tester_execution_evidence", "evidence_type")
        for field in unsupported:
            # A prohibition may name the unsupported field; instructions must not
            # tell a role to populate it as packet content.
            directive = re.compile(
                rf"\b(?:record|include|set|provide|emit|require)\b[^\n]{{0,100}}"
                rf"\b{re.escape(field)}\b", re.IGNORECASE)
            self.assertIsNone(directive.search(tester), f"Tester requires unsupported {field}")
            self.assertIsNone(directive.search(reviewer), f"Reviewer requires unsupported {field}")
        self.assertIn("no `evidence_type` field", tester)
        self.assertIn("Do not add `execution_evidence` or `tester_execution_evidence` fields", reviewer)

    def test_role_boundaries(self):
        text = {r: frontmatter(PLUGIN / "agents" / f"council-{r}.md")[1] for r in ROLES}
        self.assertIn("Do not repair", text["tester"])
        self.assertIn("CRLF-to-LF", text["tester"])
        for needle in ("exact executable", "CRLF-to-LF", "SHA-256", "NOT_COMPARABLE",
                       "Mismatch fails", "independent_rerun"):
            self.assertIn(needle, text["reviewer"])
        self.assertIn("approve your own work", text["worker"])
        self.assertIn("original", text["planner"].lower())
        self.assertIn("Do not invent approval", text["planner"])

    def test_manager_is_main_session_and_order(self):
        _, text = frontmatter(RUN / "SKILL.md")
        self.assertIn("cannot spawn", text)
        self.assertIn("main\nsession is the Manager", text)
        self.assertIn("never writes application code", text)
        for role in ROLES:
            self.assertIn(f"councilflow:council-{role}", text)
        keys = ("**Planner**", "**Manager**", "**Worker**", "**Tester**",
                "**Reviewer**", "**Final Planner check**")
        positions = [text.index(k) for k in keys]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("UNVERIFIED", text)
        self.assertIn("DRAFT_NOT_AUTHORIZED", text)
        self.assertIn("verbatim", text)  # original Owner goal bound as source


class RuntimeTests(unittest.TestCase):
    def test_runtime_identical_to_canonical(self):
        self.assertEqual(builder.drift(), [])

    def test_drift_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, copy = builder.TARGET, Path(tmp) / "run"
            shutil.copytree(old, copy)
            (copy / "scripts/contracts.py").write_bytes(b"# tampered\n")
            builder.TARGET = copy
            try:
                self.assertIn("differs: scripts/contracts.py", builder.drift())
            finally:
                builder.TARGET = old

    def test_relocated_plugin_runs_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / "cache/councilflow"
            shutil.copytree(PLUGIN, installed)
            repo = Path(tmp) / "other-repo"
            repo.mkdir()
            skill = installed / "skills/run"
            policy = py(repo, skill / "scripts/contracts.py", "policy", skill / "policies/roles.yaml")
            self.assertEqual(policy.returncode, 0, policy.stderr)
            rec = repo / "in.json"
            rec.write_text(json.dumps({"run_id": "r1", "harness": "claude-code",
                                       "route": "claude-code/unknown/stream-json"}))
            out = py(repo, skill / "scripts/efficiency.py", "record", rec, "--records", repo / "r.jsonl")
            self.assertEqual(out.returncode, 0, out.stderr)
            record = json.loads((repo / "r.jsonl").read_text())
            self.assertIsNone(record["usage"]["reported_cost"])
            self.assertEqual(record["acceptance"]["status"], "unknown")
            self.assertFalse((repo / ".councilflow").exists())  # nothing captured automatically

    def test_contract_cli_surface(self):
        helped = py(ROOT, RUN / "scripts/contracts.py", "--help")
        self.assertEqual(helped.returncode, 0)
        for sub in ("capture", "sequence", "message", "policy"):
            self.assertIn(sub, helped.stdout.decode())

    def test_original_criteria_fidelity_enforced(self):
        """The plugin's copy of the validator accepts faithful criteria and rejects altered ones."""
        sys.path.insert(0, str(ROOT / "tests"))
        from test_contracts import ref
        original = (ROOT / "tests/fixtures/owner-version-original.txt").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "owner-original.txt").write_bytes(original)
            source = ref("owner-original", "owner-original.txt", hashlib.sha256(original).hexdigest(),
                         "owner-original-source")
            ref_path = repo / "original-ref.json"
            ref_path.write_text(json.dumps(source))
            script = RUN / "scripts/contracts.py"
            captured = py(repo, script, "capture", ref_path, "--root", repo,
                          "--owner-provenance", "owner-original")
            self.assertEqual(captured.returncode, 0, captured.stderr)
            criteria = json.loads(captured.stdout)["criteria"]
            self.assertEqual(len(criteria), 3)

            from test_contracts import publish

            def check(acceptance):
                plan = {"plan_id": "P1", "plan_revision": 1, "original_source_ref": source,
                        "acceptance": acceptance, "metadata": {"maintenance_control": True}}
                plan_path = repo / "plan.json"
                plan_path.write_bytes(json.dumps(plan, ensure_ascii=False).encode("utf-8"))
                packet = publish()
                packet["payload"]["acceptance_ids"] = [e["id"] for e in acceptance]
                packet["payload"]["plan_ref"] = ref("plan", "plan.json",
                                                    hashlib.sha256(plan_path.read_bytes()).hexdigest(), "plan")
                packet["evidence_refs"] = [packet["payload"]["plan_ref"]]
                (repo / "packet.json").write_text(json.dumps(packet))
                return py(repo, script, "sequence", repo / "packet.json", "--root", repo,
                          "--original-source-ref", ref_path, "--owner-provenance", "owner-original",
                          "--require-criteria-fidelity")

            self.assertEqual(check(criteria).returncode, 0)
            altered = [dict(c) for c in criteria]
            altered[0]["criterion"] = "print something version-like"
            self.assertNotEqual(check(altered).returncode, 0)

    def test_reviewer_deterministic_comparison(self):
        """Exit code + CRLF->LF stdout SHA-256 semantics the Reviewer applies."""
        def digest(data):
            return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
        cmd = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'ok\\r\\n')"]
        first, second = subprocess.run(cmd, capture_output=True), subprocess.run(cmd, capture_output=True)
        self.assertEqual((first.returncode, digest(first.stdout)), (second.returncode, digest(second.stdout)))
        other = subprocess.run([sys.executable, "-c", "print('different')"], capture_output=True)
        self.assertNotEqual(digest(first.stdout), digest(other.stdout))
        self.assertEqual(digest(b"ok\r\n"), digest(b"ok\n"))


class PackageTests(unittest.TestCase):
    def test_committed_release_artifacts_match_isolated_rebuilds(self):
        """Fail when either committed ZIP or sidecar is stale versus current sources."""
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "source"
            shutil.copytree(ROOT, snapshot, ignore=shutil.ignore_patterns(
                ".git", "dist", "__pycache__", ".pytest_cache", "*.pyc", "*.pyo"))

            spec = importlib.util.spec_from_file_location(
                "isolated_codex_builder", snapshot / "tools/build_release.py")
            codex = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = codex
            spec.loader.exec_module(codex)
            codex_result = codex.build(root=snapshot)
            for relative, result in (("dist/council-flow.zip", codex_result),):
                rebuilt = snapshot / relative
                committed = ROOT / relative
                self.assertEqual(rebuilt.read_bytes(), committed.read_bytes(),
                                 f"stale committed release archive: {relative}")
                rebuilt_sidecar = rebuilt.with_name(rebuilt.name + ".sha256")
                committed_sidecar = committed.with_name(committed.name + ".sha256")
                self.assertEqual(rebuilt_sidecar.read_bytes(), committed_sidecar.read_bytes(),
                                 f"stale committed release sidecar: {relative}.sha256")
                self.assertEqual(result["sha256"], hashlib.sha256(committed.read_bytes()).hexdigest())

            claude_archive = snapshot / "dist/councilflow-claude-plugin.zip"
            claude_run = subprocess.run(
                [sys.executable, "tools/build_claude_plugin.py", "build", "--output", str(claude_archive)],
                cwd=snapshot, capture_output=True, timeout=60)
            self.assertEqual(claude_run.returncode, 0, claude_run.stderr.decode(errors="replace"))
            committed_claude = ROOT / "dist/councilflow-claude-plugin.zip"
            # Diagnose source/entry drift separately from ZIP byte-level drift.
            with zipfile.ZipFile(claude_archive) as rebuilt_zip, zipfile.ZipFile(committed_claude) as committed_zip:
                self.assertEqual(rebuilt_zip.namelist(), committed_zip.namelist(),
                                 "Claude release ZIP entry ordering/inventory differs")
                for entry_name in rebuilt_zip.namelist():
                    self.assertEqual(rebuilt_zip.read(entry_name), committed_zip.read(entry_name),
                                     f"Claude ZIP source-byte mismatch: {entry_name}")
            self.assertEqual(claude_archive.read_bytes(), committed_claude.read_bytes(),
                             "Claude ZIP compressed bytes or metadata differ despite identical entries")
            self.assertEqual(claude_archive.with_name(claude_archive.name + ".sha256").read_bytes(),
                             committed_claude.with_name(committed_claude.name + ".sha256").read_bytes(),
                             "stale committed release sidecar: dist/councilflow-claude-plugin.zip.sha256")

    def test_package_deterministic_and_portable(self):
        tracked_archive = ROOT / "dist/councilflow-claude-plugin.zip"
        tracked_sidecar = ROOT / "dist/councilflow-claude-plugin.zip.sha256"
        before = (tracked_archive.read_bytes(), tracked_sidecar.read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "councilflow-claude-plugin.zip"
            first, second = builder.build(archive), builder.build(archive)
            self.assertEqual(first, second)
            self.assertEqual(first["archive"], archive.as_posix())
            self.assertEqual(first["sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual((tracked_archive.read_bytes(), tracked_sidecar.read_bytes()), before)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                self.assertEqual(names, sorted(names, key=lambda name: tuple(name.split("/"))),
                                 "ZIP entries must use portable case-sensitive component ordering")
                for required in (".claude-plugin/plugin.json", "skills/run/SKILL.md",
                                 "skills/run/scripts/contracts.py", "skills/run/scripts/efficiency.py"):
                    self.assertIn(required, names)
                self.assertEqual(sum(n.startswith("agents/council-") for n in names), 4)
                for n in names:
                    self.assertFalse(n.startswith("/") or ".." in n.split("/") or "\\" in n or ":" in n, n)
                    self.assertNotIn("__pycache__", n)
                    self.assertFalse(n.endswith(".pyc"))
                with tempfile.TemporaryDirectory() as extracted:
                    z.extractall(extracted)
                    r = py(extracted, Path(extracted) / "skills/run/scripts/contracts.py", "policy",
                           Path(extracted) / "skills/run/policies/roles.yaml")
                    self.assertEqual(r.returncode, 0, r.stderr)
            sidecar = archive.with_name(archive.name + ".sha256").read_text()
            self.assertEqual(sidecar.split()[0], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(sidecar.split()[1], archive.name)

    def test_codex_release_excludes_plugin(self):
        codex = load("codex_builder", "tools/build_release.py")
        self.assertFalse(any(n.startswith("plugins/") for n in codex.source_bytes(ROOT)))


class HostAdapterTests(unittest.TestCase):
    def test_adapter_maps_every_shared_codex_reference(self):
        adapter = " ".join((RUN / "host-claude.md").read_text(encoding="utf-8").split())
        for token in ("$council-flow", ".agents/skills/council-flow/", ".codex/agents",
                      "inherit_native_codex", "/councilflow:run", "councilflow:council-planner", "`-reviewer`",
                      "skill directory", "not the plugin root"):
            self.assertIn(token, adapter)
        # Every host-specific token that remains in shared files is covered by the mapping.
        shared = "".join(p.read_text(encoding="utf-8") for sub in ("references", "policies")
                         for p in (RUN / sub).rglob("*") if p.is_file())
        if "inherit_native_codex" in shared:
            self.assertIn("inherit_native_codex", adapter)
        if ".codex/agents" in shared:
            self.assertIn(".codex/agents", adapter)

    def test_adapter_is_plugin_only_and_not_shared_runtime(self):
        self.assertFalse((ROOT / ".agents/skills/council-flow/host-claude.md").exists())
        self.assertEqual(builder.drift(), [])  # adapter does not count as shared-runtime drift
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "plugin.zip"
            builder.build(archive)
            with zipfile.ZipFile(archive) as z:
                self.assertIn("skills/run/host-claude.md", z.namelist())

    def test_entrypoints_direct_to_adapter(self):
        self.assertIn("CF/host-claude.md", (RUN / "SKILL.md").read_text(encoding="utf-8"))
        for role in ROLES:
            self.assertIn("host-claude.md", (PLUGIN / "agents" / f"council-{role}.md").read_text(encoding="utf-8"))

    def test_codex_skill_and_roles_keep_codex_syntax(self):
        codex = (ROOT / ".agents/skills/council-flow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("$council-flow", codex)
        self.assertNotIn("councilflow:run", codex)
        self.assertEqual(sorted(p.name for p in (ROOT / ".codex/agents").glob("*.toml")),
                         [f"council-{r}.toml" for r in sorted(ROLES)])


if __name__ == "__main__":
    unittest.main()
