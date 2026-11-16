"""Offline CLI and release relocation controls; no live host compatibility claim."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(".agents/skills/council-flow")
ENTRY = SKILL / "scripts/efficiency.py"
spec = importlib.util.spec_from_file_location("efficiency_release", ROOT / "tools/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InstalledEfficiencyTests(unittest.TestCase):
    def run_cli(self, root, *args, input=None):
        env = {**os.environ, "PYTHONPATH": ""}
        return subprocess.run([sys.executable, "-I", str(root / ENTRY), *map(str, args)],
                              cwd=root, env=env, input=input, capture_output=True, timeout=20)

    def exercise(self, root):
        fields = root / "record-input.json"
        fields.write_text(json.dumps({"run_id": "offline-install", "harness": "codex",
                                      "route": "codex/native-or-configured"}), encoding="utf-8")
        records = root / "records.jsonl"
        result = self.run_cli(root, "record", fields, "--records", records)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(records.read_text())
        self.assertIsNone(record["usage"]["reported_cost"])
        self.assertEqual(record["acceptance"]["status"], "unknown")
        fields.write_text('{"harness":"invented"}', encoding="utf-8")
        original = records.read_bytes()
        self.assertEqual(self.run_cli(root, "record", fields, "--records", records).returncode, 2)
        self.assertEqual(records.read_bytes(), original)

        digest = root / "capture.json"
        result = self.run_cli(root, "digest", "run", "--artifacts", root / "artifacts",
                              "--digest-output", digest, "--", sys.executable, "-c",
                              "import sys; sys.stdout.buffer.write(b'complete\\r\\n'); sys.stderr.write('failure detail'); sys.exit(7)")
        self.assertEqual(result.returncode, 7, result.stderr)
        capture = json.loads(digest.read_text())
        self.assertIn("COMMAND_FAILED", capture["flags"])
        self.assertEqual(self.run_cli(root, "digest", "expand", digest, "stdout").stdout, b"complete\r\n")
        self.assertEqual(self.run_cli(root, "digest", "expand", digest, "stderr").stdout, b"failure detail")
        artifact = Path(capture["artifact_dir"]) / capture["streams"]["stdout"]["artifact"]
        artifact.write_bytes(b"changed")
        self.assertNotEqual(self.run_cli(root, "digest", "expand", digest, "stdout").returncode, 0)

        for adapter, fixture in (("codex", "codex-exec-sanitized.jsonl"),
                                 ("claude", "claude-stream-sanitized.jsonl")):
            result = self.run_cli(root, adapter, "--artifacts", root / adapter,
                                  "--source", "synthetic-fixture", "--process-exit-code", "0",
                                  input=(ROOT / "tests/efficiency-fixtures" / fixture).read_bytes())
            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = json.loads(result.stdout)
            self.assertTrue(parsed["complete"])
            self.assertIsNone(parsed["record"]["usage"]["reported_cost"])
            self.assertIsNone(parsed["session_usage"])

    def test_skill_only_copy_runs_from_unrelated_repository(self):
        with tempfile.TemporaryDirectory(prefix="councilflow-install-") as directory:
            root = Path(directory) / "other repository"
            shutil.copytree(ROOT / SKILL, root / SKILL, ignore=shutil.ignore_patterns("__pycache__"))
            self.exercise(root)

    def test_release_inventory_bytes_determinism_and_extracted_cli(self):
        with tempfile.TemporaryDirectory(prefix="councilflow-release-") as directory:
            root = Path(directory) / "source"
            sources = builder.source_bytes(ROOT)
            for name, data in sources.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            report = builder.build(root)
            archive = root / report["archive"]
            first = archive.read_bytes()
            self.assertEqual(builder.build(root)["sha256"], report["sha256"])
            self.assertEqual(archive.read_bytes(), first)
            self.assertEqual(hashlib.sha256(first).hexdigest(), report["sha256"])
            self.assertEqual((root / "dist/council-flow.zip.sha256").read_text().split()[0], report["sha256"])
            extracted = Path(directory) / "extracted"
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertEqual(set(bundle.namelist()), set(sources))
                for name in bundle.namelist():
                    self.assertTrue(builder.safe_name(name))
                    self.assertEqual(bundle.read(name), sources[name])
                    self.assertFalse(name.startswith(("experiments/", "reports/integration-", "owner-fixtures/")))
                for required in (ENTRY, SKILL / "references/efficiency.md",
                                 SKILL / "scripts/efficiency/recorder.py",
                                 "demo/gate3-demo/app.py", "tests/test_efficiency_recorder.py"):
                    self.assertIn(str(required).replace("\\", "/"), bundle.namelist())
                bundle.extractall(extracted)
            self.exercise(extracted)

    def test_local_run_output_is_excluded_inside_allowlisted_skill(self):
        self.assertTrue(builder.excluded(".agents/skills/council-flow/.local-runs/private.json"))
        self.assertTrue(builder.excluded("tests/__pycache__/test.pyc"))


if __name__ == "__main__":
    unittest.main()
