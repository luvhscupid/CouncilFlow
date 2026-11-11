"""Independent controls; generated sequences are artificial, never AI sessions."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts as c

PROGRAM = ROOT / ".agents/skills/council-flow/scripts/contracts.py"
IDS = ["S-AC1", "S-AC2"]


def artifact(name="S-candidate", digest="0" * 64):
    return {"artifact_id": name, "path": "synthetic/" + name + ".json", "sha256": digest, "kind": "synthetic"}


def packet(mid, kind, sender, recipient, payload, reply=None, attempt="S-A1"):
    return {"protocol": "council-flow", "version": "1.0", "message_id": mid,
            "message_type": kind, "plan_id": "S-P1", "plan_revision": 1,
            "task_id": "S-T1", "attempt_id": attempt,
            "sender": {"role": sender, "instance_id": "synthetic-" + sender},
            "recipient": {"role": recipient, "instance_id": "synthetic-" + recipient},
            "created_at": "2026-11-11T00:00:00Z", "in_reply_to": reply,
            "payload": payload, "evidence_refs": []}


def synthetic_sequence():
    data = [packet("S1", "plan.publish", "planner", "manager", {
        "objective": "Synthetic independent control", "scope": ["synthetic/**"],
        "acceptance_ids": IDS, "plan_ref": artifact("S-plan")})]
    for role, number, predecessor in [("worker", 2, "S1"), ("tester", 4, "S3"), ("reviewer", 6, "S5")]:
        assignment = {"objective": "Synthetic assigned check", "scope": ["synthetic/**"],
                      "acceptance_ids": IDS, "instructions": ["Preserve original criteria."]}
        if role != "worker":
            assignment["candidate_ref"] = artifact()
        if role == "tester":
            assignment["oracle_ref"] = artifact("S-oracle")
        data.append(packet("S" + str(number), "job.assign", "manager", role, assignment, predecessor))
        result = {"status": "passed", "summary": "Synthetic check, not a runtime session",
                  "acceptance_ids": IDS, "candidate_ref": artifact(), "findings": [], "errors": []}
        if role == "worker":
            result["changed_files"] = ["synthetic/program.py"]
        if role == "tester":
            result["oracle_ref"] = artifact("S-oracle")
            result["checks"] = [{"name": "Synthetic mandatory check", "status": "passed",
                                 "evidence_ref": artifact("S-test")}]
        if role == "reviewer":
            result["observations"] = {"observed": ["Synthetic observation fixture"], "inspected": [], "simulated": []}
        report = packet("S" + str(number + 1), "job.report", role, "manager", result, "S" + str(number))
        report["evidence_refs"] = [artifact("S-evidence-" + role)]
        data.append(report)
    data.append(packet("S8", "task.decision", "manager", "planner", {
        "disposition": "accept", "reason": "Synthetic independent reports", "acceptance_ids": IDS,
        "candidate_ref": artifact(), "report_ids": ["S3", "S5", "S7"]}, "S7"))
    return data


class IndependentContractChecks(unittest.TestCase):
    def test_actual_packets_and_mutated_role_task_origin(self):
        names = ["REST-M009", "REST-PLAN-LIVE-001", "REST-M010"]
        real = [c.read_json(ROOT / "reports/restoration/messages" / (name + ".json")) for name in names]
        bindings = {"REST-M009": {"role": "manager", "instance_id": "/root"},
                    "REST-PLAN-LIVE-001": {"role": "planner", "instance_id": "/root/restoration_planner"},
                    "REST-M010": {"role": "manager", "instance_id": "/root"}}
        c.validate_sequence(real, root=ROOT, expected_senders=bindings)
        for field, value in [("plan_revision", True), ("task_id", "OTHER"), ("plan_id", "OTHER"),
                             ("attempt_id", "OTHER"), ("in_reply_to", "UNKNOWN")]:
            altered = copy.deepcopy(real); altered[-1][field] = value
            with self.subTest(field=field), self.assertRaises(c.ContractError):
                c.validate_sequence(altered, root=ROOT, expected_senders=bindings)
        forged = copy.deepcopy(real[-1]); forged["sender"] = {"role": "manager", "instance_id": "/root"}
        with self.assertRaises(c.ContractError):
            c.validate_message(forged, expected_sender={"role": "worker", "instance_id": "synthetic-worker"})

    def test_strict_json_mutations_and_bounds(self):
        for value in [b'\xff', '{', '{"x":0,"x":1}', '{"nested":{"a":1,"a":2}}',
                      '{"n":NaN}', '{"n":Infinity}', '{"n":-Infinity}', '{"n":1e9999}',
                      '"\\udfff"', '[' * 17 + '0' + ']' * 17,
                      json.dumps(list(range(129))), ' ' * 65537]:
            with self.subTest(value=str(value)[:40]), self.assertRaises(c.ContractError):
                c.loads(value)
        for field, value in [("version", True), ("version", 1.0), ("version", "0.2.1"),
                             ("protocol", "ACP"), ("message_id", ""), ("plan_revision", False),
                             ("created_at", "2026-02-30T00:00:00Z")]:
            m = copy.deepcopy(synthetic_sequence()[0]); m[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(c.ContractError):
                c.validate_message(m)
        for position in ["envelope", "actor", "payload"]:
            m = copy.deepcopy(synthetic_sequence()[0])
            target = m if position == "envelope" else m["sender" if position == "actor" else "payload"]
            target["unapproved_field"] = "x"
            with self.subTest(position=position), self.assertRaises(c.ContractError): c.validate_message(m)

    def test_independence_oracle_candidate_and_acceptance_negatives(self):
        c.validate_sequence(synthetic_sequence())
        for mutation in ["worker_only", "self_oracle", "different_candidate", "omit_acceptance", "failed_check"]:
            seq = synthetic_sequence()
            if mutation == "worker_only": seq[-1]["payload"]["report_ids"] = ["S3"]
            if mutation == "self_oracle": seq[4]["payload"]["oracle_ref"] = artifact("S-self-oracle")
            if mutation == "different_candidate": seq[4]["payload"]["candidate_ref"] = artifact("S-other")
            if mutation == "omit_acceptance": seq[-1]["payload"]["acceptance_ids"] = IDS[:1]
            if mutation == "failed_check": seq[4]["payload"]["checks"][0]["status"] = "failed"
            with self.subTest(mutation=mutation), self.assertRaises(c.ContractError): c.validate_sequence(seq)
        for role in ["worker", "tester", "reviewer", "supervisor", "owner"]:
            m = copy.deepcopy(synthetic_sequence()[-1]); m["sender"]["role"] = role
            with self.subTest(role=role), self.assertRaises(c.ContractError): c.validate_message(m)
        seq = synthetic_sequence(); seq[1]["payload"]["candidate_ref"] = artifact("S-input")
        seq[2]["payload"]["input_candidate_ref"] = artifact("S-input")
        c.validate_sequence(seq)  # Worker output differs; verifier output does not.
        seq = synthetic_sequence(); seq[4]["payload"]["checks"][0]["evidence_ref"] = artifact("S-candidate", "1" * 64)
        with self.assertRaises(c.ContractError): c.validate_sequence(seq)

    def test_nonobject_sequence_items_are_controlled_errors(self):
        for value in [[], 1, False, None, "message"]:
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([value])

    def test_wrong_bindings_types_are_controlled_errors(self):
        seed = c.read_json(ROOT / "reports/restoration/messages/REST-M009.json")
        for value in [[], [1], True, 1, "bindings"]:
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([seed], expected_senders=value)

    def test_cli_bad_context_never_accepted_or_traceback(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix="fixtures-") as tmp:
            folder = Path(tmp); malformed = folder / "nonobject.json"; malformed.write_text("[]")
            bindings = folder / "bindings.json"; bindings.write_text("[]")
            commands = [[str(PROGRAM), "sequence", str(malformed)],
                        [str(PROGRAM), "sequence", str(ROOT / "reports/restoration/messages/REST-M009.json"), "--bindings", str(bindings)]]
            for arguments in commands:
                with self.subTest(arguments=arguments):
                    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, text=True, capture_output=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("Traceback", result.stderr)
                    payload = json.loads(result.stderr)
                    self.assertIs(payload["valid"], False)

    def test_restricted_yaml_and_jsonl_controls(self):
        path = ROOT / ".agents/skills/council-flow/policies/roles.yaml"
        source = path.read_bytes(); policy = c.parse_policy(source); c.validate_policy(policy)
        for value in [b'\xff', '\ud800', 'a: true\na: false\n', 'a: &anchor true\n',
                      'a: *alias\n', 'a: !!str 1\n', 'a: 1.2\n', 'a: |\n  contents\n']:
            with self.subTest(value=str(value)[:25]), self.assertRaises(c.ContractError): c.parse_policy(value)
        for section, key, value in [("resources", "infrastructure_retries", True),
                                    ("security", "grants_os_permissions", True),
                                    ("authority", "ordinary_repair_owner_approval", True)]:
            data = copy.deepcopy(policy); data[section][key] = value
            with self.subTest(section=section), self.assertRaises(c.ContractError): c.validate_policy(data)
        data = copy.deepcopy(policy); data["roles"]["manager"]["application_code"] = True
        with self.assertRaises(c.ContractError): c.validate_policy(data)
        event = {"protocol": "council-flow", "version": "1.0", "event_id": "S-E1",
                 "event_type": "plan_published", "created_at": "2026-11-11T00:00:00Z",
                 "message_id": "S1", "plan_id": "S-P1", "task_id": "S-T1", "attempt_id": "S-A1", "evidence_refs": []}
        c.validate_jsonl(json.dumps(event), messages=synthetic_sequence())
        for change in ["duplicate", "unknown", "reference", "nonobject"]:
            value = copy.deepcopy(event)
            if change == "duplicate": raw = json.dumps(value) + "\n" + json.dumps(value)
            elif change == "unknown": value["credential"] = "not permitted"; raw = json.dumps(value)
            elif change == "reference": value["message_id"] = "UNKNOWN"; raw = json.dumps(value)
            else: raw = "[]"
            with self.subTest(change=change), self.assertRaises(c.ContractError):
                c.validate_jsonl(raw, messages=synthetic_sequence())
        for bad in [b'\xff', '\ud800']:
            with self.assertRaises(c.ContractError): c.validate_jsonl(bad)

    def test_artifact_contents_and_authorized_root_boundaries(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix="artifacts-") as tmp:
            area = Path(tmp); allowed = area / "allowed"; allowed.mkdir()
            inside = allowed / "evidence.txt"; inside.write_text("real local evidence")
            ref = {"artifact_id": "S-real-file", "path": "evidence.txt", "sha256": hashlib.sha256(inside.read_bytes()).hexdigest(), "kind": "synthetic"}
            c.artifact(ref, root=allowed)
            bad = dict(ref, sha256="0" * 64)
            with self.assertRaises(c.ContractError): c.artifact(bad, root=allowed)
            bad = dict(ref, path="../outside.txt")
            with self.assertRaises(c.ContractError): c.artifact(bad, root=allowed)
            outside = area / "outside.txt"; outside.write_text("outside the supplied subroot, still inside the repository")
            (allowed / "link").symlink_to(outside)
            bad = dict(ref, path="link", sha256=hashlib.sha256(outside.read_bytes()).hexdigest())
            with self.assertRaises(c.ContractError): c.artifact(bad, root=allowed)


if __name__ == "__main__":
    unittest.main()
