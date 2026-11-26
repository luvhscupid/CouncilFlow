"""ADR-001 M6: Reviewer as Technical Audit (advisory), through the real project_state.py CLI and
the message contract.

Ledger v1 holds G1 (Goal), AC1 and AC2 (bootstrap). Slices A (AC1) and B (AC2) are DONE and pinned
to v1, so the audit for v1 may run. Routing rules: R1 reopen to the Planner, R2 Owner decision
pauses affected slices only, R3 ordinary engineering finding changes nothing, R4 advisory (no
delivery claim), R5 a pass carries no reopen request and no pause.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/council-flow"
SPEC = importlib.util.spec_from_file_location("councilflow_project_state_m6", SKILL / "scripts/project_state.py")
ps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ps)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fx  # noqa: E402
import test_contract_v11 as fx11  # noqa: E402

c = fx.c
TS = "2026-11-26T10:00:00Z"
TS2 = "2026-11-26T12:00:00Z"
DELIVERY_WORDS = ("deliver", "approv", "accept")


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ps.main([str(a) for a in args])
    return code, json.loads(out.getvalue())


def codes(result):
    return {e["code"] for e in result["errors"]}


def keys_of(value):
    if isinstance(value, dict):
        return set(value) | set().union(*(keys_of(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(keys_of(v) for v in value)) if value else set()
    return set()


class AuditTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        (self.tmp / "owner.txt").write_bytes(b"Owner wants a working tool\n")
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": "First."}, {"id": "AC2", "criterion": "Second."}]),
            encoding="utf-8")
        (self.tmp / "report.txt").write_bytes(b"audit notes\n")
        (self.tmp / "tester-run.txt").write_bytes(b"tester execution record\n")
        (self.tmp / "rerun-out.txt").write_bytes(b"ok\r\n")
        self.assertEqual(run("init", "--project", self.project, "--budget", "1")[0], 0)
        self.assertEqual(run("source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                             "--received-at", TS)[0], 0)
        self.assertEqual(run("bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                             "--source-id", "S0001", "--goal", "Ship a working tool", "--created-at", TS)[0], 0)
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",))])

    # --- helpers -------------------------------------------------------------

    def slice(self, sid, ids, status="DONE", routing=None):
        return {"slice_id": sid, "ledger_version": 1, "ledger_ids": list(ids), "depends_on": [],
                "readiness": "READY", "status": status, "run_dir": None, "model_routing": routing}

    def write_plan(self, slices):
        plan = {"schema": "councilflow-plan", "version": "1.0", "plan_version": 1, "slices": slices}
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def plan(self):
        return json.loads((self.project / "plan.json").read_text(encoding="utf-8"))

    def ledger_snapshot(self):
        return {p.name: p.read_bytes() for p in sorted((self.project / "ledger").glob("L*.json"))}

    def snapshot(self):
        return self.ledger_snapshot() | {"plan.json": (self.project / "plan.json").read_bytes()}

    def write_next(self, mutate):
        n = max(int(p.stem[1:]) for p in (self.project / "ledger").glob("L*.json"))
        prev = (self.project / "ledger" / f"L{n:04d}.json").read_bytes()
        data = json.loads(prev.decode("utf-8"))
        data["ledger_version"] = n + 1
        data["previous_sha256"] = hashlib.sha256(prev).hexdigest()
        mutate(data["entries"])
        (self.project / "ledger" / f"L{n + 1:04d}.json").write_text(json.dumps(data), encoding="utf-8")
        return n + 1

    def supersede(self, old, new, version, kind="Requirement"):
        def mutate(entries):
            for e in entries:
                if e["id"] == old:
                    e["status"] = "superseded"
            entries.append({"id": new, "type": kind, "content": f"{new} text", "source_ids": ["S0001"],
                            "evidence_ids": [], "status": "active", "created_at": TS,
                            "version_introduced": version, "supersedes": [old], "affected_slices": []})
        return mutate

    def rerun(self, **overrides):
        digest = hashlib.sha256(b"ok\n").hexdigest()
        body = {"command_id": "CMD1", "command": "python", "arguments": ["-m", "unittest"], "workdir": ".",
                "exit_code": 0, "stdout_sha256": digest, "tester_exit_code": 0,
                "tester_stdout_sha256": digest, "tester_evidence": str(self.tmp / "tester-run.txt"),
                "output": str(self.tmp / "rerun-out.txt")}
        body.update(overrides)
        path = self.tmp / "rerun.json"
        path.write_text(json.dumps(body), encoding="utf-8")
        return path

    def passes(self, *ids):
        return [{"ledger_id": i, "verdict": "pass", "finding": f"{i} holds in the delivered system.",
                 "route": "none"} for i in ids]

    def record(self, findings, version=1, rerun=None, route_used="sonnet", **overrides):
        path = self.tmp / "findings.json"
        path.write_text(json.dumps(findings), encoding="utf-8")
        opts = {"to-version": version, "findings": path, "rerun": rerun or self.rerun(),
                "artifact": self.tmp / "report.txt", "route-used": route_used,
                "route-source": "role_default", "route-reason": "Reviewer default is Sonnet.",
                "created-at": TS2}
        opts.update({k.replace("_", "-"): v for k, v in overrides.items()})
        args = ["audit-record", "--project", self.project]
        for key, value in opts.items():
            if value is not None:
                args += [f"--{key}", value]
        return run(*args)

    def select(self, version=1):
        return run("audit-select", "--project", self.project, "--to-version", version)

    def validate(self):
        return run("validate", "--project", self.project)

    def evidence(self, eid):
        return json.loads((self.project / "evidence" / f"{eid}.json").read_text(encoding="utf-8"))

    def audit_path(self, aid="A0001"):
        return self.project / "audit" / f"{aid}.json"

    def tamper(self, change, aid="A0001"):
        record = json.loads(self.audit_path(aid).read_text(encoding="utf-8"))
        change(record)
        self.audit_path(aid).write_text(json.dumps(record), encoding="utf-8")
        return codes(self.validate()[1])

    # --- selection: verified gate and once per Goal version -------------------

    def test_select_reports_verified_goal_and_pinned_version(self):
        code, result = self.select()
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual((result["verified"], result["unverified"], result["slices"]), (True, [], ["A", "B"]))
        self.assertEqual((result["goal_ids"], result["goal_version"], result["audited"]), (["G1"], 1, False))

    def test_unfinished_slice_or_empty_plan_is_not_verified_and_cannot_be_audited(self):
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",), status="RUNNING")])
        code, result = self.select()
        self.assertEqual((code, result["verified"]), (0, False))
        self.assertEqual(result["unverified"], [{"slice_id": "B", "reason": "status RUNNING"}])
        code, result = self.record(self.passes("G1", "AC1", "AC2"))
        self.assertEqual((code, codes(result)), (1, {"not_verified"}))
        self.assertFalse((self.project / "audit").exists())
        self.write_plan([self.slice("A", ("AC1",), status="CANCELLED")])
        self.assertFalse(self.select()[1]["verified"])

    def test_pending_tester_retest_blocks_the_audit_until_it_passes(self):
        v2 = self.write_next(self.supersede("AC1", "R1", 2))
        result = self.select(v2)[1]
        self.assertEqual(result["unverified"],
                         [{"slice_id": "A", "reason": "awaiting Tester retest for ledger version 2"}])
        self.assertIn("not_verified", codes(self.record(self.passes("G1", "R1", "AC2"), version=v2)[1]))
        (self.tmp / "oracle.txt").write_bytes(b"checks\n")
        code, _ = run("retest-record", "--project", self.project, "--slice", "A", "--to-version", v2,
                      "--result", "pass", "--finding", "Still holds.", "--artifact", self.tmp / "report.txt",
                      "--oracle", self.tmp / "oracle.txt", "--route-used", "sonnet",
                      "--route-source", "role_default", "--route-reason", "r", "--created-at", TS2)
        self.assertEqual(code, 0)
        self.assertTrue(self.select(v2)[1]["verified"])

    def test_audit_pins_the_current_ledger_version_only(self):
        v2 = self.write_next(self.supersede("AC2", "R2", 2))
        self.assertIn("stale_ledger_version", codes(self.select(1)[1]))
        self.assertIn("stale_ledger_version", codes(self.record(self.passes("G1", "AC1", "AC2"), version=1)[1]))
        self.assertEqual(self.select(v2)[0], 0)

    def test_ledger_without_goal_cannot_be_audited(self):
        other = self.tmp / "nogoal"
        run("init", "--project", other)
        run("source-add", "--project", other, "--file", self.tmp / "owner.txt", "--received-at", TS)
        run("bootstrap", "--project", other, "--criteria", self.tmp / "criteria.json",
            "--source-id", "S0001", "--created-at", TS)
        code, result = run("audit-select", "--project", other, "--to-version", 1)
        self.assertEqual((code, codes(result)), (1, {"no_goal"}))

    def test_one_audit_per_goal_version_and_a_new_goal_version_reopens_it(self):
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"))[0], 0)
        result = self.select()[1]
        self.assertEqual((result["audited"], result["audit_id"]), (True, "A0001"))
        self.assertIn("already_audited", codes(self.record(self.passes("G1", "AC1", "AC2"))[1]))
        # A requirement-only change keeps Goal version 1: still refused.
        v2 = self.write_next(self.supersede("AC2", "R2", 2))
        self.write_plan([self.slice("A", ("AC1",)), dict(self.slice("B", ("R2",)), ledger_version=2)])
        self.assertIn("already_audited", codes(self.record(self.passes("G1", "AC1", "R2"), version=v2)[1]))
        # An Owner-approved Goal change creates Goal version 3: a new audit may run.
        v3 = self.write_next(self.supersede("G1", "G2", 3, kind="Goal"))
        code, result = self.record(self.passes("G2", "AC1", "R2"), version=v3)
        self.assertEqual((code, result["audit_id"], result["goal_version"]), (0, "A0002", 3), result)
        self.assertEqual(self.validate()[1]["status"], "PASS")

    def test_validate_rejects_two_audits_of_one_goal_version(self):
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"))[0], 0)
        copy_path = self.audit_path("A0002")
        record = json.loads(self.audit_path().read_text(encoding="utf-8"))
        record["audit_id"] = "A0002"
        copy_path.write_text(json.dumps(record), encoding="utf-8")
        self.assertIn("audit_duplicate_goal", codes(self.validate()[1]))

    # --- R1: requirement change becomes a Reopen Request to the Planner --------

    def test_r1_requirement_finding_is_a_submitted_reopen_request_and_never_edits_the_ledger(self):
        findings = self.passes("G1", "AC2") + [{
            "ledger_id": "AC1", "verdict": "gap", "finding": "AC1 contradicts the observed data model.",
            "route": "reopen", "affected_slices": ["A"], "contradiction": "AC1 assumes one user per account.",
            "consequence": "Slice A delivers the wrong model."}]
        before = self.snapshot()
        code, result = self.record(findings)
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual(self.snapshot(), before)  # ledger and plan untouched
        self.assertEqual((result["reopen_evidence_ids"], result["paused_slices"]), (["E0003"], []))
        evidence = self.evidence("E0003")
        self.assertEqual(evidence["reopen_request"], {"status": "submitted",
                                                      "contradiction": "AC1 assumes one user per account.",
                                                      "consequence": "Slice A delivers the wrong model."})
        self.assertEqual((evidence["source_agent"], evidence["ledger_ids"], evidence["affected_slices"]),
                         ("reviewer", ["AC1"], ["A"]))
        # The Reviewer reports it to the Manager, who forwards it unchanged to the Planner.
        body = {"evidence_id": "E0003", "ledger_ids": evidence["ledger_ids"],
                "affected_slices": evidence["affected_slices"],
                "contradiction": evidence["reopen_request"]["contradiction"],
                "consequence": evidence["reopen_request"]["consequence"],
                "evidence_ref": fx.ref("E0003", "evidence/E0003.json")}
        first = fx11.reopen("RO1", "reviewer", "manager", "M1", **body)
        forward = fx11.reopen("RO2", "manager", "planner", "RO1", **body)
        start = [dict(fx.publish(), version="1.1")]
        c.validate_sequence(start + [first, forward])
        altered = fx11.reopen("RO2", "manager", "planner", "RO1", **dict(body, consequence="Softened."))
        self.assertEqual(fx11.code(self, c.validate_sequence, start + [first, altered]), "reopen_forward")

    def test_r1_reopen_needs_contradiction_consequence_and_slices(self):
        finding = {"ledger_id": "AC1", "verdict": "gap", "finding": "Wrong.", "route": "reopen",
                   "affected_slices": ["A"]}
        self.assertIn("audit_route", codes(self.record(self.passes("G1") + [finding])[1]))
        finding.update({"contradiction": "c", "consequence": "q", "affected_slices": []})
        self.assertIn("audit_route", codes(self.record(self.passes("G1") + [finding])[1]))
        self.assertFalse((self.project / "evidence").exists())

    # --- R2: Owner-controlled decision pauses affected slices only ------------

    def test_r2_owner_decision_pauses_only_affected_slices_and_keeps_the_ledger(self):
        ledger_before = self.ledger_snapshot()
        plan_before = self.plan()
        findings = self.passes("G1", "AC1") + [{
            "ledger_id": "AC2", "verdict": "risk", "finding": "AC2 stores personal data unencrypted.",
            "route": "owner_decision", "decision_class": "security_data_financial_legal",
            "affected_slices": ["B"]}]
        code, result = self.record(findings)
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual(self.ledger_snapshot(), ledger_before)
        self.assertEqual(result["paused_slices"], ["B"])
        self.assertEqual(result["owner_decisions"], [{"ledger_id": "AC2", "decision_class":
                                                      "security_data_financial_legal",
                                                      "affected_slices": ["B"], "evidence_id": "E0003"}])
        plan = self.plan()
        expected = copy.deepcopy(plan_before)
        expected["slices"][1]["status"] = "PAUSED"
        self.assertEqual(plan, expected)  # only B's status changed; A untouched
        self.assertIsNone(self.evidence("E0003")["reopen_request"])
        self.assertEqual(self.validate()[1]["status"], "PASS")

    def test_r2_cheap_reversible_is_not_an_owner_decision(self):
        finding = {"ledger_id": "AC2", "verdict": "risk", "finding": "Naming.", "route": "owner_decision",
                   "decision_class": "cheap_reversible", "affected_slices": ["B"]}
        self.assertIn("audit_route", codes(self.record(self.passes("G1", "AC1") + [finding])[1]))
        self.assertEqual(self.plan()["slices"][1]["status"], "DONE")

    def test_r2_owner_classes_are_roles_yaml_classes_above_the_planner_default(self):
        policy = c.parse_policy((SKILL / "policies/roles.yaml").read_text(encoding="utf-8"))
        adaptive = policy["adaptive"]
        self.assertEqual(set(ps.OWNER_CLASSES),
                         set(adaptive["decision_classes"]) - set(adaptive["planner_default_classes"]))

    # --- R3: ordinary engineering gap or risk ---------------------------------

    def test_r3_engineering_gap_is_recorded_without_pause_or_reopen(self):
        findings = self.passes("G1", "AC2") + [{
            "ledger_id": "AC1", "verdict": "gap", "finding": "Error path of A lacks a test; Manager rework.",
            "route": "none", "affected_slices": ["A"]},
        ]
        before = self.snapshot()
        code, result = self.record(findings)
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual((result["reopen_evidence_ids"], result["owner_decisions"], result["paused_slices"]),
                         ([], [], []))
        self.assertIsNone(self.evidence("E0003")["reopen_request"])
        audit = json.loads(self.audit_path().read_text(encoding="utf-8"))
        self.assertEqual([(v["ledger_id"], v["verdict"], v["route"]) for v in audit["verdicts"]],
                         [("G1", "pass", "none"), ("AC2", "pass", "none"), ("AC1", "gap", "none")])

    def test_r3_route_none_cannot_carry_reopen_or_decision_fields(self):
        finding = {"ledger_id": "AC1", "verdict": "risk", "finding": "f", "route": "none",
                   "contradiction": "c", "consequence": "q"}
        self.assertIn("audit_route", codes(self.record(self.passes("G1") + [finding])[1]))
        finding = {"ledger_id": "AC1", "verdict": "risk", "finding": "f", "route": "none",
                   "decision_class": "owner_objective"}
        self.assertIn("audit_route", codes(self.record(self.passes("G1") + [finding])[1]))

    # --- R4: advisory only -----------------------------------------------------

    def test_r4_all_pass_leaves_delivery_state_unchanged_and_claims_no_delivery(self):
        before = self.snapshot()
        code, result = self.record(self.passes("G1", "AC1", "AC2"))
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual(self.snapshot(), before)
        for key in keys_of(result) | keys_of(json.loads(self.audit_path().read_text(encoding="utf-8"))):
            for word in DELIVERY_WORDS:
                self.assertNotIn(word, key.lower())
        self.assertEqual(self.select()[1]["verified"], True)  # slices stay as they were

    def test_r4_validation_rejects_an_audit_record_claiming_delivery(self):
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"))[0], 0)
        self.assertIn("audit_claims_delivery", self.tamper(lambda r: r.update(delivery_approved=True)))
        self.assertIn("audit_claims_delivery", self.tamper(
            lambda r: (r.pop("delivery_approved"), r["verdicts"][0].update(accepted=True))))

    def test_r4_contract_audit_payload_has_no_delivery_field(self):
        data = self.contract_run()
        data[6]["payload"]["audit"]["delivered"] = True
        self.assertEqual(fx11.code(self, c.validate_message, data[6]), "unknown_field")

    # --- R5: pass carries no reopen request and no pause -------------------------

    def test_r5_pass_cannot_route_to_reopen_or_owner(self):
        for route, extra in (("reopen", {"contradiction": "c", "consequence": "q"}),
                             ("owner_decision", {"decision_class": "owner_objective"})):
            finding = dict({"ledger_id": "AC1", "verdict": "pass", "finding": "f", "route": route,
                            "affected_slices": ["A"]}, **extra)
            with self.subTest(route=route):
                self.assertIn("audit_route", codes(self.record(self.passes("G1", "AC2") + [finding])[1]))
        self.assertFalse((self.project / "audit").exists())
        self.assertEqual(self.plan()["slices"][0]["status"], "DONE")

    def test_r5_validation_rejects_a_pass_with_a_route_or_reopen_evidence(self):
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"))[0], 0)
        self.assertIn("audit_route", self.tamper(lambda r: r["verdicts"][0].update(route="reopen")))
        self.tamper(lambda r: r["verdicts"][0].update(route="none"))
        path = self.project / "evidence" / "E0001.json"
        evidence = json.loads(path.read_text(encoding="utf-8"))
        evidence["reopen_request"] = {"status": "submitted", "contradiction": "c", "consequence": "q"}
        path.write_text(json.dumps(evidence), encoding="utf-8")
        self.assertIn("audit_evidence_mismatch", codes(self.validate()[1]))

    def test_r5_contract_pass_route_must_be_none(self):
        data = self.contract_run()
        data[6]["payload"]["audit"]["verdicts"][0]["route"] = "reopen"
        self.assertEqual(fx11.code(self, c.validate_message, data[6]), "audit_route")

    # --- Reviewer is never Haiku ---------------------------------------------------

    def test_reviewer_routed_to_haiku_is_rejected(self):
        code, result = self.record(self.passes("G1", "AC1", "AC2"), route_used="claude-haiku-5-5")
        self.assertEqual((code, codes(result)), (1, {"reviewer_haiku"}))
        self.assertFalse((self.project / "audit").exists())
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"), route_used="opus")[0], 0)
        self.assertIn("reviewer_haiku", self.tamper(
            lambda r: r["model_routing"]["reviewer"].update(used="Haiku")))

    def test_plan_reviewer_routing_to_haiku_fails_validation(self):
        choice = {"hint": None, "used": "haiku", "source": "host", "reason": "host model"}
        self.write_plan([self.slice("A", ("AC1",), routing={"reviewer": choice})])
        self.assertIn("reviewer_haiku", codes(self.validate()[1]))
        self.write_plan([self.slice("A", ("AC1",), routing={"worker": choice})])
        self.assertEqual(self.validate()[1]["status"], "PASS")  # Haiku stays allowed for the Worker

    # --- pinned ledger ids, verdict values, Goal coverage ------------------------------

    def test_finding_must_cite_a_current_entry_of_the_pinned_ledger_version(self):
        self.assertIn("audit_ledger_ref", codes(self.record(self.passes("G1", "AC1", "AC9"))[1]))
        v2 = self.write_next(self.supersede("AC2", "R2", 2))
        self.write_plan([self.slice("A", ("AC1",)), dict(self.slice("B", ("R2",)), ledger_version=2)])
        self.assertIn("audit_ledger_ref",
                      codes(self.record(self.passes("G1", "AC1", "AC2"), version=v2)[1]))  # superseded
        self.assertEqual(self.record(self.passes("G1", "AC1", "R2"), version=v2)[0], 0)
        self.assertIn("audit_ledger_ref", self.tamper(lambda r: r["verdicts"][0].update(ledger_id="ZZ9")))

    def test_verdict_outside_gap_risk_pass_is_rejected(self):
        finding = {"ledger_id": "AC1", "verdict": "approved", "finding": "f", "route": "none"}
        self.assertIn("audit_verdict", codes(self.record(self.passes("G1") + [finding])[1]))
        self.assertEqual(self.record(self.passes("G1", "AC1"))[0], 0)
        self.assertIn("audit_verdict", self.tamper(lambda r: r["verdicts"][0].update(verdict="ok")))

    def test_every_goal_entry_needs_a_verdict_and_ids_do_not_repeat(self):
        self.assertIn("audit_goal_missing", codes(self.record(self.passes("AC1", "AC2"))[1]))
        self.assertIn("audit_duplicate", codes(self.record(self.passes("G1", "AC1", "AC1"))[1]))

    # --- the Reviewer's independent rerun is required ---------------------------------

    def test_independent_rerun_is_required_and_hash_checked(self):
        bad = self.tmp / "empty.json"
        bad.write_text("{}", encoding="utf-8")
        self.assertIn("audit_rerun_required", codes(self.record(self.passes("G1", "AC1", "AC2"), rerun=bad)[1]))
        rerun = self.rerun(stdout_sha256="b" * 64, tester_stdout_sha256="b" * 64)
        self.assertIn("audit_rerun_hash", codes(self.record(self.passes("G1", "AC1", "AC2"), rerun=rerun)[1]))
        rerun = self.rerun(output=str(self.tmp / "missing.txt"))
        self.assertIn("bad_input", codes(self.record(self.passes("G1", "AC1", "AC2"), rerun=rerun)[1]))
        self.assertFalse((self.project / "audit").exists())

    def test_mismatching_rerun_cannot_come_with_all_pass(self):
        rerun = self.rerun(tester_exit_code=1)
        self.assertIn("audit_contradiction",
                      codes(self.record(self.passes("G1", "AC1", "AC2"), rerun=rerun)[1]))
        finding = {"ledger_id": "AC1", "verdict": "risk", "finding": "Rerun exit differs.", "route": "none"}
        code, result = self.record(self.passes("G1", "AC2") + [finding], rerun=rerun)
        self.assertEqual((code, result["rerun_status"]), (0, "MISMATCH"), result)

    def test_validation_rejects_missing_or_not_comparable_rerun(self):
        self.assertEqual(self.record(self.passes("G1", "AC1", "AC2"))[0], 0)
        self.assertIn("audit_rerun_required", self.tamper(lambda r: r.update(independent_rerun=None)))
        self.assertIn("audit_rerun_required", self.tamper(
            lambda r: r.update(independent_rerun=dict(self.saved_rerun, status="NOT_COMPARABLE"))))
        self.assertIn("audit_rerun_status", self.tamper(
            lambda r: r.update(independent_rerun=dict(self.saved_rerun, status="MATCH", exit_code=3))))

    @property
    def saved_rerun(self):
        if not hasattr(self, "_saved"):
            digest = hashlib.sha256(b"ok\n").hexdigest()
            fp = {"path": "x", "sha256": "0" * 64}
            self._saved = {"command_id": "CMD1", "command": "python", "arguments": [], "workdir": ".",
                           "exit_code": 0, "stdout_sha256": digest, "tester_exit_code": 0,
                           "tester_stdout_sha256": digest, "tester_evidence": fp, "output": fp,
                           "status": "MATCH"}
        return self._saved

    def test_contract_audit_needs_a_comparable_independent_rerun(self):
        data = self.contract_run()
        report = data[6]
        report["payload"]["status"] = "failed"
        report["payload"]["comparison"]["independent_rerun"] = {"status": "NOT_COMPARABLE"}
        self.assertEqual(fx11.code(self, c.validate_message, report), "audit_rerun")

    # --- message contract ------------------------------------------------------------

    def contract_run(self):
        """The standard 1.1 run with a Technical Audit payload on the Reviewer report (M7)."""
        data = fx11.run11()
        report = data[6]
        audit_ref = fx.ref("A0001", "audit/A0001.json")
        report["payload"]["audit"] = {"audit_ref": audit_ref, "goal_version": 1, "verdicts": [
            {"ledger_id": "G1", "verdict": "pass", "finding": "Goal met.", "route": "none",
             "evidence_refs": [fx.ref("E0001", "evidence/E0001.json")]},
            {"ledger_id": "AC1", "verdict": "gap", "finding": "Needs a requirement change.", "route": "reopen",
             "evidence_refs": [fx.ref("E0002", "evidence/E0002.json")]}]}
        report["evidence_refs"].append(audit_ref)
        return data

    def test_contract_accepts_an_audit_on_the_reviewer_report_and_keeps_the_run_valid(self):
        data = self.contract_run()
        c.validate_message(data[6])
        c.validate_sequence(data)

    def test_contract_audit_is_reviewer_only_and_1_1_only(self):
        data = self.contract_run()
        tester = data[4]
        tester["payload"]["audit"] = copy.deepcopy(data[6]["payload"]["audit"])
        self.assertEqual(fx11.code(self, c.validate_message, tester), "role_payload")
        old = copy.deepcopy(data[6])
        old["version"] = "1.0"
        for key in ("ledger_version", "slice_id"):
            del old["payload"][key]
        self.assertEqual(fx11.code(self, c.validate_message, old), "unknown_field")

    def test_contract_audit_verdict_and_citation_rules(self):
        for change, expected in (
                (lambda a, m: a["verdicts"][0].update(verdict="approved"), "enum"),
                (lambda a, m: a["verdicts"][1].update(ledger_id="G1"), "duplicate_item"),
                (lambda a, m: a["verdicts"][0].update(evidence_refs=[]), "evidence"),
                (lambda a, m: m["evidence_refs"].pop(), "evidence"),
                (lambda a, m: a.update(goal_version=2), "ledger_pin")):
            data = self.contract_run()
            change(data[6]["payload"]["audit"], data[6])
            with self.subTest(expected=expected):
                self.assertEqual(fx11.code(self, c.validate_message, data[6]), expected)

    def test_cli_usage_error_exits_2(self):
        with self.assertRaises(SystemExit) as usage:
            with contextlib.redirect_stderr(io.StringIO()):
                ps.main(["audit-select", "--project", str(self.project)])
        self.assertEqual(usage.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
