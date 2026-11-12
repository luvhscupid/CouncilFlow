"""Synthetic deterministic controls, not real agents, approvals or activation proof."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/council-flow"
sys.path.insert(0, str(SKILL / "scripts"))
import contracts as c

AC = ["AC1", "AC2"]
STAMP = "2026-11-11T00:00:00Z"  # Synthetic fixture time, never runtime evidence.


def ref(identity="candidate", path="synthetic/candidate.json", content_hash="0" * 64, kind="synthetic"):
    return {"artifact_id": identity, "path": path, "sha256": content_hash, "kind": kind}


def message(mid, kind, role, recipient, payload, reply=None, attempt="A1", instance=None):
    return {"protocol": "council-flow", "version": "1.0", "message_id": mid,
            "message_type": kind, "plan_id": "P1", "plan_revision": 1, "task_id": "T1",
            "attempt_id": attempt, "sender": {"role": role, "instance_id": instance or role + "-1"},
            "recipient": {"role": recipient, "instance_id": recipient + "-1"},
            "in_reply_to": reply, "payload": payload,
            "evidence_refs": [ref()]}


def publish():
    return message("M1", "plan.publish", "planner", "manager",
                   {"objective": "Synthetic contract test", "scope": ["demo/**"],
                    "acceptance_ids": AC, "plan_ref": ref("plan", "synthetic/plan.json")})


def assignment(mid, role, reply, candidate=None, attempt="A1", instance=None):
    p = {"objective": "Synthetic bounded task", "scope": ["demo/**"],
         "acceptance_ids": AC, "instructions": ["Use original acceptance."]}
    if candidate is not None:
        p["candidate_ref"] = candidate
    if role == "tester":
        p["oracle_ref"] = ref("approved-strategy", "synthetic/strategy.json")
    m = message(mid, "job.assign", "manager", role, p, reply, attempt)
    if instance:
        m["recipient"]["instance_id"] = instance
    return m


def report(mid, role, reply, candidate=None, status="passed", attempt="A1", instance=None,
           input_ref=None, tester_message_id="M5"):
    p = {"status": status, "summary": "Synthetic observation, not live proof",
         "acceptance_ids": AC, "candidate_ref": candidate or ref(), "findings": [], "errors": []}
    if role == "worker":
        p["changed_files"] = ["demo/program.py"]
        if input_ref is not None:
            p["input_candidate_ref"] = input_ref
    if role == "tester":
        p["oracle_ref"] = ref("approved-strategy", "synthetic/strategy.json")
        p["checks"] = [{"name": "Synthetic behavioral check", "status": status,
                        "evidence_ref": ref("test-output", "synthetic/test.txt")}]
        p["deterministic_commands"] = [{"command_id": "CMD1", "command": "python",
            "arguments": ["-m", "unittest"], "workdir": ".", "candidate_ref": p["candidate_ref"],
            "input_refs": [], "exit_code": 0, "stdout_sha256": "a" * 64,
            "acceptance_id": AC[0], "evidence_ref": ref("tester-execution", "synthetic/tester-run.txt")}]
        p["checks"][0]["status"] = "passed"
        m = message(mid, "job.report", role, "manager", p, reply, attempt, instance)
        m["evidence_refs"].append(ref("tester-report", "synthetic/tester-report.json"))
        m["evidence_refs"].append(ref("tester-execution", "synthetic/tester-run.txt"))
        return m
    if role == "reviewer":
        p["comparison"] = {"plan_ref": ref("plan", "synthetic/plan.json"),
            "tester_report_ref": ref(tester_message_id, "synthetic/tester-report.json", kind="message"),
            "candidate_ref": p["candidate_ref"], "findings": ["Compared original criteria, candidate and Tester evidence."],
            "discrepancies": [], "independent_rerun": {"status": "MATCH", "command_id": "CMD1",
                "command": "python", "arguments": ["-m", "unittest"], "workdir": ".",
                "candidate_ref": p["candidate_ref"], "input_refs": [], "exit_code": 0,
                "stdout_sha256": "a" * 64, "acceptance_id": AC[0],
                "evidence_ref": ref("reviewer-execution", "synthetic/reviewer-run.txt"),
                "tester_evidence_ref": ref("tester-execution", "synthetic/tester-run.txt"),
                "tester_exit_code": 0, "tester_stdout_sha256": "a" * 64}}
        m = message(mid, "job.report", role, "manager", p, reply, attempt, instance)
        m["evidence_refs"].append(ref("reviewer-execution", "synthetic/reviewer-run.txt"))
        return m
    return message(mid, "job.report", role, "manager", p, reply, attempt, instance)


def sequence():
    return [
        publish(),
        assignment("M2", "worker", "M1"),
        report("M3", "worker", "M2"),
        assignment("M4", "tester", "M3", ref()),
        report("M5", "tester", "M4"),
        assignment("M6", "reviewer", "M5", ref()),
        report("M7", "reviewer", "M6"),
        message("M8", "task.decision", "manager", "planner",
                {"disposition": "accept", "reason": "Independent synthetic evidence",
                 "acceptance_ids": AC, "candidate_ref": ref(), "report_ids": ["M3", "M5", "M7"]}, "M7"),
        message("M9", "plan.check", "planner", "manager",
                {"status": "passed", "summary": "Synthetic original acceptance map",
                 "acceptance_ids": AC, "plan_ref": ref("plan", "synthetic/plan.json"),
                 "results": [{"acceptance_id": a, "status": "passed", "evidence_refs": [ref()]} for a in AC]}, "M8")
    ]


class JSONContractTests(unittest.TestCase):
    def rejects(self, value):
        with self.assertRaises(c.ContractError):
            c.validate_message(value)

    def test_valid_all_five_ai_roles_and_full_ordered_sequence(self):
        data = sequence()
        for m in data:
            c.validate_message(c.loads(json.dumps(m)))
        self.assertEqual({m["sender"]["role"] for m in data},
                         {"planner", "manager", "worker", "tester", "reviewer"})
        c.validate_sequence(data)

    def test_all_purposes_and_synthetic_owner_provenance(self):
        data = [publish(), message("AR", "approval.request", "manager", "owner",
                {"question": "Synthetic scope choice?", "reason": "Fixture only",
                 "options": ["approve", "reject"], "operation_ref": ref("operation", "synthetic/operation.json")}, "M1")]
        decision = message("AD", "approval.decision", "owner", "manager",
                {"decision": "approved", "approval_request_id": "AR",
                 "provenance_ref": ref("owner-input", "synthetic/owner.txt")}, "AR")
        c.validate_message(decision)  # Structure only, not an actual Owner approval.
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data + [decision])
        c.validate_sequence(data + [decision], owner_provenance={"owner-input"})
        progress = message("PR", "plan.progress", "manager", "planner",
                {"status": "planning", "objective": "Fixture", "scope": ["demo/**"],
                 "acceptance_ids": AC, "verified_progress": ["Observed fixture"], "next_action": "Publish plan"})
        c.validate_message(progress)
        self.assertEqual(set(c.ROUTES), {m["message_type"] for m in sequence() + data + [decision, progress]})

    def test_malformed_duplicate_nonfinite_overflow_and_utf8(self):
        for raw in ['{', '{"x":1,"x":2}', '{"a":{"x":1,"x":2}}',
                    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e9999}',
                    '"\\ud800"', b"\xff"]:
            with self.subTest(raw=str(raw)), self.assertRaises(c.ContractError):
                c.loads(raw)

    def test_types_versions_unknown_fields_and_identifiers(self):
        variants = [("protocol", "acp"), ("version", "0.2.1"), ("version", 1.0),
                    ("version", True), ("plan_revision", True), ("plan_revision", 0),
                    ("plan_revision", "1"), ("task_id", False), ("attempt_id", ""),
                    ("message_id", "x" * 129), ("created_at", "2026-11-11T00:00:00Z"),
                    ("in_reply_to", "M1")]
        for key, value in variants:
            m = publish();m[key] = value
            with self.subTest(key=key, value=value):
                self.rejects(m)
        m = publish();m["unexpected"] = 1;self.rejects(m)
        m = publish();m["sender"]["authority"] = "owner";self.rejects(m)
        m = publish();m["payload"]["secret"] = "not a supported field";self.rejects(m)

    def test_size_depth_array_and_surrogate_limits(self):
        with self.assertRaises(c.ContractError):
            c.loads(b" " * (c.MAX_BYTES + 1))
        with self.assertRaises(c.ContractError):
            c.loads("[" * 17 + "0" + "]" * 17)
        with self.assertRaises(c.ContractError):
            c.loads(json.dumps(list(range(129))))
        m = publish();m["payload"]["objective"] = "x" * (c.MAX_STRING + 1);self.rejects(m)
        m = publish();m["payload"]["objective"] = "\ud800";self.rejects(m)
        m = publish();m[1] = "bad key";self.rejects(m)

    def test_invalid_roles_routes_and_self_approved_oracle(self):
        for role in ("worker", "tester", "reviewer"):
            m = copy.deepcopy(sequence()[7]);m["sender"]["role"] = role
            with self.subTest(role=role):
                self.rejects(m)
        m = publish();m["sender"]["role"] = "supervisor";self.rejects(m)
        m = report("M5", "tester", "M4");m["payload"]["oracle_approved"] = True;self.rejects(m)
        m = report("M7", "reviewer", "M6");m["message_type"] = "approval.decision";self.rejects(m)

    def test_expected_origin_rejects_a_spoofed_manager_label(self):
        m = copy.deepcopy(sequence()[7])
        with self.assertRaises(c.ContractError):
            c.validate_message(m, expected_sender={"role": "worker", "instance_id": "worker-1"})
        data = sequence()
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data, expected_senders={"M8": {"role": "worker", "instance_id": "worker-1"}})

    def test_context_unknown_duplicate_and_changed_causal_identity(self):
        for field, value in [("in_reply_to", "UNKNOWN"), ("task_id", "T2"),
                             ("plan_id", "P2"), ("plan_revision", 2), ("attempt_id", "A2")]:
            data = sequence();data[4][field] = value
            with self.subTest(field=field), self.assertRaises(c.ContractError):
                c.validate_sequence(data)
        data = sequence();data[4]["message_id"] = "M3"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)

    def test_sequence_nonobjects_and_bad_identity_are_controlled_errors(self):
        for value in ([], 1, False, None, "message"):
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([value])
        for value in ([], {}, False, None):
            m = publish();m["message_id"] = value
            with self.subTest(message_id=value), self.assertRaises(c.ContractError):
                c.validate_sequence([m])

    def test_supplied_sender_bindings_are_strict_even_when_falsey(self):
        for value in ([], [1], True, False, 0, 1, "", "bindings"):
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([publish()], expected_senders=value)
        malformed = [
            {False: {"role": "planner", "instance_id": "planner-1"}},
            {" ": {"role": "planner", "instance_id": "planner-1"}},
            {"M1": None}, {"M1": []},
            {"M1": {"role": "supervisor", "instance_id": "planner-1"}},
            {"M1": {"role": "planner", "instance_id": False}},
            {"M1": {"role": "planner", "instance_id": "planner-1", "authority": "owner"}},
        ]
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([publish()], expected_senders=value)
        c.validate_sequence([publish()], expected_senders=None)
        c.validate_sequence([publish()], expected_senders={})
        c.validate_sequence([publish()], expected_senders={"M1": publish()["sender"]})

    def test_owner_provenance_context_types_are_controlled_errors(self):
        for value in (None, False, 0, "owner-input", {}, [False], [" "]):
            with self.subTest(value=value), self.assertRaises(c.ContractError):
                c.validate_sequence([publish()], owner_provenance=value)
        c.validate_sequence([publish()], owner_provenance={"synthetic-owner-input"})

    def test_cli_sequence_type_errors_are_json_without_traceback(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            folder = Path(directory)
            valid = folder / "publish.json";valid.write_text(json.dumps(publish()), encoding="utf-8")
            invalid = folder / "invalid.json";bindings = folder / "bindings.json"
            for value in ([], 1, False, None):
                invalid.write_text(json.dumps(value), encoding="utf-8")
                run = subprocess.run([sys.executable, str(SKILL / "scripts/contracts.py"),
                                      "sequence", str(invalid)], capture_output=True, text=True, cwd=ROOT)
                with self.subTest(message=value):
                    self.assertEqual(run.returncode, 1)
                    self.assertEqual(run.stdout, "")
                    self.assertIs(json.loads(run.stderr)["valid"], False)
                    self.assertNotIn("Traceback", run.stderr)
            for value in ([], [1], False, 0, "bindings"):
                bindings.write_text(json.dumps(value), encoding="utf-8")
                run = subprocess.run([sys.executable, str(SKILL / "scripts/contracts.py"),
                                      "sequence", str(valid), "--bindings", str(bindings)],
                                     capture_output=True, text=True, cwd=ROOT)
                with self.subTest(bindings=value):
                    self.assertEqual(run.returncode, 1)
                    self.assertEqual(run.stdout, "")
                    self.assertEqual(json.loads(run.stderr)["error"], "context_bindings")
                    self.assertNotIn("Traceback", run.stderr)

    def test_worker_can_create_and_change_candidate_but_verifier_cannot(self):
        data = sequence();input_ref = ref("input", "synthetic/input.json", "1" * 64)
        data[1]["payload"]["candidate_ref"] = input_ref
        data[2]["payload"]["input_candidate_ref"] = input_ref
        c.validate_sequence(data)
        data[2]["payload"]["input_candidate_ref"] = ref()
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)
        for index in (4, 6):
            data = sequence();data[index]["payload"]["candidate_ref"] = ref("other", "synthetic/other.json", "2" * 64)
            with self.subTest(role=data[index]["sender"]["role"]), self.assertRaises(c.ContractError):
                c.validate_sequence(data)
        self.rejects(assignment("T", "tester", "M1"))

    def test_reports_bound_to_assignment_actor_and_acceptance(self):
        data = sequence();data[4]["sender"]["instance_id"] = "different-tester"
        with self.assertRaises(c.ContractError):c.validate_sequence(data)
        data = sequence();data[4]["payload"]["acceptance_ids"] = ["AC1"]
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_optional_changed_files_is_typed_for_every_report_role(self):
        for role in ("worker", "tester", "reviewer"):
            for bad in (42, False, None, {"path": "not-a-list"}, "path", [False], [""]):
                m = report("TYPE", role, "ASSIGN")
                m["payload"]["changed_files"] = bad
                with self.subTest(role=role, changed_files=bad):
                    self.rejects(m)
            m = report("TYPE", role, "ASSIGN")
            m["payload"]["changed_files"] = ["reports/generated-evidence.json"]
            c.validate_message(m)

    def test_decisions_cannot_accept_failures_or_name_unassigned_failures(self):
        for failed in (["AC1"], ["UNKNOWN"]):
            data = sequence()
            data[7]["payload"]["failed_acceptance_ids"] = failed
            with self.subTest(accept_failed=failed), self.assertRaises(c.ContractError):
                c.validate_sequence(data)
        for disposition in ("reject", "rework", "escalate"):
            m = copy.deepcopy(sequence()[7])
            m["payload"].update(disposition=disposition, failed_acceptance_ids=["UNKNOWN"])
            with self.subTest(disposition=disposition):
                self.rejects(m)
        data = sequence()
        data[7]["payload"]["failed_acceptance_ids"] = []
        c.validate_sequence(data)

    def test_passed_planner_criteria_need_explicit_citations(self):
        for status in ("passed", "blocked"):
            m = copy.deepcopy(sequence()[-1])
            m["payload"]["status"] = status
            m["payload"]["results"][0]["evidence_refs"] = []
            with self.subTest(overall_status=status):
                self.rejects(m)
        m = copy.deepcopy(sequence()[-1])
        m["payload"]["status"] = "blocked"
        m["payload"]["results"][0].update(status="unverified", evidence_refs=[])
        c.validate_message(m)  # Missing proof is not represented as a pass.

    def test_referenced_plan_context_types_and_preserved_metadata(self):
        valid = {"plan_id": "P1", "plan_revision": 1,
                 "acceptance": [{"id": "AC1", "criterion": "First requirement"},
                                {"id": "AC2", "criterion": "Second requirement"}],
                 "project_metadata": {"provenance": "Synthetic external-plan wrapper"}}
        variants = [[], True, None, 1]
        for key, value in [("plan_id", True), ("plan_revision", True),
                           ("plan_revision", "1"), ("plan_revision", 0),
                           ("acceptance", []), ("acceptance", {}),
                           ("acceptance", [None]), ("acceptance", ["not-an-object"]),
                           ("acceptance", [{"id": False}]),
                           ("acceptance", [{"id": "AC1"}, {"id": "AC1"}]),
                           ("acceptance", [{"id": "AC1", "criterion": False}]),
                           ("acceptance", [{"id": "AC1", "criterion": " "}])]:
            value_plan = copy.deepcopy(valid)
            value_plan[key] = value
            variants.append(value_plan)
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "plan.json"
            def packet(value):
                path.write_text(json.dumps(value), encoding="utf-8")
                p = publish()
                p["payload"]["plan_ref"] = ref("actual-plan", path.relative_to(ROOT).as_posix(),
                                                  hashlib.sha256(path.read_bytes()).hexdigest())
                p["evidence_refs"] = [p["payload"]["plan_ref"]]
                return p
            c.validate_sequence([packet(valid)], root=ROOT)
            for index, value in enumerate(variants):
                with self.subTest(plan_variant=index), self.assertRaises(c.ContractError):
                    c.validate_sequence([packet(value)], root=ROOT)
            source = Path(directory) / "packet.json"
            source.write_text(json.dumps(packet([])), encoding="utf-8")
            run = subprocess.run([sys.executable, str(SKILL / "scripts/contracts.py"),
                                  "sequence", str(source), "--root", str(ROOT)],
                                 capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(run.returncode, 1)
            self.assertIs(json.loads(run.stderr)["valid"], False)
            self.assertNotIn("Traceback", run.stderr)
    def test_original_plan_and_final_acceptance_cannot_be_weakened(self):
        data = sequence();data[7]["payload"]["acceptance_ids"] = ["AC1"]
        with self.assertRaises(c.ContractError):c.validate_sequence(data)
        data = sequence();data[8]["payload"]["plan_ref"] = ref("other-plan", "synthetic/other-plan.json")
        with self.assertRaises(c.ContractError):c.validate_sequence(data)
        changed = publish();changed["message_id"] = "M10";changed["payload"]["acceptance_ids"] = ["AC1"]
        with self.assertRaises(c.ContractError):c.validate_sequence([publish(), changed])

    def test_worker_assertion_cannot_satisfy_independent_acceptance(self):
        data = sequence();data[7]["payload"]["report_ids"] = ["M3"]
        with self.assertRaises(c.ContractError):c.validate_sequence(data)
        data = sequence();data[4]["payload"]["status"] = "failed"
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_reviewer_must_compare_original_plan_candidate_tester_and_rerun(self):
        m = report("R", "reviewer", "M6")
        del m["payload"]["comparison"];self.rejects(m)
        m = report("R", "reviewer", "M6");m["payload"]["comparison"]["independent_rerun"]["status"] = "NOT_COMPARABLE"
        self.rejects(m)

    def test_agent_messages_reject_model_written_created_at(self):
        m = publish();m["created_at"] = STAMP;self.rejects(m)
        self.assertTrue(all("created_at" not in item for item in sequence()))

    def test_normalization_is_crlf_to_lf_only(self):
        normalize = lambda raw: raw.replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(normalize(b"a\r\nb\r\n")).hexdigest(),
                         hashlib.sha256(normalize(b"a\nb\n")).hexdigest())
        self.assertNotEqual(hashlib.sha256(normalize(b"a b\n")).hexdigest(),
                            hashlib.sha256(normalize(b"a  b\n")).hexdigest())

    def test_tester_command_and_reviewer_rerun_must_match(self):
        data = sequence();c.validate_sequence(data)
        for field, value in (("exit_code", 1), ("stdout_sha256", "b" * 64),
                             ("candidate_ref", ref("other", "synthetic/other.json")),
                             ("input_refs", [ref("changed-input", "synthetic/input.json")])):
            changed = copy.deepcopy(data)
            changed[6]["payload"]["comparison"]["independent_rerun"][field] = value
            changed[6]["payload"]["comparison"]["independent_rerun"]["status"] = "MISMATCH"
            changed[6]["payload"]["status"] = "failed"
            with self.subTest(field=field), self.assertRaises(c.ContractError):c.validate_sequence(changed)

    def test_exact_tester_executable_path_is_bound_to_reviewer_rerun(self):
        data = sequence()
        declared = data[4]["payload"]["deterministic_commands"][0]
        declared["command"] = r"C:\Python312\python.exe"
        data[6]["payload"]["comparison"]["independent_rerun"]["command"] = "python"
        data[6]["payload"]["status"] = "failed"
        data[6]["payload"]["comparison"]["independent_rerun"]["status"] = "MISMATCH"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)

    def test_reviewer_compares_frozen_plan_candidate_and_tester_record(self):
        data = sequence();c.validate_sequence(data)
        for field in ("plan_ref", "candidate_ref", "tester_report_ref"):
            changed = copy.deepcopy(data)
            changed[6]["payload"]["comparison"][field] = ref("forged-" + field, "synthetic/forged.json")
            with self.subTest(field=field), self.assertRaises(c.ContractError):c.validate_sequence(changed)

    def test_reviewer_report_reference_is_exact_prior_tester_message(self):
        data = sequence(); c.validate_sequence(data)
        for identity, kind in (("OTHER-TESTER", "message"), ("M6", "message"), ("M5", "report")):
            changed = copy.deepcopy(data)
            changed[6]["payload"]["comparison"]["tester_report_ref"] = ref(
                identity, "synthetic/tester-report.json", kind=kind)
            with self.subTest(identity=identity, kind=kind), self.assertRaises(c.ContractError):
                c.validate_sequence(changed)

    def test_reviewer_tester_message_reference_verifies_file_bytes_with_root(self):
        data = sequence()
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            folder = Path(directory)
            artifacts = folder / "artifacts"
            artifacts.mkdir()
            refs = {}
            def replace_refs(value):
                if isinstance(value, dict):
                    if set(value) == {"artifact_id", "path", "sha256", "kind"}:
                        identity = value["artifact_id"]
                        if identity not in refs:
                            path = f"artifacts/{len(refs)}.bin"
                            content = (json.dumps({"plan_id": "P1", "plan_revision": 1,
                                "acceptance": [{"id": "AC1"}, {"id": "AC2"}]})
                                if identity == "plan" else identity)
                            target = folder / path
                            target.write_text(content, encoding="utf-8")
                            refs[identity] = ref(identity, path,
                                hashlib.sha256(target.read_bytes()).hexdigest(),
                                "plan" if identity == "plan" else "synthetic")
                        value.clear(); value.update(refs[identity])
                    else:
                        for child in value.values():
                            replace_refs(child)
                elif isinstance(value, list):
                    for child in value:
                        replace_refs(child)
            for item in data:
                replace_refs(item)
            tester_path = folder / "tester-message.json"
            tester_path.write_text(json.dumps(data[4]), encoding="utf-8")
            data[6]["payload"]["comparison"]["tester_report_ref"] = ref(
                data[4]["message_id"], "tester-message.json",
                hashlib.sha256(tester_path.read_bytes()).hexdigest(), kind="message")
            c.validate_sequence(data, root=folder)
            tester_path.write_text("{}", encoding="utf-8")
            with self.assertRaises(c.ContractError):
                c.validate_sequence(data, root=folder)

    def test_tester_deterministic_record_has_command_cwd_inputs_hash_and_evidence(self):
        tester = report("T", "tester", "M4")["payload"]["deterministic_commands"][0]
        self.assertEqual(set(tester), {"command_id", "command", "arguments", "workdir", "candidate_ref",
                         "input_refs", "exit_code", "stdout_sha256", "acceptance_id", "evidence_ref"})
        self.assertEqual(tester["stdout_sha256"], "a" * 64)

    def test_exit_code_mismatch_fails_reviewer_acceptance(self):
        data = sequence();rerun = data[6]["payload"]["comparison"]["independent_rerun"]
        rerun["exit_code"] = 2;rerun["status"] = "MISMATCH";data[6]["payload"]["status"] = "failed"
        data[7]["payload"]["report_ids"] = ["M3", "M5", "M7"]
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_stdout_hash_mismatch_fails_reviewer_acceptance(self):
        data = sequence();rerun = data[6]["payload"]["comparison"]["independent_rerun"]
        rerun["stdout_sha256"] = "b" * 64;rerun["status"] = "MISMATCH";data[6]["payload"]["status"] = "failed"
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_not_comparable_never_passes_e8(self):
        data = sequence()[:7]
        data[4]["payload"]["deterministic_commands"] = []
        data[6]["payload"]["comparison"]["independent_rerun"] = {"status": "NOT_COMPARABLE"}
        data[6]["payload"]["status"] = "failed"
        c.validate_sequence(data)

    def test_json_assertion_without_execution_artifacts_is_rejected(self):
        m = report("R", "reviewer", "M6")
        m["evidence_refs"] = []
        self.rejects(m)
        self.assertIn("not authenticate execution", (SKILL / "references/communication.md").read_text())

    def test_reviewer_report_cannot_edit_candidate_criteria_or_tester_evidence(self):
        for field in ("candidate_bytes", "original_acceptance", "tester_evidence_bytes"):
            m = report("R", "reviewer", "M6");m["payload"][field] = "changed"
            with self.subTest(field=field), self.assertRaises(c.ContractError):c.validate_message(m)

    def test_changed_candidate_and_relevant_input_invalidate_rerun(self):
        data = sequence();data[6]["payload"]["comparison"]["independent_rerun"]["candidate_ref"] = ref("other", "synthetic/other.json")
        with self.assertRaises(c.ContractError):c.validate_sequence(data)
        data = sequence();data[6]["payload"]["comparison"]["independent_rerun"]["input_refs"] = [ref("different-input", "synthetic/input.json")]
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_missing_reviewer_comparison_evidence_cannot_pass_acceptance(self):
        data = sequence();data[6]["payload"]["comparison"]["findings"] = []
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_unresolved_comparator_discrepancy_cannot_be_reported_as_passed(self):
        m = report("R", "reviewer", "M6")
        m["payload"]["comparison"]["discrepancies"] = ["Tester evidence conflicts with frozen AC1."]
        self.rejects(m)

    def test_reviewer_requires_tester_declared_deterministic_execution(self):
        data = sequence();data[4]["payload"]["deterministic_commands"] = []
        with self.assertRaises(c.ContractError):c.validate_sequence(data)

    def test_rework_requires_failure_and_fresh_worker_attempt(self):
        data = sequence()[:5];data[-1]["payload"]["status"] = "failed"
        decision = message("D", "task.decision", "manager", "planner",
                {"disposition": "rework", "reason": "Actual fixture failed",
                 "acceptance_ids": AC, "candidate_ref": ref(), "report_ids": ["M5"],
                 "failed_acceptance_ids": ["AC1"]}, "M5")
        repair = assignment("W2", "worker", "D", ref(), "A2", "fresh-worker")
        c.validate_sequence(data + [decision, repair])
        bad = copy.deepcopy(repair);bad["attempt_id"] = "A1"
        with self.assertRaises(c.ContractError):c.validate_sequence(data + [decision, bad])
        bad = copy.deepcopy(repair);bad["recipient"]["instance_id"] = "worker-1"
        with self.assertRaises(c.ContractError):c.validate_sequence(data + [decision, bad])
        data[-1]["payload"]["status"] = "passed"
        with self.assertRaises(c.ContractError):c.validate_sequence(data + [decision])

    def test_planner_failure_rework_completes_through_fresh_independent_checks(self):
        data = sequence()
        progress_before_check = message("P0", "plan.progress", "manager", "planner",
            {"status": "checking", "objective": "Original task", "scope": ["demo/**"],
             "acceptance_ids": AC, "verified_progress": ["Manager accepted candidate"],
             "next_action": "Check original acceptance"}, "M8")
        data.insert(-1, progress_before_check)
        data[-1]["in_reply_to"] = "P0"
        data[-1]["payload"]["status"] = "blocked"
        data[-1]["payload"]["summary"] = "AC1 failed the frozen original check"
        data[-1]["payload"]["results"][0]["status"] = "failed"
        decision = message("D1", "task.decision", "manager", "planner",
            {"disposition": "rework", "reason": "Planner evidence shows AC1 failed",
             "acceptance_ids": AC, "candidate_ref": ref(), "report_ids": ["M3", "M5", "M7"],
             "failed_acceptance_ids": ["AC1"]}, "M9")
        worker = assignment("W2", "worker", "D1", ref(), "A2", "worker-2")
        repaired_candidate = ref("candidate-v2", "synthetic/candidate-v2.json")
        worker_report = report("WR2", "worker", "W2", repaired_candidate,
                               attempt="A2", instance="worker-2", input_ref=ref())
        tester_assignment = assignment("TA2", "tester", "WR2", repaired_candidate,
                                       "A2", "tester-2")
        tester_report = report("TR2", "tester", "TA2", repaired_candidate,
                               attempt="A2", instance="tester-2")
        reviewer_assignment = assignment("RA2", "reviewer", "TR2", repaired_candidate,
                                         "A2", "reviewer-2")
        reviewer_report = report("RR2", "reviewer", "RA2", repaired_candidate,
                                  attempt="A2", instance="reviewer-2", tester_message_id="TR2")
        accept = message("D2", "task.decision", "manager", "planner",
            {"disposition": "accept", "reason": "Fresh independent evidence passes",
             "acceptance_ids": AC, "candidate_ref": repaired_candidate,
             "report_ids": ["WR2", "TR2", "RR2"]}, "RR2", "A2")
        progress = message("P2", "plan.progress", "manager", "planner",
            {"status": "ready", "objective": "Original task", "scope": ["demo/**"],
             "acceptance_ids": AC, "verified_progress": ["Fresh Tester and Reviewer passed"],
             "next_action": "Check frozen plan", "candidate_ref": repaired_candidate}, "D2", "A2")
        final_check = message("PC2", "plan.check", "planner", "manager",
            {"status": "passed", "summary": "Original acceptance passed after repair",
             "acceptance_ids": AC, "plan_ref": ref("plan", "synthetic/plan.json"),
             "results": [{"acceptance_id": a, "status": "passed", "evidence_refs": [ref()]} for a in AC]},
            "P2", "A2")
        complete = data + [decision, worker, worker_report, tester_assignment, tester_report,
                           reviewer_assignment, reviewer_report, accept, progress, final_check]
        c.validate_sequence(complete)

        wrong_failed_id = copy.deepcopy(complete)
        wrong_failed_id[10]["payload"]["failed_acceptance_ids"] = ["AC2"]
        with self.assertRaises(c.ContractError):
            c.validate_sequence(wrong_failed_id)
        wrong_candidate = copy.deepcopy(complete)
        wrong_candidate[10]["payload"]["candidate_ref"] = ref("other", "synthetic/other.json")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(wrong_candidate)
        erased_report = copy.deepcopy(complete)
        erased_report[10]["payload"]["report_ids"].remove("M7")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(erased_report)
        erased_failure = copy.deepcopy(complete)
        erased_failure[9]["payload"]["results"][0]["status"] = "passed"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(erased_failure)
        missing_transition = copy.deepcopy(complete)
        missing_transition[11]["in_reply_to"] = "M9"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(missing_transition)
        same_worker = copy.deepcopy(complete)
        same_worker[11]["recipient"]["instance_id"] = "worker-1"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(same_worker)
        same_attempt = copy.deepcopy(complete)
        same_attempt[11]["attempt_id"] = "A1"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(same_attempt)
        duplicate_decision = copy.deepcopy(complete)
        duplicate_decision.append(copy.deepcopy(duplicate_decision[10]))
        with self.assertRaises(c.ContractError):
            c.validate_sequence(duplicate_decision)
        out_of_order = copy.deepcopy(complete)
        out_of_order[10], out_of_order[11] = out_of_order[11], out_of_order[10]
        with self.assertRaises(c.ContractError):
            c.validate_sequence(out_of_order)
        forged_transition = copy.deepcopy(complete)
        forged_transition[10]["payload"]["disposition"] = "accept"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(forged_transition)
        changed_progress_candidate = copy.deepcopy(complete)
        changed_progress_candidate[18]["payload"]["candidate_ref"] = ref("other", "synthetic/other.json")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(changed_progress_candidate)

    def test_rework_after_planner_check_requires_actual_failed_criteria(self):
        data = sequence()
        progress_before_check = message("P0", "plan.progress", "manager", "planner",
            {"status": "checking", "objective": "Original task", "scope": ["demo/**"],
             "acceptance_ids": AC, "verified_progress": ["Manager accepted candidate"],
             "next_action": "Check original acceptance"}, "M8")
        data.insert(-1, progress_before_check)
        data[-1]["in_reply_to"] = "P0"
        data[-1]["payload"]["status"] = "blocked"
        data[-1]["payload"]["results"][0]["status"] = "failed"
        decision = message("D", "task.decision", "manager", "planner",
            {"disposition": "rework", "reason": "Planner failed AC1",
             "acceptance_ids": AC, "candidate_ref": ref(), "report_ids": ["M5"],
             "failed_acceptance_ids": ["AC2"]}, "M9")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data + [decision])

    def test_passed_tester_cannot_hide_failed_or_unverified_checks(self):
        for status in ("failed", "blocked", "unverified"):
            m = report("T", "tester", "M4")
            m["payload"]["checks"][0]["status"] = status
            with self.subTest(status=status):
                self.rejects(m)

    def test_tester_strategy_is_assigned_not_self_approved(self):
        m = assignment("T", "tester", "M1", ref())
        del m["payload"]["oracle_ref"]
        self.rejects(m)
        data = sequence()
        data[4]["payload"]["oracle_ref"] = ref("self-oracle", "synthetic/self.json")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)

    def test_nested_artifact_identity_conflict_is_rejected(self):
        data = sequence()
        data[4]["payload"]["checks"][0]["evidence_ref"] = ref("candidate", "synthetic/different.txt", "2" * 64)
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)
        data = sequence()
        data[8]["payload"]["results"][0]["evidence_refs"] = [ref("candidate", "synthetic/changed.txt")]
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)

    def test_rework_unknown_failed_criterion_is_rejected(self):
        data = sequence()[:5];data[-1]["payload"]["status"] = "failed"
        decision = message("D", "task.decision", "manager", "planner",
                {"disposition": "rework", "reason": "Fixture failed",
                 "acceptance_ids": AC, "candidate_ref": ref(), "report_ids": ["M5"],
                 "failed_acceptance_ids": ["UNKNOWN"]}, "M5")
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data + [decision])

    def test_acceptance_cannot_hide_known_failed_candidate_report(self):
        data = sequence()
        failed = report("FAILED", "tester", "M4", status="failed")
        data.insert(4, failed)
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data)

    def test_passing_final_check_requires_manager_evidence_acceptance(self):
        data = sequence()[:3]
        check = sequence()[-1];check["in_reply_to"] = "M3"
        with self.assertRaises(c.ContractError):
            c.validate_sequence(data + [check])

    def test_artifact_path_shape_and_actual_hash_sensitivity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            target = Path(directory) / "evidence.txt";target.write_text("actual evidence", encoding="utf-8")
            item = ref("real", target.relative_to(ROOT).as_posix(), hashlib.sha256(target.read_bytes()).hexdigest())
            c.artifact(item, ROOT)
            item["sha256"] = "0" * 64
            with self.assertRaises(c.ContractError):c.artifact(item, ROOT)
            item["path"] = "../outside"
            with self.assertRaises(c.ContractError):c.artifact(item, ROOT)
            item["path"] = "/etc/secret"
            with self.assertRaises(c.ContractError):c.artifact(item, ROOT)

    def test_artifact_symlink_escape_is_rejected_when_supported(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            parent = Path(directory)
            authorized = parent / "authorized"
            authorized.mkdir()
            outside = parent / "outside.txt"
            outside.write_text("outside root", encoding="utf-8")
            link = authorized / "escape.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            item = ref("symlink-escape", link.relative_to(ROOT).as_posix(),
                       hashlib.sha256(outside.read_bytes()).hexdigest())
            with self.assertRaises(c.ContractError):
                c.artifact(item, ROOT)

    def test_published_json_message_examples_match_current_contract(self):
        examples = ROOT / "docs" / "CouncilFlow-Full-Plan" / "examples"
        for name in ("job.assign.json", "job.report.json"):
            with self.subTest(name=name):
                packet = c.loads((examples / name).read_bytes())
                c.validate_message(packet)

    def test_plan_artifact_acceptance_is_checked_not_only_packet(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps({"plan_id": "P1", "plan_revision": 1,
                                       "acceptance": [{"id": "AC1"}]}))
            m = publish()
            m["payload"]["plan_ref"] = ref("actual-plan", path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
            m["evidence_refs"] = [m["payload"]["plan_ref"]]
            with self.assertRaises(c.ContractError):c.validate_sequence([m], root=ROOT)

    def test_unknown_role_specific_and_nested_check_fields(self):
        m = report("T", "tester", "M4")
        m["payload"]["checks"][0]["approved_by_self"] = True;self.rejects(m)
        m = report("W", "worker", "M2");del m["payload"]["changed_files"];self.rejects(m)
        m = report("T", "tester", "M4");m["payload"]["input_candidate_ref"] = ref();self.rejects(m)

    def test_cli_invalid_json_fails_with_structured_error_no_traceback(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            path = Path(directory) / "bad.json";path.write_text('{"x":1,"x":2}')
            run = subprocess.run([sys.executable, str(SKILL / "scripts/contracts.py"), "message", str(path)],
                                 capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(run.returncode, 1)
            self.assertFalse(json.loads(run.stderr)["valid"])
            self.assertNotIn("Traceback", run.stderr)


class PolicyAndDiagnosticTests(unittest.TestCase):
    def test_real_restricted_policy_roles_and_native_mapping(self):
        data = c.parse_policy((SKILL / "policies/roles.yaml").read_bytes())
        c.validate_policy(data)
        self.assertEqual(set(data["roles"]), c.ROLES)
        self.assertFalse(data["resources"]["retry_accounting"] != "instruction_only")

    def test_yaml_duplicates_and_unsupported_features_really_fail(self):
        for source in ['x: "a"\nx: "b"\n', "x: unquoted\n", "x: &anchor\n",
                       "x: *alias\n", "x: !!str hello\n", "x:\n - bad\n",
                       'x:\n   y: "bad"\n', 'x:\n\ty: "bad"\n',
                       "x: 1.5\n", "x: null\n", 'x: |\n  text\n']:
            with self.subTest(source=source), self.assertRaises(c.ContractError):
                c.parse_policy(source)

    def test_yaml_authority_retry_and_boolean_mutations_fail(self):
        original = c.parse_policy((SKILL / "policies/roles.yaml").read_bytes())
        mutations = [
            ("security", "grants_os_permissions", True),
            ("authority", "ordinary_repair_owner_approval", True),
            ("resources", "infrastructure_retries", True),
            ("resources", "crash_recoveries", 3),
            ("evidence", "tester_self_approves_oracle", True),
            ("context", "independent_tester", False),
        ]
        for section, key, value in mutations:
            d = copy.deepcopy(original);d[section][key] = value
            with self.subTest(section=section), self.assertRaises(c.ContractError):c.validate_policy(d)
        d = copy.deepcopy(original);d["roles"]["manager"]["application_code"] = True
        with self.assertRaises(c.ContractError):c.validate_policy(d)

    def test_jsonl_real_reference_checks_and_invalid_lines(self):
        event = {"protocol": "council-flow", "version": "1.0", "event_id": "E1",
                 "event_type": "plan_published", "created_at": STAMP, "message_id": "M1",
                 "plan_id": "P1", "task_id": "T1", "attempt_id": "A1", "evidence_refs": []}
        self.assertEqual(c.validate_jsonl(json.dumps(event) + "\n", messages=[publish()]), 1)
        for value in ["{}\n", json.dumps(event) + "\n\n", json.dumps(event) + "\n" + json.dumps(event),
                      '{"x":NaN}\n', json.dumps({**event, "raw_prompt": "not allowed"}),
                      json.dumps({**event, "message_id": "unknown"}),
                      json.dumps({**event, "created_at": "2026-02-30T00:00:00Z"})]:
            with self.subTest(value=value[:40]), self.assertRaises(c.ContractError):
                c.validate_jsonl(value, messages=[publish()])

    def test_diagnostic_clock_timestamp_is_syntax_only_not_provenance(self):
        event = {"protocol": "council-flow", "version": "1.0", "event_id": "CLOCK1",
                 "event_type": "plan_published", "created_at": STAMP, "message_id": "M1",
                 "plan_id": "P1", "task_id": "T1", "attempt_id": "A1", "evidence_refs": []}
        self.assertEqual(c.validate_jsonl(json.dumps(event) + "\n", messages=[publish()]), 1)
        self.assertIn("provenance", (SKILL / "references/communication.md").read_text())

    def test_contract_spec_tracks_exact_envelope_and_routes(self):
        spec = json.loads((SKILL / "references/message-contract.json").read_text())
        self.assertEqual(set(spec["envelope_required"]), c.FIELDS)
        self.assertEqual(set(spec["routes"]), set(c.ROUTES))
        self.assertEqual(spec["bounds"]["message_bytes"], c.MAX_BYTES)

    def test_integration_requires_formats_in_real_skill_and_native_roles(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertIn("MUST be UTF-8 JSON", text)
        self.assertIn("policies/roles.yaml", text)
        self.assertIn("JSONL", text)
        for path in (ROOT / ".codex/agents").glob("council-*.toml"):
            text = path.read_text()
            self.assertIn("MUST be UTF-8 JSON", text)
            self.assertIn("policies/roles.yaml", text)
        self.assertNotIn("JSON or equivalent", (SKILL / "references/roles.md").read_text())

    def test_examples_are_explicitly_synthetic(self):
        self.assertIn("Synthetic", __doc__)
        self.assertNotIn("session_id", json.dumps(sequence()))


if __name__ == "__main__":
    unittest.main()
