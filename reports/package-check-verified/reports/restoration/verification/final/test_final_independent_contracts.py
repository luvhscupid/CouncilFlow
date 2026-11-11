"""Independent controlled-record checks; mutations are not native message history."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts as c


def actual_round():
    # Freeze the actual assigned prefix so later legitimate Manager progress does
    # not change this independently verified input or supply a different tail.
    names = c.read_json(HERE / "live-input-order.json")
    return [c.read_json(ROOT / name) for name in names]


def synthetic_positive():
    # Independently authored earlier Tester fixture, explicitly not live sessions.
    path = ROOT / "reports/restoration/verification/initial/test_independent_contracts.py"
    spec = importlib.util.spec_from_file_location("independent_t1_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.synthetic_sequence()


class FinalIndependentChecks(unittest.TestCase):
    def test_actual_round_and_causal_candidate_authority_acceptance_mutations(self):
        messages = actual_round()
        bindings = c.read_json(ROOT / "reports/restoration/live-bindings.json")
        c.validate_sequence(messages, root=ROOT, expected_senders=bindings)
        for mutation in ("causal", "candidate", "authority", "acceptance", "origin"):
            altered = copy.deepcopy(messages)
            if mutation == "causal":
                altered[-1]["in_reply_to"] = "NO-SUCH-ACTUAL-MESSAGE"
            elif mutation == "candidate":
                earlier_report = next(x for x in altered if x["message_id"] == "REST-T1-REPORT-001")
                earlier_report["payload"]["candidate_ref"] = altered[-1]["payload"]["candidate_ref"]
            elif mutation == "authority":
                altered[-1]["sender"]["role"] = "worker"
            elif mutation == "acceptance":
                earlier_report = next(x for x in altered if x["message_id"] == "REST-T1-REPORT-001")
                earlier_report["payload"]["acceptance_ids"] = earlier_report["payload"]["acceptance_ids"][:-1]
            else:
                bindings = copy.deepcopy(bindings)
                bindings[altered[-1]["message_id"]] = {"role": "worker", "instance_id": "synthetic-forged-origin"}
            with self.subTest(mutation=mutation), self.assertRaises(c.ContractError):
                c.validate_sequence(altered, root=ROOT, expected_senders=bindings)

    def test_repaired_message_identity_and_falsey_context_types(self):
        seed = actual_round()[0]
        for value in ([], {}, False, None, 1):
            altered = copy.deepcopy(seed)
            altered["message_id"] = value
            with self.subTest(identity=value), self.assertRaises(c.ContractError):
                c.validate_sequence([altered])
        for value in ([], (), False, 0, "", [1]):
            with self.subTest(bindings=value), self.assertRaises(c.ContractError):
                c.validate_sequence([seed], expected_senders=value)
        for value in (None, {}, False, "owner"):
            with self.subTest(owner_context=value), self.assertRaises(c.ContractError):
                c.validate_sequence([seed], owner_provenance=value)

    def test_every_recognized_changed_files_field_has_correct_type(self):
        base = c.read_json(ROOT / "reports/restoration/messages/REST-T1-REPORT-001.json")
        for role in ("tester", "reviewer"):
            for bad in (42, False, {"path": "not-a-list"}):
                altered = copy.deepcopy(base)
                if role == "reviewer":
                    altered["sender"] = {"role": "reviewer", "instance_id": "synthetic-reviewer"}
                    altered["payload"].pop("oracle_ref", None)
                    altered["payload"].pop("checks", None)
                    altered["payload"]["observations"] = {
                        "observed": ["Artificial mutation, not a native Reviewer observation"],
                        "inspected": [], "simulated": []}
                altered["payload"]["changed_files"] = bad
                with self.subTest(role=role, value=bad), self.assertRaises(c.ContractError):
                    c.validate_message(altered, root=ROOT)

    def test_accept_decision_cannot_declare_current_failed_criteria(self):
        c.validate_sequence(synthetic_positive())
        for ids in (["S-AC1"], ["UNKNOWN"]):
            altered = synthetic_positive()
            altered[-1]["payload"]["failed_acceptance_ids"] = ids
            with self.subTest(failed_ids=ids), self.assertRaises(c.ContractError):
                c.validate_sequence(altered)

    def test_actual_diagnostic_export_and_reference_sensitivity(self):
        messages = actual_round()
        messages.append(c.read_json(ROOT / "reports/restoration/activation/REST-ACT-REPORT-001.json"))
        raw = (ROOT / "reports/restoration/events-prefix-001.jsonl").read_bytes()
        self.assertEqual(c.validate_jsonl(raw, messages=messages, root=ROOT), 6)
        events = [c.loads(line) for line in raw.splitlines()]
        for mutation in ("message", "task", "unknown_field", "duplicate"):
            changed = copy.deepcopy(events)
            if mutation == "message":
                changed[0]["message_id"] = "NOT-ACTUAL"
            elif mutation == "task":
                changed[0]["task_id"] = "NOT-THIS-TASK"
            elif mutation == "unknown_field":
                changed[0]["raw_credentials"] = "synthetic-forbidden-field"
            else:
                changed.append(copy.deepcopy(changed[0]))
            encoded = "\n".join(json.dumps(x) for x in changed)
            with self.subTest(mutation=mutation), self.assertRaises(c.ContractError):
                c.validate_jsonl(encoded, messages=messages, root=ROOT)

    def test_referenced_plan_context_has_typed_identity_and_acceptance(self):
        import hashlib
        original = c.read_json(ROOT / "reports/restoration/plan.json")
        values = [[], True, None, 1]
        changed = copy.deepcopy(original)
        changed["plan_revision"] = True
        values.append(changed)
        for entry in ("not-an-entry", None):
            changed = copy.deepcopy(original)
            changed["acceptance"] = [entry]
            values.append(changed)
        with tempfile.TemporaryDirectory(dir=HERE, prefix="plans-") as tmp:
            for index, value in enumerate(values):
                path = Path(tmp) / (str(index) + ".json")
                path.write_text(json.dumps(value))
                packet = c.read_json(ROOT / "reports/restoration/messages/REST-PLAN-LIVE-001.json")
                packet["in_reply_to"] = None
                packet["payload"]["plan_ref"] = {
                    "artifact_id": "SYNTHETIC-PLAN-" + str(index),
                    "path": str(path.relative_to(ROOT)),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "kind": "synthetic-context-mutation"}
                with self.subTest(value_index=index), self.assertRaises(c.ContractError):
                    c.validate_sequence([packet], root=ROOT)

    def test_passed_final_map_requires_explicit_per_criterion_evidence(self):
        sequence = synthetic_positive()
        check = {
            "protocol": "council-flow", "version": "1.0", "message_id": "S9",
            "message_type": "plan.check", "plan_id": "S-P1", "plan_revision": 1,
            "task_id": "S-T1", "attempt_id": "S-A1",
            "sender": {"role": "planner", "instance_id": "synthetic-planner"},
            "recipient": {"role": "manager", "instance_id": "synthetic-manager"},
            "created_at": "2026-11-11T00:00:00Z", "in_reply_to": "S8",
            "payload": {"status": "passed", "summary": "Artificial missing-citation control",
                        "acceptance_ids": ["S-AC1", "S-AC2"],
                        "plan_ref": sequence[0]["payload"]["plan_ref"],
                        "results": [{"acceptance_id": item, "status": "passed", "evidence_refs": []}
                                    for item in ["S-AC1", "S-AC2"]]},
            "evidence_refs": []}
        with self.assertRaises(c.ContractError):
            c.validate_sequence(sequence + [check])


if __name__ == "__main__":
    unittest.main()
