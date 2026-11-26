"""ADR-001 M5: Tester retest selection, pass and fail paths, and independence rules.

Uses the real project_state.py through its CLI entry point. Ledger v1 holds G1, AC1, AC2 (bootstrap);
v2 supersedes AC1 with R1, so slice A (AC1) is closed-but-affected and slice B (AC2) is unaffected.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/council-flow/scripts/project_state.py"
SPEC = importlib.util.spec_from_file_location("councilflow_project_state_m5", SCRIPT)
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


class RetestTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        (self.tmp / "owner.txt").write_bytes(b"Owner says keep it simple\n")
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": "First."}, {"id": "AC2", "criterion": "Second."}]),
            encoding="utf-8")
        (self.tmp / "oracle.txt").write_bytes(b"run the acceptance checks for A\n")
        (self.tmp / "out.txt").write_bytes(b"observed output\n")
        self.assertEqual(run("init", "--project", self.project, "--budget", "1")[0], 0)
        self.assertEqual(run("source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                             "--received-at", TS)[0], 0)
        self.assertEqual(run("bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                             "--source-id", "S0001", "--goal", "Ship it", "--created-at", TS)[0], 0)

    # --- helpers -------------------------------------------------------------

    def snapshot(self):
        """Bytes of everything the Tester must never write: the ledger and the plan."""
        return {p.name: p.read_bytes() for p in sorted((self.project / "ledger").glob("L*.json"))} | {
            "plan.json": (self.project / "plan.json").read_bytes()}

    def ledger_snapshot(self):
        return {p.name: p.read_bytes() for p in sorted((self.project / "ledger").glob("L*.json"))}

    def slice(self, sid, ids=("AC1",), status="DONE"):
        return {"slice_id": sid, "ledger_version": 1, "ledger_ids": list(ids), "depends_on": [],
                "readiness": "READY", "status": status, "run_dir": None, "model_routing": None}

    def write_plan(self, slices):
        plan = {"schema": "councilflow-plan", "version": "1.0", "plan_version": 1, "slices": slices}
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def write_next(self, mutate):
        n = max(int(p.stem[1:]) for p in (self.project / "ledger").glob("L*.json"))
        prev = (self.project / "ledger" / f"L{n:04d}.json").read_bytes()
        data = json.loads(prev.decode("utf-8"))
        data["ledger_version"] = n + 1
        data["previous_sha256"] = hashlib.sha256(prev).hexdigest()
        mutate(data["entries"])
        (self.project / "ledger" / f"L{n + 1:04d}.json").write_text(json.dumps(data), encoding="utf-8")
        return n + 1

    def supersede(self, old, new, version):
        def mutate(entries):
            for e in entries:
                if e["id"] == old:
                    e["status"] = "superseded"
            entries.append({"id": new, "type": "Requirement", "content": f"{new} text",
                            "source_ids": ["S0001"], "evidence_ids": [], "status": "active",
                            "created_at": TS, "version_introduced": version,
                            "supersedes": [old], "affected_slices": []})
        return mutate

    def start(self):
        """Ledger v2 supersedes AC1 with R1. A (AC1) is DONE and closed-but-affected; B (AC2) unaffected."""
        self.write_plan([self.slice("A", ("AC1",)), self.slice("B", ("AC2",))])
        return self.write_next(self.supersede("AC1", "R1", 2))

    def select(self, version):
        return run("retest-select", "--project", self.project, "--to-version", version)

    def record(self, version, slice_id="A", result="pass", **overrides):
        opts = {"slice": slice_id, "to-version": version, "result": result,
                "finding": "Checked against R1.", "artifact": str(self.tmp / "out.txt"),
                "oracle": str(self.tmp / "oracle.txt"), "route-used": "sonnet",
                "route-source": "role_default", "route-reason": "Tester default for design.",
                "created-at": TS2}
        if result == "fail":
            opts.update({"contradiction": "A's check no longer matches R1.", "consequence": "A needs reopening."})
        for key, value in overrides.items():
            opts[key.replace("_", "-")] = value
        args = ["retest-record", "--project", self.project]
        for key, value in opts.items():
            if value is not None:
                args += [f"--{key}", value]
        return run(*args)

    # --- selection -----------------------------------------------------------

    def test_selection_picks_only_closed_affected_slices(self):
        v = self.start()
        code, result = self.select(v)
        self.assertEqual((code, result["status"]), (0, "PASS"))
        self.assertEqual((result["retest"], result["already_passed"]), (["A"], []))

    def test_open_affected_slices_are_not_retest_candidates(self):
        self.write_plan([self.slice("A", ("AC1",), status="RUNNING"), self.slice("B", ("AC2",))])
        v = self.write_next(self.supersede("AC1", "R1", 2))
        code, result = self.select(v)
        self.assertEqual((code, result["retest"]), (0, []))

    def test_selection_with_no_plan_is_empty(self):
        v = self.write_next(self.supersede("AC1", "R1", 2))
        self.assertEqual(self.select(v)[1]["retest"], [])

    # --- pass path -----------------------------------------------------------

    def test_pass_records_evidence_and_retest_without_touching_plan_or_ledger(self):
        v = self.start()
        before = self.snapshot()
        code, result = self.record(v, result="pass")
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual((result["retest_id"], result["evidence_id"]), ("T0001", "E0001"))
        self.assertEqual(self.snapshot(), before)
        evidence = json.loads((self.project / "evidence" / "E0001.json").read_text(encoding="utf-8"))
        self.assertEqual((evidence["source_agent"], evidence["reopen_request"]), ("tester", None))
        self.assertEqual((evidence["affected_slices"], evidence["ledger_ids"]), (["A"], ["AC1"]))
        self.assertEqual(self.validate()[1]["status"], "PASS")

    def test_pass_is_not_selected_again_for_the_same_version(self):
        v = self.start()
        self.assertEqual(self.record(v, result="pass")[0], 0)
        code, result = self.select(v)
        self.assertEqual((code, result["retest"], result["already_passed"]), (0, [], ["A"]))

    def test_pass_for_old_version_does_not_satisfy_a_later_change(self):
        v2 = self.start()
        self.assertEqual(self.record(v2, result="pass")[0], 0)
        # Manager re-pins A to v2 and its R1 after the pass (simulated; the Tester never writes the plan).
        plan = json.loads((self.project / "plan.json").read_text(encoding="utf-8"))
        plan["slices"][0].update({"ledger_version": 2, "ledger_ids": ["R1"]})
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(self.select(v2)[1]["retest"], [])
        v3 = self.write_next(self.supersede("R1", "R2", 3))
        code, result = self.select(v3)
        self.assertEqual((code, result["retest"]), (0, ["A"]))

    # --- fail path -----------------------------------------------------------

    def test_fail_creates_submitted_reopen_request_for_the_manager(self):
        v = self.start()
        ledger_before = self.ledger_snapshot()
        code, result = self.record(v, result="fail")
        self.assertEqual((code, result["status"]), (0, "PASS"), result)
        self.assertEqual(self.ledger_snapshot(), ledger_before)
        evidence = json.loads((self.project / "evidence" / "E0001.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["reopen_request"], {"status": "submitted",
                                                      "contradiction": "A's check no longer matches R1.",
                                                      "consequence": "A needs reopening."})
        self.assertEqual((evidence["affected_slices"], evidence["ledger_ids"]), (["A"], ["AC1"]))
        self.assertEqual(self.validate()[1]["status"], "PASS")

    def test_fail_auto_pauses_only_the_cited_slice_and_keeps_it_in_retest(self):
        v = self.start()
        self.assertEqual(self.record(v, result="fail")[0], 0)
        code, result = self.select(v)
        self.assertEqual((result["retest"], result["already_passed"]), (["A"], []))
        plan = json.loads((self.project / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual([(s["slice_id"], s["status"], s["ledger_version"], s["ledger_ids"])
                          for s in plan["slices"]],
                         [("A", "PAUSED", 1, ["AC1"]), ("B", "DONE", 1, ["AC2"])])

    def test_pass_never_changes_plan_and_fail_then_pass_clears_retest(self):
        v = self.start()
        self.assertEqual(self.record(v, result="fail")[0], 0)
        self.assertEqual(self.record(v, result="pass")[0], 0)
        self.assertEqual(self.select(v)[1]["retest"], [])
        plan = json.loads((self.project / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["slices"][0]["status"], "PAUSED")  # resuming is the Manager's call
        self.assertEqual(self.validate()[1]["status"], "PASS")

    # --- independence rules --------------------------------------------------

    def test_unaffected_or_open_slice_cannot_be_retested(self):
        v = self.start()
        code, result = self.record(v, slice_id="B")
        self.assertEqual((code, result["status"]), (1, "FAIL"))
        self.assertIn("not_retestable", codes(result))
        self.write_plan([self.slice("A", ("AC1",), status="RUNNING"), self.slice("B", ("AC2",))])
        self.assertIn("not_retestable", codes(self.record(v)[1]))

    def test_fail_needs_reopen_fields_and_pass_takes_none(self):
        v = self.start()
        code, result = run("retest-record", "--project", self.project, "--slice", "A", "--to-version", v,
                           "--result", "fail", "--finding", "x", "--artifact", self.tmp / "out.txt",
                           "--oracle", self.tmp / "oracle.txt", "--route-used", "sonnet",
                           "--route-source", "role_default", "--route-reason", "r", "--created-at", TS2)
        self.assertEqual(code, 1)
        self.assertIn("bad_value", codes(result))
        self.assertIn("bad_value", codes(self.record(v, result="pass", contradiction="c")[1]))

    def test_artifact_and_oracle_must_exist_and_be_hashed(self):
        v = self.start()
        code, result = self.record(v, artifact=str(self.tmp / "missing.txt"))
        self.assertIn("bad_input", codes(result))
        code, result = self.record(v, oracle=str(self.tmp / "missing.txt"))
        self.assertIn("bad_input", codes(result))
        self.assertFalse((self.project / "evidence").exists())

    def test_tester_routing_must_use_the_schema_and_no_hint_source_mismatch(self):
        v = self.start()
        code, result = self.record(v, route_source="hint")
        self.assertIn("slice_model_routing", codes(result))
        self.assertEqual(code, 1)

    def test_validate_rejects_retest_citing_non_tester_or_mismatched_evidence(self):
        v = self.start()
        self.assertEqual(self.record(v, result="pass")[0], 0)
        evidence_path = self.project / "evidence" / "E0001.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence["source_agent"] = "worker"
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        self.assertIn("retest_evidence_agent", codes(self.validate()[1]))
        evidence["source_agent"] = "tester"
        evidence["reopen_request"] = {"status": "submitted", "contradiction": "c", "consequence": "q"}
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        self.assertIn("retest_evidence_mismatch", codes(self.validate()[1]))

    def test_validate_rejects_bad_retest_record(self):
        v = self.start()
        self.assertEqual(self.record(v, result="pass")[0], 0)
        path = self.project / "retest" / "T0001.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["result"] = "maybe"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertIn("bad_value", codes(self.validate()[1]))

    def validate(self):
        return run("validate", "--project", self.project)

    def test_cli_usage_error_exits_2_and_missing_plan_fails_closed(self):
        v = self.start()
        with self.assertRaises(SystemExit) as usage:
            with contextlib.redirect_stderr(io.StringIO()):
                ps.main(["retest-select", "--project", str(self.project)])  # --to-version missing
        self.assertEqual(usage.exception.code, 2)
        self.assertEqual(self.select(v)[0], 0)
        code, result = run("retest-record", "--project", self.project, "--slice", "A", "--to-version", v,
                           "--result", "pass", "--finding", "x", "--artifact", self.tmp / "out.txt",
                           "--oracle", self.tmp / "oracle.txt", "--route-used", "sonnet",
                           "--route-source", "host", "--route-reason", "r", "--created-at", TS2)
        self.assertEqual((code, result["status"]), (0, "PASS"), result)


if __name__ == "__main__":
    unittest.main()
