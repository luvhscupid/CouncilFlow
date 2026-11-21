"""Remote update state-machine tests against a disposable local bare Git remote."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PS = shutil.which("pwsh") or shutil.which("powershell")
BOOTSTRAP = ROOT / "scripts/bootstrap.ps1"
UPDATER = ROOT / "scripts/remote-update.ps1"


@unittest.skipUnless(PS, "PowerShell is required for remote updater integration tests")
class RemoteUpdateTests(unittest.TestCase):
    def git(self, cwd, *args, check=True):
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
        if check and result.returncode:
            self.fail(result.stdout + result.stderr)
        return result

    def run_ps(self, script, home, *args, expect=0):
        env = os.environ.copy()
        env["COUNCILFLOW_BOOTSTRAP_HOME"] = str(home)
        result = subprocess.run([PS, "-NoProfile", "-File", str(script), *map(str, args)],
                                cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def make_test_updater(self, folder, upstream):
        source = UPDATER.read_text(encoding="utf-8")
        pinned = "$Upstream = 'https://github.com/luvhscupid/CouncilFlow.git'"
        self.assertIn(pinned, source)
        path = Path(folder) / "remote-update.ps1"
        path.write_text(source.replace(pinned, f"$Upstream = '{upstream}'"), encoding="utf-8")
        return path

    def add_candidate_tree(self, work):
        for relative in (".agents/skills/council-flow", ".codex/agents"):
            shutil.copytree(ROOT / relative, work / relative, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        plugin = ROOT / "plugins/councilflow"
        if plugin.is_dir():
            shutil.copytree(plugin, work / "plugins/councilflow", dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        tests = work / "tests"
        tests.mkdir(exist_ok=True)
        (tests / "__init__.py").write_text("", encoding="utf-8")
        for name in ("test_skill_files", "test_contracts", "test_dispatch_lifecycle", "test_planner_contract"):
            (tests / f"{name}.py").write_text(
                "import unittest\nclass CandidateCheck(unittest.TestCase):\n def test_candidate(self): self.assertTrue(True)\n",
                encoding="utf-8")
        (work / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
        return tests

    def commit(self, work, message):
        self.git(work, "add", "--all")
        self.git(work, "-c", "user.name=CouncilFlow test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", message)
        return self.git(work, "rev-parse", "HEAD").stdout.strip()

    def test_stage_validate_activate_idempotent_failure_and_rollback(self):
        with tempfile.TemporaryDirectory(prefix="cf-remote-") as temp:
            base = Path(temp)
            home, work, bare = base / "home", base / "work", base / "upstream.git"
            home.mkdir(); work.mkdir()
            self.git(base, "init", "--bare", "--initial-branch=main", str(bare))
            self.git(work, "init", "--initial-branch=main")
            tests = self.add_candidate_tree(work)
            (work / ".agents/skills/council-flow/references/remote-marker.md").write_text("v1\n", encoding="utf-8")
            first = self.commit(work, "base")
            upstream = bare.as_uri()
            updater = self.make_test_updater(base, upstream)
            self.git(work, "remote", "add", "origin", upstream)
            self.git(work, "push", "-u", "origin", "main")

            self.run_ps(BOOTSTRAP, home, "-Install")
            manifest_path = home / ".councilflow/bootstrap.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            manifest["active_commit"] = first
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            (work / ".agents/skills/council-flow/references/remote-marker.md").write_text("v2\n", encoding="utf-8")
            second = self.commit(work, "eligible fast-forward")
            self.git(work, "push", "origin", "main")
            result = self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Activate")
            self.assertIn("activated", result.stdout.lower())
            installed = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            manifest = installed
            self.assertEqual(installed["active_commit"], second)
            self.assertTrue(installed.get("previous_source"), installed)
            self.assertTrue(Path(installed["active_source"]).is_relative_to(home / ".councilflow/versions"))
            self.assertIn("v2", (home / ".agents/skills/council-flow/references/remote-marker.md").read_text())

            # A divergent installed identity must fail the fast-forward check.
            self.git(work, "checkout", "-b", "divergent", first)
            (work / ".agents/skills/council-flow/references/remote-marker.md").write_text("divergent\n", encoding="utf-8")
            divergent = self.commit(work, "divergent version")
            manifest["active_commit"] = divergent
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Activate", expect=1)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["active_commit"], divergent)
            manifest["active_commit"] = second
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.git(work, "checkout", "main")

            repeated = self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Activate")
            self.assertIn("Already current", repeated.stdout)
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8-sig"))["active_commit"], second)

            # A candidate failing deterministic validation leaves the activated version intact.
            (tests / "test_contracts.py").write_text(
                "import unittest\nclass CandidateCheck(unittest.TestCase):\n def test_candidate(self): self.fail('reject candidate')\n",
                encoding="utf-8")
            third = self.commit(work, "invalid candidate")
            self.git(work, "push", "origin", "main")
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Activate", expect=1)
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8-sig"))["active_commit"], second)
            self.assertIn("v2", (home / ".agents/skills/council-flow/references/remote-marker.md").read_text())

            # Restore a valid candidate, then dirty the separate managed checkout: update refuses it.
            (tests / "test_contracts.py").write_text(
                "import unittest\nclass CandidateCheck(unittest.TestCase):\n def test_candidate(self): self.assertTrue(True)\n",
                encoding="utf-8")
            fourth = self.commit(work, "valid next candidate")
            self.git(work, "push", "origin", "main")
            active = Path(installed["active_source"])
            (active / "unexpected.txt").write_text("dirty", encoding="utf-8")
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Activate", expect=1)
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8-sig"))["active_commit"], second)
            (active / "unexpected.txt").unlink()

            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, "-Rollback")
            rolled = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            self.assertNotEqual(rolled["active_commit"], fourth)
            self.assertTrue(Path(rolled["active_source"]).is_dir())

    def test_rejects_unexpected_default_branch_missing_network_and_lock(self):
        with tempfile.TemporaryDirectory(prefix="cf-remote-check-") as temp:
            base = Path(temp); home = base / "home"; home.mkdir()
            work = base / "work"; work.mkdir()
            bare = base / "upstream.git"
            self.git(base, "init", "--bare", "--initial-branch=main", str(bare))
            self.git(work, "init", "--initial-branch=main")
            (work / "README.md").write_text("synthetic upstream\n", encoding="utf-8")
            self.git(work, "add", "README.md")
            self.git(work, "-c", "user.name=CouncilFlow test", "-c", "user.email=test@example.invalid", "commit", "-m", "initial")
            self.git(work, "remote", "add", "origin", bare.as_uri())
            self.git(work, "push", "-u", "origin", "main")
            upstream = bare.as_uri()
            updater = self.make_test_updater(base, upstream)
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home)
            self.git(bare, "symbolic-ref", "HEAD", "refs/heads/unexpected")
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, expect=1)
            missing_updater = self.make_test_updater(base, (base / "missing.git").as_uri())
            self.run_ps(missing_updater, home, "-RepoRoot", ROOT, "-UserHome", home, expect=1)
            lock = home / ".councilflow/remote-update.lock"
            lock.write_text("held", encoding="utf-8")
            self.run_ps(updater, home, "-RepoRoot", ROOT, "-UserHome", home, expect=1)

    @unittest.skipUnless(shutil.which("claude") and (ROOT / "plugins/councilflow").is_dir(),
                         "Claude CLI and plugin source are required for the inventory-growth control")
    def test_remote_candidate_cannot_claim_an_unmanaged_claude_destination(self):
        with tempfile.TemporaryDirectory(prefix="cf-inventory-") as temp:
            base = Path(temp)
            home, work, bare = base / "home", base / "work", base / "upstream.git"
            home.mkdir(); work.mkdir()
            self.git(base, "init", "--bare", "--initial-branch=main", str(bare))
            self.git(work, "init", "--initial-branch=main")
            self.add_candidate_tree(work)
            shutil.rmtree(work / "plugins/councilflow")
            scripts = work / "scripts"; scripts.mkdir()
            shutil.copy2(BOOTSTRAP, scripts / "bootstrap.ps1")
            upstream = bare.as_uri()
            updater = self.make_test_updater(base, upstream)
            shutil.copy2(updater, scripts / "remote-update.ps1")
            first = self.commit(work, "Codex-only release A")
            self.git(work, "remote", "add", "origin", upstream)
            self.git(work, "push", "-u", "origin", "main")

            unowned = home / ".claude/skills/councilflow/owner.txt"
            unowned.parent.mkdir(parents=True)
            unowned.write_text("Owner content stays intact", encoding="utf-8")
            self.run_ps(scripts / "bootstrap.ps1", home, "-Install")
            self.assertEqual(unowned.read_text(encoding="utf-8"), "Owner content stays intact")

            author = base / "release-b"
            self.git(base, "clone", "--branch", "main", upstream, str(author))
            shutil.copytree(ROOT / "plugins/councilflow", author / "plugins/councilflow")
            second = self.commit(author, "Release B adds optional Claude package")
            self.git(author, "push", "origin", "main")
            launcher = home / ".councilflow/launcher/remote-update.ps1"
            self.run_ps(launcher, home, "-RepoRoot", work, "-UserHome", home, "-Activate", expect=1)

            manifest = json.loads((home / ".councilflow/bootstrap.json").read_text(encoding="utf-8-sig"))
            self.assertEqual(manifest["active_commit"], first)
            self.assertNotEqual(manifest["active_commit"], second)
            self.assertEqual(unowned.read_text(encoding="utf-8"), "Owner content stays intact")


if __name__ == "__main__":
    unittest.main()
