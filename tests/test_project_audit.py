"""ADR-001 M6: Technical Audit selection, routing rules and the advisory rule.

Uses the real project_state.py through its CLI entry point. Ledger v1 holds G1, AC1, AC2 (bootstrap).
Slice A covers AC1 and slice B covers AC2; both are DONE, so the audit of v1 is eligible.

Routing rules under test:
  R1 implementation finding   -> recorded in the audit only; no state change.
  R2 requirement_change       -> reviewer reopen evidence for the Planner; plan and ledger untouched.
  R3 owner_choice             -> the affected slice (and only it) is paused; owner_items lists it.
  R4 pass                     -> recorded; no state change.
Advisory rule: an audit never changes delivery state, never writes the ledger, and never carries a
delivery field; a fully passing audit leaves every DONE slice DONE.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/council-flow/scripts/project_state.py"
SPEC = importlib.util.spec_from_file_location("councilflow_project_state_m6", SCRIPT)
ps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ps)

TS = "2026-11-26T10:00:00Z"
TS2 = "2026-11-26T11:00:00Z"


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ps.main([str(a) for a in args])
    return code, json.loads(out.getvalue())


def codes(result):
    return {e["code"] for e in result["errors"]}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        (self.tmp / "owner.txt").write_bytes(b"Owner says keep it simple\n")
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": "First."}, {"id": "AC2", "criterion": "Second."}]),
            encoding="utf-8")
        (self.tmp / "rerun.txt").write_bytes(b"rerun output\n")
        self.assertEqual(run("init", "--project", self.project, "--budget", "1")[0], 0)
        self.assertEqual(run("source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                             "--received-at", TS)[0], 0)
        self.assertEqual(run("bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                             "--source-id", "S0001", "--goal", "Ship it", "--created-at", TS)[0], 0)
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",))])

    # --- helpers -------------------------------------------------------------

    def slice(self, sid, ids=("AC1",), status="DONE"):
        return {"slice_id": sid, "ledger_version": 1, "ledger_ids": list(ids), "depends_on": [],
                "readiness": "READY", "status": status, "run_dir": None, "model_routing": None}

    def write_plan(self, slices):
        plan = {"schema": "councilflow-plan", "version": "1.0", "plan_version": 1, "slices": slices}
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def plan_status(self):
        plan = json.loads((self.project / "plan.json").read_text(encoding="utf-8"))
        return {s["slice_id"]: s["status"] for s in plan["slices"]}

    def snapshot(self):
        """Bytes of everything an audit must never write: the ledger and the plan."""
        return {p.name: p.read_bytes() for p in sorted((self.project / "ledger").glob("L*.json"))} | {
            "plan.json": (self.project / "plan.json").read_bytes()}

    def entry(self, lid, verdict, kind, finding="Observed behaviour differs.", slice_ids=None,
              consequence=None):
        return {"ledger_id": lid, "verdict": verdict, "kind": kind, "finding": finding,
                "slice_ids": list(slice_ids or []), "consequence": consequence}

    def write_entries(self, entries, reruns=None, name="entries.json"):
        if reruns is None:
            reruns = [{"command": "python -m unittest", "exit_code": 0,
                       "output": str(self.tmp / "rerun.txt")}]
        path = self.tmp / name
        path.write_text(json.dumps({"entries": entries, "reruns": reruns}), encoding="utf-8")
        return path

    def select(self, version=1):
        return run("audit-select", "--project", self.project, "--ledger-version", version)

    def record(self, entries, version=1, reruns=None, used="sonnet", name="entries.json"):
        path = self.write_entries(entries, reruns, name)
        return run("audit-record", "--project", self.project, "--ledger-version", version,
                   "--entries", path, "--route-used", used, "--route-source", "role_default",
                   "--route-reason", "Reviewer default for audit.", "--created-at", TS2)

    def audit_records(self):
        return sorted((self.project / "audit").glob("A*.json"))

    def evidence_records(self):
        return sorted((self.project / "evidence").glob("E*.json"))

    # --- eligibility ---------------------------------------------------------

    def test_eligible_once_all_slices_are_done(self):
        code, out = self.select()
        self.assertEqual(code, 0)
        self.assertEqual(out["status"], "PASS")

    def test_not_eligible_while_a_slice_is_not_verified(self):
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",), status="PAUSED")])
        code, out = self.select()
        self.assertEqual(code, 1)
        self.assertIn("not_eligible", codes(out))

    def test_cancelled_slices_are_not_audited(self):
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",), status="CANCELLED")])
        code, out = self.select()
        self.assertEqual(code, 0)
        self.assertEqual(out["slice_ids"], ["A"])

    def test_one_audit_per_ledger_version(self):
        self.assertEqual(self.record([self.entry("AC1", "pass", "none"),
                                      self.entry("AC2", "pass", "none")])[0], 0)
        code, out = self.select()
        self.assertEqual(code, 1)
        self.assertIn("not_eligible", codes(out))

    def test_audit_runs_only_against_latest_ledger_version(self):
        code, out = self.select(version=2)
        self.assertEqual(code, 1)
        self.assertIn("not_eligible", codes(out))

    # --- R1: implementation finding is advisory only -------------------------

    def test_r1_implementation_finding_changes_no_state(self):
        before = self.snapshot()
        code, out = self.record([self.entry("AC1", "gap", "implementation", slice_ids=["A"]),
                                 self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.evidence_records(), [])
        self.assertEqual(len(self.audit_records()), 1)

    # --- R2: requirement_change becomes a Reopen Request for the Planner -----

    def test_r2_requirement_change_writes_reopen_evidence_and_keeps_plan_and_ledger(self):
        before = self.snapshot()
        code, out = self.record([self.entry("AC1", "gap", "requirement_change",
                                            finding="AC1 no longer matches what the Owner wants.",
                                            slice_ids=["A"], consequence="A must be reopened."),
                                 self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 0, out)
        self.assertEqual(out["reopen_evidence_ids"], ["E0001"])
        self.assertEqual(out["paused_slice_ids"], [])
        evidence = json.loads(self.evidence_records()[0].read_text(encoding="utf-8"))
        self.assertEqual(evidence["source_agent"], "reviewer")
        self.assertEqual(evidence["ledger_ids"], ["AC1"])
        self.assertEqual(evidence["affected_slices"], ["A"])
        self.assertEqual(evidence["reopen_request"]["status"], "submitted")
        self.assertEqual(evidence["reopen_request"]["consequence"], "A must be reopened.")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.plan_status(), {"A": "DONE", "B": "DONE"})

    def test_r2_requires_a_consequence(self):
        code, out = self.record([self.entry("AC1", "gap", "requirement_change", slice_ids=["A"]),
                                 self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 1)
        self.assertIn("audit_reopen", codes(out))
        self.assertEqual(self.evidence_records(), [])

    # --- R3: owner_choice pauses the affected slice and goes to the Owner ----

    def test_r3_owner_choice_pauses_only_the_affected_slice(self):
        code, out = self.record([self.entry("AC1", "risk", "owner_choice",
                                            finding="Two valid behaviours; the Owner must choose.",
                                            slice_ids=["A"]),
                                 self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 0, out)
        self.assertEqual(out["paused_slice_ids"], ["A"])
        self.assertEqual(self.plan_status(), {"A": "PAUSED", "B": "DONE"})
        audit = json.loads(self.audit_records()[0].read_text(encoding="utf-8"))
        self.assertEqual(audit["owner_items"], [{"ledger_id": "AC1",
                                                 "finding": "Two valid behaviours; the Owner must choose.",
                                                 "slice_ids": ["A"]}])

    def test_r3_owner_choice_never_writes_the_ledger(self):
        before = self.ledger_bytes()
        self.record([self.entry("AC1", "risk", "owner_choice", slice_ids=["A"]),
                     self.entry("AC2", "pass", "none")])
        self.assertEqual(self.ledger_bytes(), before)

    def ledger_bytes(self):
        return {p.name: p.read_bytes() for p in sorted((self.project / "ledger").glob("L*.json"))}

    # --- R4: pass ------------------------------------------------------------

    def test_r4_pass_changes_no_state(self):
        before = self.snapshot()
        code, out = self.record([self.entry("AC1", "pass", "none"), self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.evidence_records(), [])

    # --- advisory rule -------------------------------------------------------

    def test_advisory_audit_never_writes_delivery_state(self):
        self.record([self.entry("AC1", "gap", "implementation", slice_ids=["A"]),
                     self.entry("AC2", "risk", "implementation", slice_ids=["B"])])
        audit = json.loads(self.audit_records()[0].read_text(encoding="utf-8"))
        self.assertEqual(set(audit), ps.AUDIT_FIELDS)
        self.assertFalse(any("deliver" in key or key == "status" or key == "passed" for key in audit))
        self.assertEqual(self.plan_status(), {"A": "DONE", "B": "DONE"})

    def test_gap_findings_are_recorded_and_validate_without_delivery_change(self):
        # Gaps and risks are recorded and the audit passes validation; nothing in project state
        # declares delivery, so the Owner's acceptance remains the only path to delivered.
        code, out = self.record([self.entry("AC1", "gap", "implementation", slice_ids=["A"]),
                                 self.entry("AC2", "gap", "implementation", slice_ids=["B"])])
        self.assertEqual(code, 0, out)
        self.assertEqual(run("validate", "--project", self.project)[0], 0)

    def test_advisory_rejects_a_delivery_field_in_the_audit(self):
        self.record([self.entry("AC1", "pass", "none"), self.entry("AC2", "pass", "none")])
        path = self.audit_records()[0]
        audit = json.loads(path.read_text(encoding="utf-8"))
        audit["delivery_status"] = "delivered"
        path.write_text(json.dumps(audit), encoding="utf-8")
        code, out = run("validate", "--project", self.project)
        self.assertEqual(code, 1)
        self.assertIn("bad_fields", codes(out))

    # --- input rules and tamper checks ---------------------------------------

    def test_reviewer_never_runs_on_haiku(self):
        code, out = self.record([self.entry("AC1", "pass", "none"), self.entry("AC2", "pass", "none")],
                                used="claude-haiku-5-5")
        self.assertEqual(code, 1)
        self.assertIn("audit_routing", codes(out))
        self.assertEqual(self.audit_records(), [])

    def test_every_audited_ledger_id_needs_exactly_one_entry(self):
        code, out = self.record([self.entry("AC1", "pass", "none")])
        self.assertEqual(code, 1)
        self.assertIn("audit_coverage", codes(out))
        code, out = self.record([self.entry("AC1", "pass", "none"), self.entry("AC1", "pass", "none"),
                                 self.entry("AC2", "pass", "none")], name="dup.json")
        self.assertIn("audit_coverage", codes(out))

    def test_owner_slices_must_hold_the_ledger_id(self):
        code, out = self.record([self.entry("AC1", "risk", "owner_choice", slice_ids=["B"]),
                                 self.entry("AC2", "pass", "none")])
        self.assertEqual(code, 1)
        self.assertIn("audit_slices", codes(out))
        self.assertEqual(self.plan_status(), {"A": "DONE", "B": "DONE"})

    def test_at_least_one_deterministic_rerun_is_required(self):
        code, out = self.record([self.entry("AC1", "pass", "none"), self.entry("AC2", "pass", "none")],
                                reruns=[])
        self.assertEqual(code, 1)
        self.assertIn("audit_rerun", codes(out))

    def test_tampered_owner_items_fail_validation(self):
        self.record([self.entry("AC1", "risk", "owner_choice", slice_ids=["A"]),
                     self.entry("AC2", "pass", "none")])
        path = self.audit_records()[0]
        audit = json.loads(path.read_text(encoding="utf-8"))
        audit["owner_items"] = []
        path.write_text(json.dumps(audit), encoding="utf-8")
        code, out = run("validate", "--project", self.project)
        self.assertEqual(code, 1)
        self.assertIn("audit_owner", codes(out))


if __name__ == "__main__":
    unittest.main()
