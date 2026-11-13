"""Bounded maintenance integration controls, not a simulated native experiment.

Subprocess behavior is real. Packet actors are synthetic contract fixtures and
cannot establish native roles, activation, authentication or recovery enforcement.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_contracts as fixtures
import test_original_source as source_tests

c = fixtures.c


class WorkflowRecoveryTests(unittest.TestCase):
    def complete_context(self, root):
        helper = source_tests.OriginalSourceTests()
        packet, original, _, plan = helper.context(root)
        data = fixtures.sequence()
        data[0] = packet
        ids = [entry["id"] for entry in plan["acceptance"]]
        for message in data:
            message["payload"]["acceptance_ids"] = ids
        data[-1]["payload"]["results"] = [
            {"acceptance_id": identity, "status": "passed", "evidence_refs": [fixtures.ref()]}
            for identity in ids]
        # A completed Tester report is referenced externally by Reviewer, not
        # recursively hash-bound inside the Tester's own serialized message.
        data[4]["evidence_refs"] = [item for item in data[4]["evidence_refs"]
                                     if item["artifact_id"] != "tester-report"]

        def materialize(value):
            if isinstance(value, dict):
                if set(value) == {"artifact_id", "path", "sha256", "kind"}:
                    if value["artifact_id"] == "plan":
                        value.update(packet["payload"]["plan_ref"])
                    path = root / value["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if not path.exists():
                        path.write_bytes(b"Synthetic contract evidence; no native execution claim.\n")
                    value["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                else:
                    for child in value.values():
                        materialize(child)
            elif isinstance(value, list):
                for child in value:
                    materialize(child)

        for message in data:
            materialize(message)
            if message["message_id"] == "M5":
                (root / "synthetic/tester-report.json").write_bytes(json.dumps(message).encode())
        return data, original, plan

    def validate(self, messages, root, original):
        c.validate_sequence(messages, root=root, original_source_ref=original,
                            owner_provenance={"owner-original"}, require_criteria_fidelity=True)

    def test_complete_final_check_remains_bound_to_actual_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            messages, original, plan = self.complete_context(root)
            self.validate(messages, root, original)
            changed = copy.deepcopy(messages)
            changed[-1]["payload"]["results"][0]["status"] = "failed"
            with self.assertRaises(c.ContractError):
                self.validate(changed, root, original)
            # Rehash the entire internally consistent plan/reference ledger.
            # The retained original bytes still expose the rewritten text.
            plan["acceptance"][0]["criterion"] = plan["acceptance"][0]["criterion"].replace("`", "")
            (root / "plan.json").write_bytes(json.dumps(plan).encode())
            digest = hashlib.sha256((root / "plan.json").read_bytes()).hexdigest()
            def rehash(value):
                if isinstance(value, dict):
                    if value.get("artifact_id") == "plan":
                        value["sha256"] = digest
                    else:
                        for child in value.values(): rehash(child)
                elif isinstance(value, list):
                    for child in value: rehash(child)
            rehash(messages)
            with self.assertRaises(c.ContractError) as failure:
                self.validate(messages, root, original)
            self.assertEqual(failure.exception.code, "acceptance_fidelity")

    def test_final_validation_reopens_pinned_original_after_initial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            messages, original, _ = self.complete_context(root)
            self.validate(messages[:-1], root, original)
            source = root / original["path"]
            source.write_bytes(source.read_bytes().replace(b"`", b""))
            with self.assertRaises(c.ContractError) as failure:
                self.validate(messages, root, original)
            self.assertEqual(failure.exception.code, "artifact_hash")

    def test_real_pristine_oracle_catches_defect_hidden_by_weakened_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.py"
            candidate.write_text("def total(values):\n    return sum(values)\n", encoding="utf-8")
            oracle = root / "pristine-oracle.py"
            oracle.write_text(
                "import importlib.util,sys\n"
                "s=importlib.util.spec_from_file_location('candidate',sys.argv[1])\n"
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
                "actual=m.total([1,2,3])\n"
                "assert actual == 6, f'AC1 behavioral defect: {actual} != 6'\n"
                "print('AC1 total=6')\n", encoding="utf-8")
            oracle_ref = fixtures.ref("pristine-oracle", oracle.name,
                                      hashlib.sha256(oracle.read_bytes()).hexdigest(), "accepted-oracle")
            command = [sys.executable, "-B", str(oracle), str(candidate)]
            baseline = subprocess.run(command, cwd=root, capture_output=True, timeout=15)
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            # Worker edits both functionality and its own tests. The independent
            # oracle stays outside those edited candidate files and is hash-bound.
            candidate.write_text("def total(values):\n    return sum(values) - 1\n", encoding="utf-8")
            weakened = root / "test_weakened.py"
            weakened.write_text("import unittest\nclass Weak(unittest.TestCase):\n def test_total(self): self.assertTrue(True)\n", encoding="utf-8")
            weak = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(root),
                                   "-p", "test_weakened.py"], cwd=root, capture_output=True, timeout=15)
            self.assertEqual(weak.returncode, 0, weak.stderr)
            self.assertIn(b"Ran 1 test", weak.stderr)
            c.artifact(oracle_ref, root)
            independent = subprocess.run(command, cwd=root, capture_output=True, timeout=15)
            self.assertEqual(independent.returncode, 1)
            self.assertIn(b"AssertionError: AC1 behavioral defect: 5 != 6", independent.stderr)
            self.assertNotIn(b"ImportError", independent.stderr)
            candidate.write_text("def total(values):\n    return sum(values)\n", encoding="utf-8")
            tester = subprocess.run(command, cwd=root, capture_output=True, timeout=15)
            reviewer = subprocess.run(command, cwd=root, capture_output=True, timeout=15)
            self.assertEqual(tester.returncode, reviewer.returncode)
            self.assertEqual(tester.returncode, 0)
            normalized_hash = lambda output: hashlib.sha256(output.replace(b"\r\n", b"\n")).hexdigest()
            self.assertEqual(normalized_hash(tester.stdout), normalized_hash(reviewer.stdout))
            self.assertNotEqual(normalized_hash(tester.stdout + b"changed\n"), normalized_hash(reviewer.stdout))
            oracle.write_bytes(oracle.read_bytes().replace(b"actual == 6", b"True"))
            with self.assertRaises(c.ContractError):
                c.artifact(oracle_ref, root)

    def test_reviewer_real_rerun_rejects_false_deterministic_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "deterministic.py"
            script.write_bytes(b"print('actual candidate output')\n")
            args = ["-B", str(script)]
            actual = subprocess.run([sys.executable] + args, cwd=root, capture_output=True, timeout=15)
            data = fixtures.sequence()
            declared = data[4]["payload"]["deterministic_commands"][0]
            declared.update(command=sys.executable, arguments=args, workdir=str(root), exit_code=actual.returncode,
                            stdout_sha256=hashlib.sha256(b"false Tester result\n").hexdigest())
            rerun = data[6]["payload"]["comparison"]["independent_rerun"]
            rerun.update(command=sys.executable, arguments=args, workdir=str(root),
                         tester_exit_code=declared["exit_code"], tester_stdout_sha256=declared["stdout_sha256"],
                         exit_code=actual.returncode, stdout_sha256=hashlib.sha256(actual.stdout.replace(b"\r\n", b"\n")).hexdigest(),
                         status="MISMATCH")
            data[6]["payload"]["status"] = "failed"
            c.validate_sequence(data[:7])
            with self.assertRaises(c.ContractError):
                c.validate_sequence(data)

    def test_infrastructure_timeout_is_observed_without_success_or_role_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.TimeoutExpired):
                subprocess.run([sys.executable, "-B", "-c", "import time; time.sleep(10)"],
                               cwd=directory, capture_output=True, timeout=0.1)
        data = fixtures.sequence()[:5]
        data[-1]["payload"]["status"] = "blocked"
        data[-1]["payload"]["checks"][0]["status"] = "blocked"
        data[-1]["payload"]["errors"] = [{"code": "infrastructure_timeout", "field": "command", "message": "Observed timeout; not a passed check."}]
        c.validate_sequence(data)
        data.extend(fixtures.sequence()[5:])
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)


if __name__ == "__main__":
    unittest.main()
