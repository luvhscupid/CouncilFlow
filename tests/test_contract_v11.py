"""Contract version 1.1: new types, pins, exact question check, no downgrade; 1.0 unchanged."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fx

c = fx.c
ref = fx.ref
SCRIPT = fx.SKILL / "scripts/contracts.py"


def v11(m, **pin):
    m = copy.deepcopy(m)
    m["version"] = "1.1"
    if m["message_type"] in ("job.assign", "job.report"):
        m["payload"].update({"ledger_version": 1, "slice_id": "S1"})
        m["payload"].update(pin)
    return m


def run11():
    """The standard run, every packet on 1.1 with the same pin."""
    return [v11(m) for m in fx.sequence()]


def reopen(mid, sender, recipient, reply=None, **payload):
    body = {"evidence_id": "E0001", "ledger_ids": ["R1"], "affected_slices": ["S1"],
            "contradiction": "Observed behaviour contradicts R1.", "consequence": "Slice S1 may be wrong.",
            "evidence_ref": ref("E0001", "synthetic/E0001.json")}
    body.update(payload)
    m = fx.message(mid, "evidence.reopen", sender, recipient, body, reply)
    m["version"] = "1.1"
    return m


def ledger(mid, version, reply="M1", reopen_ids=(), changed=("R1",)):
    m = fx.message(mid, "ledger.publish", "planner", "manager",
                   {"ledger_version": version, "ledger_ref": ref("L%04d" % version, "synthetic/L%04d.json" % version),
                    "changed_entry_ids": list(changed), "reason": "Synthetic ledger change",
                    "reopen_ids": list(reopen_ids)}, reply)
    m["version"] = "1.1"
    return m


def code(test, call, *args, **kwargs):
    with test.assertRaises(c.ContractError) as failure:
        call(*args, **kwargs)
    return failure.exception.code


QUESTION = {"question_id": "Q1", "text": "Which database should we use?", "blocking": True,
            "decision_class": "owner_objective", "affected_slices": ["S1"],
            "permitted_default": None, "reason": "The choice changes the objective."}


class VersionOneCompatibility(unittest.TestCase):
    def test_known_valid_1_0_run_still_validates(self):
        c.validate_sequence(fx.sequence())

    def test_1_0_packets_reject_1_1_only_fields_and_types(self):
        assign = fx.sequence()[1]
        assign["payload"].update({"ledger_version": 1, "slice_id": "S1"})
        self.assertEqual(code(self, c.validate_message, assign), "unknown_field")
        for m in (reopen("R1", "worker", "manager"), ledger("L1", 1)):
            m["version"] = "1.0"
            self.assertEqual(code(self, c.validate_message, m), "message_type")

    def test_unsupported_version_is_refused(self):
        m = fx.publish()
        m["version"] = "1.2"
        self.assertEqual(code(self, c.validate_message, m), "version")


class PinTests(unittest.TestCase):
    def test_full_1_1_run_validates(self):
        c.validate_sequence(run11())

    def test_1_1_assign_without_ledger_version_fails(self):
        data = run11()
        del data[1]["payload"]["ledger_version"]
        self.assertEqual(code(self, c.validate_message, data[1]), "required")

    def test_1_1_report_without_slice_fails(self):
        data = run11()
        del data[2]["payload"]["slice_id"]
        self.assertEqual(code(self, c.validate_message, data[2]), "required")

    def test_report_pin_mismatch_fails_ledger_pin(self):
        for field, value in (("ledger_version", 2), ("slice_id", "S2")):
            data = run11()
            data[2]["payload"][field] = value
            with self.subTest(field=field):
                self.assertEqual(code(self, c.validate_sequence, data), "ledger_pin")


class ReopenTests(unittest.TestCase):
    def base(self):
        return [dict(fx.publish(), version="1.1")]

    def test_reopen_worker_to_manager_then_forward_passes(self):
        first = reopen("R1", "worker", "manager", "M1")
        forward = reopen("R2", "manager", "planner", "R1")
        c.validate_sequence(self.base() + [first, forward])

    def test_altered_forward_fails(self):
        first = reopen("R1", "worker", "manager", "M1")
        forward = reopen("R2", "manager", "planner", "R1", consequence="Different.")
        self.assertEqual(code(self, c.validate_sequence, self.base() + [first, forward]), "reopen_forward")

    def test_forward_must_answer_a_reopen(self):
        forward = reopen("R2", "manager", "planner", "M1")
        self.assertEqual(code(self, c.validate_sequence, self.base() + [forward]), "reopen_forward")

    def test_bad_routes_and_payloads(self):
        self.assertEqual(code(self, c.validate_message, reopen("R1", "planner", "manager")), "route")
        self.assertEqual(code(self, c.validate_message, reopen("R1", "worker", "planner")), "route")
        self.assertEqual(code(self, c.validate_message, reopen("R1", "manager", "manager")), "route")
        empty = reopen("R1", "worker", "manager")
        empty["evidence_refs"] = []
        self.assertEqual(code(self, c.validate_message, empty), "evidence")
        self.assertEqual(code(self, c.validate_message, reopen("R1", "worker", "manager", ledger_ids=[])), "array")
        self.assertEqual(code(self, c.validate_message, reopen("R1", "worker", "manager", affected_slices=["S1", "S1"])), "duplicate_item")
        extra = reopen("R1", "worker", "manager")
        extra["payload"]["x"] = 1
        self.assertEqual(code(self, c.validate_message, extra), "unknown_field")

    def test_reopen_needs_a_published_plan(self):
        self.assertEqual(code(self, c.validate_sequence, [reopen("R1", "worker", "manager")]), "plan_context")


class LedgerTests(unittest.TestCase):
    def base(self):
        return [dict(fx.publish(), version="1.1")]

    def test_valid_publish_answering_a_reopen(self):
        c.validate_sequence(self.base() + [reopen("R1", "worker", "manager", "M1"),
                                           ledger("L2", 2, "R1", ["R1"])])

    def test_unknown_reopen_id_fails(self):
        self.assertEqual(code(self, c.validate_sequence, self.base() + [ledger("L2", 2, "M1", ["nope"])]), "reopen_reference")

    def test_reopen_id_must_be_a_reopen(self):
        self.assertEqual(code(self, c.validate_sequence, self.base() + [ledger("L2", 2, "M1", ["M1"])]), "reopen_reference")

    def test_decreasing_or_equal_version_fails(self):
        for second in (2, 1):
            data = self.base() + [ledger("L1", 2), ledger("L2", second, "L1")]
            with self.subTest(second=second):
                self.assertEqual(code(self, c.validate_sequence, data), "ledger_version_order")

    def test_empty_changes_only_for_version_one(self):
        c.validate_message(ledger("L1", 1, changed=()))
        self.assertEqual(code(self, c.validate_message, ledger("L2", 2, changed=())), "required")

    def test_publish_goes_planner_to_manager_only(self):
        m = ledger("L1", 1)
        m["sender"], m["recipient"] = {"role": "manager", "instance_id": "m"}, {"role": "planner", "instance_id": "p"}
        self.assertEqual(code(self, c.validate_message, m), "route")


class QuestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        answer = {"schema": "councilflow-readiness", "version": "1.0", "status": "BLOCKED", "slice_id": "S1",
                  "ledger_version": None, "discovery_cycle": 1, "assumption_ids": [],
                  "questions": [QUESTION], "reason": "Blocked on the database choice."}
        data = json.dumps(answer).encode()
        (self.root / "answer.json").write_bytes(data)
        self.ref = ref("readiness", "answer.json", hashlib.sha256(data).hexdigest())

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, question):
        m = fx.message("Q", "approval.request", "manager", "owner",
                       {"question": "Which database?", "reason": "Needed.", "options": ["A", "B"],
                        "operation_ref": self.ref, "questions": [question]})
        m["version"] = "1.1"
        m["evidence_refs"] = []
        return m

    def test_matching_questions_pass(self):
        c.validate_message(self.request(copy.deepcopy(QUESTION)), root=self.root)
        c.validate_message(self.request(copy.deepcopy(QUESTION)))

    def test_one_changed_character_fails_question_text(self):
        changed = dict(QUESTION, text="Which database should we use ?")
        self.assertEqual(code(self, c.validate_message, self.request(changed), root=self.root), "question_text")
        c.validate_message(self.request(changed))  # without root there is nothing to compare

    def test_question_rules_are_the_readiness_rules(self):
        bad = dict(QUESTION, decision_class="cheap_reversible_x")
        self.assertEqual(code(self, c.validate_message, self.request(bad)), "decision_class")
        bad = dict(QUESTION, permitted_default="Use SQLite")
        self.assertEqual(code(self, c.validate_message, self.request(bad)), "class_downgrade")
        bad = {k: v for k, v in QUESTION.items() if k != "reason"}
        self.assertEqual(code(self, c.validate_message, self.request(bad)), "fields")

    def test_questions_not_allowed_on_1_0(self):
        m = self.request(copy.deepcopy(QUESTION))
        m["version"] = "1.0"
        self.assertEqual(code(self, c.validate_message, m), "unknown_field")


class DecisionTests(unittest.TestCase):
    def decision(self, **extra):
        m = fx.message("D", "approval.decision", "owner", "manager",
                       {"decision": "approved", "approval_request_id": "Q",
                        "provenance_ref": ref("owner-note", "synthetic/owner.txt"), **extra}, "Q")
        m["version"] = "1.1"
        return m

    def test_missing_owner_source_ref_fails(self):
        self.assertEqual(code(self, c.validate_message, self.decision()), "required")

    def test_source_ref_and_interpretation_pass(self):
        c.validate_message(self.decision(owner_source_ref=ref("S0001", "synthetic/S0001.txt"),
                                         interpretation="Owner approved option A."))

    def test_1_0_decision_is_unchanged(self):
        m = self.decision()
        m["version"] = "1.0"
        c.validate_message(m)


class DowngradeAndSaveTests(unittest.TestCase):
    def test_1_1_then_1_0_fails(self):
        data = [dict(fx.publish(), version="1.1"), fx.sequence()[1]]
        self.assertEqual(code(self, c.validate_sequence, data), "version_downgrade")

    def test_1_0_then_1_1_passes(self):
        data = fx.sequence()[:2] + [reopen("R1", "worker", "manager", "M2")]
        c.validate_sequence(data)

    def test_save_accepts_a_1_1_reopen_in_library_and_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / ".councilflow/runs/T1"
            run.mkdir(parents=True)
            c.save_message(json.dumps(dict(fx.publish(), version="1.1")).encode(), run)
            packet = json.dumps(reopen("R1", "worker", "manager", "M1"))
            path = Path(directory) / "R1.json"
            path.write_text(packet)
            done = subprocess.run([sys.executable, str(SCRIPT), "save", str(path), "--run", str(run),
                                   "--expected-sender", "worker", "--expected-instance", "worker-1"],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue((run / "messages/R1.json").is_file())
            saved = [c.read_json(p) for p in (run / "messages").glob("*.json")]
            c.validate_sequence(c._run_order(saved))


class SpecTests(unittest.TestCase):
    def test_contract_json_lists_versions_types_and_pins(self):
        spec = json.loads((fx.SKILL / "references/message-contract.json").read_text())
        self.assertEqual(spec["supported_versions"], list(c.VERSIONS))
        self.assertEqual(set(spec["routes"]), set(c.ROUTES))
        self.assertEqual(set(spec["version_1_1_only_types"]), c.V11_TYPES)
        self.assertEqual(set(spec["payload_required"]["evidence.reopen"]),
                         {"evidence_id", "ledger_ids", "affected_slices", "contradiction", "consequence", "evidence_ref"})
        self.assertEqual(set(spec["version_1_1_payload_required"]["job.report"]), {"ledger_version", "slice_id"})


if __name__ == "__main__":
    unittest.main()
