"""contracts.py save: only full council-flow packets reach a run's messages/ folder.

Regression for the first dogfood run (dashboard-issues-1), where Worker, Tester and
Reviewer reports were saved as bare payload bodies. Fixtures are synthetic packets
from test_contracts plus a verbatim copy of that run's bare M003 report body.
"""
import hashlib
import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fixtures

c = fixtures.c
ROOT = Path(__file__).resolve().parents[1]
BARE = ROOT / "tests/fixtures/bare-worker-report-M003.json"
COPIES = (ROOT / ".agents/skills/council-flow/scripts/contracts.py",
          ROOT / "plugins/councilflow/skills/run/scripts/contracts.py")


def raw(message):
    return (json.dumps(message, indent=1) + "\n").encode("utf-8")


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / ".councilflow/runs/T1"
        self.run.mkdir(parents=True)
        self.messages = self.run / "messages"

    def tearDown(self):
        self.tmp.cleanup()

    def saved(self):
        return sorted(p.name for p in self.messages.glob("*")) if self.messages.exists() else []

    def assertRefused(self, data, code):
        before = {p.name: p.read_bytes() for p in self.messages.glob("*")} if self.messages.exists() else {}
        with self.assertRaises(c.ContractError) as failure:
            c.save_message(data, self.run)
        self.assertEqual(failure.exception.code, code)
        after = {p.name: p.read_bytes() for p in self.messages.glob("*")} if self.messages.exists() else {}
        self.assertEqual(before, after, "a refused save must not write or change any file")

    def test_full_run_saved_packet_by_packet_passes_sequence(self):
        """AC1 + AC5: every packet of a full run saves; the saved folder passes sequence."""
        sequence = fixtures.sequence()
        for message in sequence:
            data = raw(message)
            result = c.save_message(data, self.run)
            self.assertTrue(result["saved"])
            self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual((self.messages / (message["message_id"] + ".json")).read_bytes(), data)
        self.assertEqual(self.saved(), sorted(m["message_id"] + ".json" for m in sequence))
        saved = [c.read_json(p) for p in self.messages.glob("*.json")]
        c.validate_sequence(c._run_order(saved))

    def test_demo_bare_report_body_is_refused(self):
        """AC2: the dogfood run's M003 shape (payload with no envelope) is refused."""
        c.save_message(raw(fixtures.sequence()[0]), self.run)
        c.save_message(raw(fixtures.sequence()[1]), self.run)
        self.assertRefused(BARE.read_bytes(), "bare_payload")
        self.assertEqual(self.saved(), ["M1.json", "M2.json"])

    def test_report_out_of_order_is_refused(self):
        """AC3: a full Worker report with no saved job.assign before it is refused."""
        sequence = fixtures.sequence()
        c.save_message(raw(sequence[0]), self.run)
        self.assertRefused(raw(sequence[2]), "causal_reference")

    def test_invalid_full_packet_is_refused(self):
        report = fixtures.sequence()[2]
        del report["payload"]["candidate_ref"]
        self.assertRefused(raw(report), "required")

    def test_existing_message_is_never_overwritten(self):
        """AC4: saving the same message id again is refused; the first file is unchanged."""
        first = fixtures.sequence()[0]
        c.save_message(raw(first), self.run)
        changed = json.loads(json.dumps(first))
        changed["payload"]["objective"] = "changed"
        self.assertRefused(raw(changed), "message_exists")

    def test_unsafe_message_id_and_linked_folders_are_refused(self):
        first = fixtures.sequence()[0]
        first["message_id"] = "../escape"
        self.assertRefused(raw(first), "message_file_name")
        with self.assertRaises(c.ContractError) as failure:
            c.save_message(raw(fixtures.sequence()[0]), self.run / "missing")
        self.assertEqual(failure.exception.code, "run_folder")
        other = Path(self.tmp.name) / "elsewhere"
        other.mkdir()
        try:
            self.messages.symlink_to(other, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaises(c.ContractError) as failure:
            c.save_message(raw(fixtures.sequence()[0]), self.run)
        self.assertEqual(failure.exception.code, "run_folder")
        self.assertEqual(list(other.iterdir()), [])

    def test_cli_save_refreshes_the_project_board(self):
        """A save into .councilflow/runs/<task> republishes the run and project boards."""
        env = {**os.environ, "CI": "1"}  # never open a browser from the test run
        for script in COPIES:
            if not script.exists():
                continue
            with self.subTest(copy=script.parent.parent.name), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp) / "proj"
                run = project / ".councilflow" / "runs" / "T1"
                run.mkdir(parents=True)
                packet = Path(tmp) / "M1.json"
                packet.write_bytes(raw(fixtures.sequence()[0]))
                ok = subprocess.run([sys.executable, "-I", str(script), "save", str(packet), "--run", str(run)],
                                    capture_output=True, text=True, env=env)
                self.assertEqual(ok.returncode, 0, ok.stderr)
                board = json.loads(ok.stdout)["dashboard"]
                self.assertNotIn("error", board)
                self.assertIsNone(board["opened"])
                self.assertEqual(Path(board["board"]), (project / ".councilflow/dashboard.html").resolve())
                self.assertIn('"taskId":"T1"', (project / ".councilflow/dashboard.html").read_text(encoding="utf-8"))
                self.assertTrue((run / "dashboard.html").is_file())
                self.assertEqual(sorted(p.name for p in (run / "messages").iterdir()), ["M1.json"])

                second = Path(tmp) / "M2.json"
                second.write_bytes(raw(fixtures.sequence()[1]))
                skipped = subprocess.run([sys.executable, "-I", str(script), "save", str(second), "--run", str(run),
                                          "--no-dashboard"], capture_output=True, text=True, env=env)
                self.assertEqual(skipped.returncode, 0, skipped.stderr)
                self.assertNotIn("dashboard", json.loads(skipped.stdout))

    def test_cli_in_both_copies(self):
        """The Codex skill and the Claude plugin copy give the same save behavior."""
        for script in COPIES:
            if not script.exists():
                continue  # the portable release archive ships only the Codex skill copy
            with self.subTest(copy=script.parent.parent.name), tempfile.TemporaryDirectory() as tmp:
                run = Path(tmp) / "run"
                run.mkdir()
                packet = Path(tmp) / "M1.json"
                packet.write_bytes(raw(fixtures.sequence()[0]))
                ok = subprocess.run([sys.executable, "-I", str(script), "save", str(packet), "--run", str(run)],
                                    capture_output=True, text=True)
                self.assertEqual(ok.returncode, 0, ok.stderr)
                self.assertTrue(json.loads(ok.stdout)["saved"])
                self.assertNotIn("dashboard", json.loads(ok.stdout), "only canonical run folders get a board")
                bad = subprocess.run([sys.executable, "-I", str(script), "save", str(BARE), "--run", str(run)],
                                     capture_output=True, text=True)
                self.assertEqual(bad.returncode, 1)
                self.assertEqual(json.loads(bad.stderr)["error"], "bare_payload")
                again = subprocess.run([sys.executable, "-I", str(script), "save", str(packet), "--run", str(run)],
                                       capture_output=True, text=True)
                self.assertEqual(json.loads(again.stderr)["error"], "message_exists")
                misuse = subprocess.run([sys.executable, "-I", str(script), "message", str(packet), "--run", str(run)],
                                        capture_output=True, text=True)
                self.assertEqual(json.loads(misuse.stderr)["error"], "save_mode")
                self.assertEqual(sorted(p.name for p in (run / "messages").iterdir()), ["M1.json"])


if __name__ == "__main__":
    unittest.main()
