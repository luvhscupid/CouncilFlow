import json
import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from doctor import diagnose, load_evidence


class DoctorTests(unittest.TestCase):
    def test_schema_v1_output_contract_is_unchanged(self):
        self.assertEqual(diagnose({"schema_version": 1}), [
            {"check": "evidence_schema", "status": "PASS", "detail": "top-level evidence object uses schema version 1"},
            {"check": "source_integrity", "status": "BLOCKED", "detail": "source artifact reference is missing"},
            {"check": "native_role_sequence", "status": "BLOCKED", "detail": "native role evidence references are missing"},
            {"check": "independent_tester", "status": "BLOCKED", "detail": "required evidence is missing"},
            {"check": "reviewer_rerun", "status": "BLOCKED", "detail": "required evidence is missing"},
            {"check": "planner_final_check", "status": "BLOCKED", "detail": "required evidence is missing"},
            {"check": "dashboard", "status": "SKIP", "detail": "optional dashboard projection is not configured"},
        ])

    def test_missing_native_role_evidence_is_blocked(self):
        result = diagnose({"schema_version": 1, "native_role_evidence": []})
        native = next(item for item in result if item["check"] == "native_role_sequence")
        self.assertEqual(native["status"], "BLOCKED")

    def test_complete_claimed_roles_remain_unverified_and_dashboard_skips(self):
        roles = ["planner", "worker", "tester", "reviewer"]
        result = diagnose({"schema_version": 1, "native_role_evidence": [
            {"role": role, "identity": f"claimed-{role}", "evidence_ref": f"sessions/{role}.json"}
            for role in roles], "dashboard": None})
        self.assertEqual(next(item for item in result if item["check"] == "native_role_sequence")["status"], "UNVERIFIED")
        self.assertEqual(next(item for item in result if item["check"] == "dashboard")["status"], "SKIP")

    def test_self_reported_role_names_and_success_booleans_do_not_pass(self):
        roles = ["planner", "worker", "tester", "reviewer"]
        result = diagnose({"schema_version": 1, "native_role_evidence": [
                               {"role": role, "identity": role, "evidence_ref": f"{role}.json"} for role in roles],
                           "source_hash_valid": True, "tester_evidence": True,
                           "reviewer_rerun": True, "planner_check": True})
        self.assertTrue(all(item["status"] == "UNVERIFIED" for item in result if item["check"] in {
            "source_integrity", "native_role_sequence", "independent_tester", "reviewer_rerun", "planner_final_check"}))

    def test_valid_source_artifact_is_hashed_from_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "source.txt"
            artifact.write_bytes(b"source bytes")
            expected = hashlib.sha256(b"source bytes").hexdigest()
            result = diagnose({"schema_version": 1, "source_artifact": {"path": "source.txt", "sha256": expected}}, root)
            source = next(item for item in result if item["check"] == "source_integrity")
            self.assertEqual(source["status"], "PASS")
            self.assertEqual(source["detail"], "referenced source bytes match the declared SHA-256")

    def test_v2_null_executable_and_host_evidence_are_blocked(self):
        result = diagnose({"schema_version": 2, "executable_artifact": None, "native_host": None})
        self.assertEqual(next(item for item in result if item["check"] == "executable_integrity")["status"], "BLOCKED")
        self.assertEqual(next(item for item in result if item["check"] == "native_host")["status"], "BLOCKED")

    def test_v2_hashes_executable_bytes_and_keeps_native_host_claim_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "tool.bin"
            marker = root / "was-executed"
            executable = f"#!/bin/sh\ntouch '{marker}'\n".encode()
            artifact.write_bytes(executable)
            os.chmod(artifact, 0o755)
            result = diagnose({
                "schema_version": 2,
                "executable_artifact": {"path": "tool.bin", "sha256": hashlib.sha256(executable).hexdigest()},
                "native_host": {"name": "Codex", "version": "caller-version", "evidence_ref": "host.json"},
            }, root)
            self.assertFalse(marker.exists())
        self.assertEqual(next(item for item in result if item["check"] == "executable_integrity")["status"], "PASS")
        self.assertEqual(next(item for item in result if item["check"] == "native_host")["status"], "UNVERIFIED")

    def test_v2_malformed_records_digest_mismatch_and_missing_fields_fail(self):
        malformed = diagnose({"schema_version": 2, "executable_artifact": {"path": "tool", "sha256": "bad"},
                              "native_host": {"name": "Codex", "version": "1"}})
        self.assertEqual(next(item for item in malformed if item["check"] == "executable_integrity")["status"], "FAIL")
        self.assertEqual(next(item for item in malformed if item["check"] == "native_host")["status"], "FAIL")
        with self.assertRaises(ValueError):
            diagnose({"schema_version": 2, "executable_artifact": None})
        with self.assertRaises(ValueError):
            diagnose({"schema_version": 3, "executable_artifact": None, "native_host": None})
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "tool"
            artifact.write_bytes(b"actual")
            result = diagnose({"schema_version": 2,
                               "executable_artifact": {"path": "tool", "sha256": "0" * 64},
                               "native_host": None}, tmp)
        self.assertEqual(next(item for item in result if item["check"] == "executable_integrity")["status"], "FAIL")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_v2_symlink_executable_fails_without_reading_target(self):
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            root, outside = Path(root_dir), Path(outside_dir)
            target = outside / "tool"
            target.write_bytes(b"outside")
            (root / "link").symlink_to(target)
            result = diagnose({"schema_version": 2,
                               "executable_artifact": {"path": "link", "sha256": hashlib.sha256(b"outside").hexdigest()},
                               "native_host": None}, root)
        self.assertEqual(next(item for item in result if item["check"] == "executable_integrity")["status"], "FAIL")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are unavailable")
    def test_v2_fifo_executable_reference_returns_without_blocking(self):
        script = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts" / "doctor.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            os.mkfifo(root / "tool.pipe")
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps({"schema_version": 2,
                                            "executable_artifact": {"path": "tool.pipe", "sha256": "0" * 64},
                                            "native_host": None}), encoding="utf-8")
            run = subprocess.run([sys.executable, "-B", str(script), str(evidence)],
                                 capture_output=True, text=True, timeout=2)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(next(item for item in result if item["check"] == "executable_integrity")["status"], "BLOCKED")

    def test_source_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.txt").write_bytes(b"actual")
            result = diagnose({"schema_version": 1, "source_artifact": {"path": "source.txt", "sha256": "0" * 64}}, root)
            self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "FAIL")

    def test_source_path_traversal_fails_closed(self):
        result = diagnose({"schema_version": 1, "source_artifact": {"path": "../outside", "sha256": "0" * 64}}, Path.cwd())
        self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "FAIL")

    def test_source_symlink_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (Path(outside) / "source.txt").write_bytes(b"outside")
            (root / "link").symlink_to(Path(outside) / "source.txt")
            result = diagnose({"schema_version": 1, "source_artifact": {"path": "link", "sha256": hashlib.sha256(b"outside").hexdigest()}}, root)
            self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "FAIL")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_source_symlink_inside_root_fails_without_following(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.txt"
            target.write_bytes(b"source")
            (root / "link.txt").symlink_to(target)
            result = diagnose({"schema_version": 1,
                               "source_artifact": {"path": "link.txt", "sha256": hashlib.sha256(b"source").hexdigest()}}, root)
        self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "FAIL")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are unavailable")
    def test_fifo_reference_returns_without_blocking(self):
        script = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts" / "doctor.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            os.mkfifo(root / "source.pipe")
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps({"schema_version": 1,
                                            "source_artifact": {"path": "source.pipe", "sha256": "0" * 64}}),
                                encoding="utf-8")
            run = subprocess.run([sys.executable, "-B", str(script), str(evidence)],
                                 capture_output=True, text=True, timeout=2)
        result = json.loads(run.stdout)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(next(item for item in result if item["check"] == "source_integrity")["status"], "BLOCKED")

    def test_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            load_evidence('{"source_hash_valid":false,"source_hash_valid":true}')

    def test_malformed_schema_and_non_finite_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            diagnose({"schema_version": True})
        with self.assertRaises(ValueError):
            diagnose({"schema_version": 1, "required_roles": ["worker"]})
        with self.assertRaises(ValueError):
            load_evidence('{"schema_version":NaN}')
        malformed = diagnose({"schema_version": 1, "tester_evidence": "yes"})
        self.assertEqual(next(item for item in malformed if item["check"] == "independent_tester")["status"], "FAIL")

    def test_cli_reads_file_and_stdin_and_rejects_bad_input(self):
        script = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "council-flow" / "scripts" / "doctor.py"
        payload = json.dumps({"schema_version": 1, "native_role_evidence": []})
        with tempfile.TemporaryDirectory() as tmp:
            evidence_file = Path(tmp) / "evidence.json"
            evidence_file.write_text(payload, encoding="utf-8")
            file_run = subprocess.run([sys.executable, "-B", str(script), str(evidence_file)], capture_output=True, text=True)
        stdin_run = subprocess.run([sys.executable, "-B", str(script), "-"], input=payload, capture_output=True, text=True)
        bad_run = subprocess.run([sys.executable, "-B", str(script), "-"], input="{bad", capture_output=True, text=True)
        self.assertEqual(file_run.returncode, 0)
        self.assertEqual(stdin_run.returncode, 0)
        self.assertEqual(json.loads(stdin_run.stdout)[1]["status"], "BLOCKED")
        self.assertEqual(bad_run.returncode, 2)


if __name__ == "__main__":
    unittest.main()
