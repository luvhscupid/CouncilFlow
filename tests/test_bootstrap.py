"""Isolated Windows bootstrap lifecycle and collision tests."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "PowerShell is required for bootstrap integration tests")
class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, home, *args, expect=0):
        env = os.environ.copy()
        env["COUNCILFLOW_BOOTSTRAP_HOME"] = str(home)
        result = subprocess.run([POWERSHELL, "-NoProfile", "-File", str(BOOTSTRAP), *args],
                                cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def test_install_status_update_no_change_and_uninstall_in_isolated_home(self):
        with tempfile.TemporaryDirectory(prefix="councilflow-home-") as temp:
            home = Path(temp)
            identical = home / ".codex/agents/council-worker.toml"
            identical.parent.mkdir(parents=True)
            identical.write_bytes((ROOT / ".codex/agents/council-worker.toml").read_bytes())
            self.run_bootstrap(home, "-Install", "-DryRun")
            self.assertFalse((home / ".councilflow/bootstrap.json").exists())
            first = self.run_bootstrap(home, "-Install")
            self.assertIn("Local synchronization", first.stdout)
            manifest = json.loads((home / ".councilflow/bootstrap.json").read_text(encoding="utf-8-sig"))
            self.assertGreaterEqual(len(manifest["installs"]), 5)
            self.assertTrue(any(record["mode"] == "copy" for record in manifest["installs"]))
            worker_record = next(record for record in manifest["installs"] if record["id"] == "role-council-worker")
            self.assertEqual(worker_record["mode"], "copy")
            self.run_bootstrap(home, "-Status")
            self.run_bootstrap(home, "-Install")
            original = identical.read_bytes()
            identical.write_text("locally modified", encoding="utf-8")
            self.run_bootstrap(home, "-Update", expect=1)
            self.assertEqual(identical.read_text(encoding="utf-8"), "locally modified")
            identical.write_bytes(original)
            self.run_bootstrap(home, "-Update")
            self.run_bootstrap(home, "-Update")
            self.assertTrue((home / ".agents/skills/council-flow/SKILL.md").is_file())
            self.run_bootstrap(home, "-Uninstall")
            self.assertFalse((home / ".agents/skills/council-flow").exists())

    def test_automatic_task_registration_is_opt_in_and_dry_run_only(self):
        with tempfile.TemporaryDirectory(prefix="councilflow-task-dryrun-") as temp:
            home = Path(temp)
            self.run_bootstrap(home, "-Install")
            result = self.run_bootstrap(home, "-EnableAutomatic", "-DryRun")
            self.assertIn("DRY-RUN register daily Task Scheduler task", result.stdout)
            self.assertIn("remote-update.ps1", result.stdout)
            manifest = json.loads((home / ".councilflow/bootstrap.json").read_text(encoding="utf-8-sig"))
            self.assertEqual(len(manifest["launcher"]), 2)

    def test_collision_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="councilflow-collision-") as temp:
            home = Path(temp)
            target = home / ".agents/skills/council-flow"
            target.mkdir(parents=True)
            marker = target / "owner-file.txt"
            marker.write_text("preserve", encoding="utf-8")
            self.run_bootstrap(home, "-Install", expect=1)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
            self.assertFalse((home / ".claude/skills/councilflow").exists())
            self.assertFalse((home / ".codex/agents/council-worker.toml").exists())


if __name__ == "__main__":
    unittest.main()
