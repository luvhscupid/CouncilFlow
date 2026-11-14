"""Maintenance controls; synthetic packets never prove native activation or roles."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts as c
from test_contracts import assignment, publish, ref, sequence


class OriginalSourceTests(unittest.TestCase):
    def context(self, root, raw=None, acceptance=None):
        original = root / "owner-original.txt"
        original.write_bytes(raw if raw is not None else (ROOT / "tests/fixtures/owner-version-original.txt").read_bytes())
        original_ref = ref("owner-original", original.name, hashlib.sha256(original.read_bytes()).hexdigest(), "owner-original-source")
        captured = c.capture_criteria(original_ref, root, owner_provenance={"owner-original"})
        derivative = root / "owner-criteria.json"
        derivative.write_bytes(json.dumps(captured, ensure_ascii=False).encode("utf-8"))
        derivative_ref = ref("derived", derivative.name, hashlib.sha256(derivative.read_bytes()).hexdigest(), "owner-approved-criteria")
        plan = {"plan_id": "P1", "plan_revision": 1, "original_source_ref": original_ref,
                "acceptance": captured["criteria"] if acceptance is None else acceptance,
                "metadata": {"maintenance_control": True}}
        packet = self.write_plan(root, plan)
        return packet, original_ref, derivative_ref, plan

    def write_plan(self, root, plan):
        path = root / "plan.json"
        path.write_bytes(json.dumps(plan, ensure_ascii=False).encode("utf-8"))
        packet = publish()
        packet["payload"]["acceptance_ids"] = [entry["id"] for entry in plan["acceptance"]]
        packet["payload"]["plan_ref"] = ref("plan", path.name, hashlib.sha256(path.read_bytes()).hexdigest(), "plan")
        packet["evidence_refs"] = [packet["payload"]["plan_ref"]]
        return packet

    def validate(self, packet, root, original, derivative=None):
        return c.validate_sequence([packet], root=root, original_source_ref=original,
                                   authoritative_criteria_ref=derivative,
                                   owner_provenance={"owner-original"}, require_criteria_fidelity=True)

    def test_derivative_only_is_rejected_in_required_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            altered = [{"id": "AC1", "criterion": "When invoked with --version, print exactly 1.0.0 followed by a newline."}]
            derivative = root / "owner-criteria.json"
            derivative.write_bytes(json.dumps({"criteria": altered}).encode())
            plan = root / "plan.json"
            plan.write_bytes(json.dumps({"plan_id": "P1", "plan_revision": 1, "acceptance": altered}).encode())
            packet = publish()
            packet["payload"]["acceptance_ids"] = ["AC1"]
            packet["payload"]["plan_ref"] = ref("plan", "plan.json", hashlib.sha256(plan.read_bytes()).hexdigest())
            packet["evidence_refs"] = [packet["payload"]["plan_ref"]]
            derivative_ref = ref("derived", "owner-criteria.json", hashlib.sha256(derivative.read_bytes()).hexdigest(), "owner-approved-criteria")
            with self.assertRaises(c.ContractError):
                c.validate_sequence([packet], root=root, authoritative_criteria_ref=derivative_ref,
                                    require_criteria_fidelity=True)

    def test_direct_failure_repair_requires_rework(self):
        messages = sequence()[:5]
        messages[-1]["payload"]["status"] = "failed"
        repair = assignment("REPAIR", "worker", "M5", ref(), instance="worker-1")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(messages + [repair])

    def test_actual_saved_fixture_survives_capture_publish_and_dispatch(self):
        fixture = (ROOT / "tests/fixtures/owner-version-original.txt").read_bytes()
        self.assertEqual(hashlib.sha256(fixture).hexdigest(), "e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, derivative, plan = self.context(root)
            self.validate(packet, root, original, derivative)
            self.assertEqual(plan["acceptance"][0]["criterion"], "When invoked with `--version`, print exactly `1.0.0` followed by a newline.")
            self.assertEqual(plan["acceptance"][1]["criterion"], "The `--version` invocation exits with status code 0.")
            dispatch = assignment("M2", "worker", "M1")
            dispatch["payload"]["acceptance_ids"] = ["AC1", "AC2", "AC3"]
            dispatch["evidence_refs"] = [original, derivative, packet["payload"]["plan_ref"]]
            c.validate_sequence([packet, dispatch], root=root, original_source_ref=original,
                                owner_provenance={"owner-original"}, require_criteria_fidelity=True)
            self.assertEqual((root / original["path"]).read_bytes(), fixture)

    def test_actual_fixture_plan_mutations_rejected_despite_rehashed_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, original, _, plan = self.context(root)
            original_acceptance = copy.deepcopy(plan["acceptance"])
            mutations = []
            for transform in (lambda s: s.replace("`", ""), lambda s: s.replace(",", ";"),
                              lambda s: s.replace("When", "when"), lambda s: s.replace("print exactly", "print  exactly"),
                              lambda s: s.replace("1.0.0", "2.0.0")):
                changed = copy.deepcopy(original_acceptance)
                changed[0]["criterion"] = transform(changed[0]["criterion"])
                mutations.append(changed)
            mutations.extend([original_acceptance[:-1], list(reversed(original_acceptance)),
                              [original_acceptance[0], original_acceptance[0], original_acceptance[2]],
                              original_acceptance + [{"id": "AC4", "criterion": "New mandatory demand."}]])
            for index, changed in enumerate(mutations):
                plan["acceptance"] = changed
                packet = self.write_plan(root, plan)
                with self.subTest(mutation=index), self.assertRaises(c.ContractError):
                    self.validate(packet, root, original)

    def test_self_consistent_derivative_and_plan_cannot_replace_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, original, derivative, plan = self.context(root)
            for entry in plan["acceptance"]:
                entry["criterion"] = entry["criterion"].replace("`", "")
            path = root / derivative["path"]
            path.write_bytes(json.dumps({"criteria": plan["acceptance"]}).encode())
            derivative["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            packet = self.write_plan(root, plan)
            for item in (packet,):
                c.validate_message(item, root=root)  # Individually valid is insufficient.
            with self.assertRaises(c.ContractError) as failure:
                self.validate(packet, root, original, derivative)
            self.assertEqual(failure.exception.code, "acceptance_fidelity")

    def test_missing_stale_and_replaced_original_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, derivative, _ = self.context(root)
            path = root / original["path"]
            raw = path.read_bytes()
            path.unlink()
            with self.assertRaises(c.ContractError) as missing:
                self.validate(packet, root, original, derivative)
            self.assertEqual(missing.exception.code, "artifact_missing")
            path.write_bytes(raw.replace(b"`", b""))
            with self.assertRaises(c.ContractError) as stale:
                self.validate(packet, root, original, derivative)
            self.assertEqual(stale.exception.code, "artifact_hash")

    def test_generated_json_is_not_an_original_input_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, _, derivative, plan = self.context(root)
            pretend = dict(derivative, kind="owner-original-source", artifact_id="owner-original")
            plan["original_source_ref"] = pretend
            packet = self.write_plan(root, plan)
            with self.assertRaises(c.ContractError) as failure:
                self.validate(packet, root, pretend)
            self.assertEqual(failure.exception.code, "criteria_source")

    def test_source_provenance_is_required_separately_from_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, _, _ = self.context(root)
            with self.assertRaises(c.ContractError) as failure:
                c.validate_sequence([packet], root=root, original_source_ref=original, require_criteria_fidelity=True)
            self.assertEqual(failure.exception.code, "owner_provenance")

    def test_derivative_and_plan_source_lineage_cannot_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, derivative, plan = self.context(root)
            changed = dict(original, artifact_id="different-original")
            path = root / derivative["path"]
            path.write_bytes(json.dumps({"source_ref": changed, "criteria": plan["acceptance"]}).encode())
            derivative["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(c.ContractError):
                self.validate(packet, root, original, derivative)
            plan["original_source_ref"] = changed
            with self.assertRaises(c.ContractError):
                self.validate(self.write_plan(root, plan), root, original)

    def test_original_and_derivative_cannot_rebind_one_artifact_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, derivative, _ = self.context(root)
            derivative["artifact_id"] = original["artifact_id"]
            with self.assertRaises(c.ContractError) as failure:
                self.validate(packet, root, original, derivative)
            self.assertEqual(failure.exception.code, "artifact_identity")

    def test_frozen_whitespace_unicode_and_line_endings_are_not_normalized(self):
        for ending in (b"\n", b"\r\n"):
            raw = b"Task." + ending + b"AC1: Keep\t`two  spaces` ." + ending + "  café\u0301".encode() + ending
            with self.subTest(ending=ending), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                packet, original, _, plan = self.context(root, raw)
                self.validate(packet, root, original)
                expected = b"Keep\t`two  spaces` ." + ending + "  café\u0301".encode()
                self.assertEqual(plan["acceptance"][0]["criterion"].encode(), expected)
                plan["acceptance"][0]["criterion"] = plan["acceptance"][0]["criterion"].replace("\t", " ")
                with self.assertRaises(c.ContractError):
                    self.validate(self.write_plan(root, plan), root, original)

    def test_ambiguous_missing_duplicate_or_unsupported_labels_fail_closed(self):
        variants = [b"No criteria", b"AC1: One.\nAC1: Duplicate.\n", b" AC1: Indented.\n",
                    b"AC1: One.\n- AC2: Hidden.\n", b"AC1: One.\n**AC2:** Hidden.\n",
                    b"AC0: Zero.\n", b"AC1: \xff\n",
                    b"AC1: One.\rAC2: Two.", b"AC1: " + b"x" * c.MAX_BYTES]
        for raw in variants:
            with self.subTest(raw=raw[:50]), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(c.ContractError):
                    self.context(root, raw)

    def test_cli_capture_and_dispatch_use_original_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet, original, _, _ = self.context(root)
            original_path = root / "original-ref.json"
            original_path.write_bytes(json.dumps(original).encode())
            packet_path = root / "publish.json"
            packet_path.write_bytes(json.dumps(packet).encode())
            command = [sys.executable, str(ROOT / ".agents/skills/council-flow/scripts/contracts.py")]
            capture = subprocess.run(command + ["capture", str(original_path), "--root", str(root),
                                               "--owner-provenance", "owner-original"], capture_output=True, timeout=15)
            self.assertEqual(capture.returncode, 0, capture.stderr)
            self.assertEqual(json.loads(capture.stdout)["source_ref"], original)
            check = subprocess.run(command + ["sequence", str(packet_path), "--root", str(root),
                                             "--original-source-ref", str(original_path), "--owner-provenance", "owner-original",
                                             "--require-criteria-fidelity"], capture_output=True, timeout=15)
            self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
