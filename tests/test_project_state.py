"""Plain-file project state validator (ADR-001 section 3)."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/council-flow/scripts/project_state.py"
SPEC = importlib.util.spec_from_file_location("councilflow_project_state", SCRIPT)
ps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ps)

TS = "2026-11-26T10:00:00Z"
CRITERION = "Keep café behavior.  "  # non-ASCII and trailing spaces


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ps.main([str(a) for a in args])
    return code, json.loads(out.getvalue())


def codes(result):
    return {e["code"] for e in result["errors"]}


class ProjectStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        (self.tmp / "owner.txt").write_bytes("Owner says café\r\nline  \n".encode("utf-8"))
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": CRITERION}, {"id": "AC2", "criterion": "Second."}]),
            encoding="utf-8")
        self.assertEqual(run("init", "--project", self.project, "--budget", "1")[0], 0)
        self.assertEqual(run("source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                             "--received-at", TS)[0], 0)
        self.assertEqual(run("bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                             "--source-id", "S0001", "--goal", "Ship it", "--created-at", TS)[0], 0)

    def ledger_path(self, n):
        return self.project / "ledger" / f"L{n:04d}.json"

    def read_ledger(self, n):
        return json.loads(self.ledger_path(n).read_text(encoding="utf-8"))

    def entry(self, eid, kind, status, version, **kw):
        base = {"id": eid, "type": kind, "content": f"{eid} text", "source_ids": ["S0001"],
                "evidence_ids": [], "status": status, "created_at": TS,
                "version_introduced": version, "supersedes": [], "affected_slices": []}
        base.update(kw)
        return base

    def write_next(self, mutate):
        """Write ledger version N+1 from the latest, after mutate(entries)."""
        n = max(int(p.stem[1:]) for p in (self.project / "ledger").glob("L*.json"))
        prev = self.ledger_path(n).read_bytes()
        data = json.loads(prev.decode("utf-8"))
        data["ledger_version"] = n + 1
        data["previous_sha256"] = hashlib.sha256(prev).hexdigest()
        mutate(data["entries"])
        self.ledger_path(n + 1).write_text(json.dumps(data), encoding="utf-8")
        return n + 1

    def validate(self):
        return run("validate", "--project", self.project)

    def test_happy_path_preserves_criteria_bytes(self):
        code, result = self.validate()
        self.assertEqual((code, result["status"], result["errors"]), (0, "PASS", []))
        self.assertEqual(result["ledger_version"], 1)
        self.assertEqual(result["budget"], {"limit": 1, "used": 0, "exceeded": False})
        entries = {e["id"]: e for e in self.read_ledger(1)["entries"]}
        self.assertEqual(entries["AC1"]["content"], CRITERION)
        self.assertEqual(entries["G1"]["type"], "Goal")
        stored = (self.project / "sources/S0001.txt").read_bytes()
        self.assertEqual(stored, (self.tmp / "owner.txt").read_bytes())

    def test_cli_subprocess_exit_codes(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "validate", "--project", str(self.project)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["status"], "PASS")
        bad = subprocess.run([sys.executable, str(SCRIPT), "validate"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)

    def test_overwrite_refused(self):
        code, result = run("init", "--project", self.project)
        self.assertEqual((code, codes(result)), (1, {"exists"}))
        code, result = run("bootstrap", "--project", self.project, "--criteria", self.tmp / "criteria.json",
                           "--source-id", "S0001", "--created-at", TS)
        self.assertEqual((code, codes(result)), (1, {"exists"}))

    def test_source_hash_tamper_fails(self):
        (self.project / "sources/S0001.txt").write_bytes(b"changed")
        self.assertIn("source_hash_mismatch", codes(self.validate()[1]))

    def test_gap_in_numbering_fails(self):
        self.ledger_path(1).rename(self.ledger_path(2))
        self.assertIn("numbering_gap", codes(self.validate()[1]))

    def test_content_edit_in_v2_fails(self):
        def edit(entries):
            entries[1]["content"] = "rewritten"
        self.write_next(edit)
        self.assertIn("entry_changed", codes(self.validate()[1]))

    def test_dropped_entry_that_is_superseded_reports_instead_of_crashing(self):
        def drop(entries):
            gone = entries.pop(1)
            entries.append(self.entry("AC1b", "Requirement", "active", 2, supersedes=[gone["id"]]))
        self.write_next(drop)
        status, out = self.validate()
        self.assertEqual(status, 1)
        self.assertIn("entry_dropped", codes(out))

    def test_illegal_status_move_fails(self):
        def revive(entries):
            entries.append(self.entry("A1", "Assumption", "unconfirmed", 2))
        self.write_next(revive)
        self.assertEqual(self.validate()[1]["status"], "PASS")

        def bad(entries):
            for e in entries:
                if e["id"] == "A1":
                    e["status"] = "resolved"
        self.write_next(bad)
        self.assertIn("entry_status", codes(self.validate()[1]))

    def test_active_entry_cannot_be_revived(self):
        def supersede(entries):
            entries[1]["status"] = "superseded"
            entries.append(self.entry("R9", "Requirement", "active", 2, supersedes=[entries[1]["id"]]))
        self.write_next(supersede)
        self.assertEqual(self.validate()[1]["status"], "PASS")

        def revive(entries):
            entries[1]["status"] = "active"
        self.write_next(revive)
        self.assertIn("status_transition", codes(self.validate()[1]))

    def test_supersede_without_superseding_entry_fails(self):
        def supersede(entries):
            entries[1]["status"] = "superseded"
        self.write_next(supersede)
        self.assertIn("supersede_unbacked", codes(self.validate()[1]))

    def test_assumption_confirmation_needs_decision(self):
        self.write_next(lambda e: e.append(self.entry("A1", "Assumption", "unconfirmed", 2)))
        self.assertEqual(self.validate()[1]["budget"]["used"], 1)

        def confirm(entries):
            for e in entries:
                if e["id"] == "A1":
                    e["status"] = "confirmed"
        v3 = self.write_next(confirm)
        self.assertIn("promotion_without_decision", codes(self.validate()[1]))

        data = self.read_ledger(v3)
        data["entries"].append(self.entry("D1", "Decision", "active", v3))
        self.ledger_path(v3).write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.validate()[1]["status"], "PASS")

    def test_previous_sha_mismatch_fails(self):
        v2 = self.write_next(lambda e: None)
        data = self.read_ledger(v2)
        data["previous_sha256"] = "0" * 64
        self.ledger_path(v2).write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("previous_hash_mismatch", codes(self.validate()[1]))

    def test_budget_exceeded_is_reported_not_failed(self):
        def add(entries):
            entries.append(self.entry("A1", "Assumption", "unconfirmed", 2))
            entries.append(self.entry("A2", "Assumption", "unconfirmed", 2))
        self.write_next(add)
        code, result = self.validate()
        self.assertEqual((code, result["status"]), (0, "PASS"))
        self.assertEqual(result["budget"], {"limit": 1, "used": 2, "exceeded": True})

    def write_plan(self, slices):
        plan = {"schema": "councilflow-plan", "version": "1.0", "plan_version": 1, "slices": slices}
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def slice(self, sid, ids=("AC1",), deps=()):
        return {"slice_id": sid, "ledger_version": 1, "ledger_ids": list(ids), "depends_on": list(deps),
                "readiness": "READY", "status": "PLANNED", "run_dir": None, "model_routing": None}

    def test_plan_valid_unknown_ledger_id_and_cycle(self):
        self.write_plan([self.slice("A"), self.slice("B", deps=["A"])])
        self.assertEqual(self.validate()[1]["status"], "PASS")
        self.write_plan([self.slice("A", ids=["NOPE"])])
        self.assertIn("slice_ledger_ref", codes(self.validate()[1]))
        self.write_plan([self.slice("A", deps=["B"]), self.slice("B", deps=["A"])])
        self.assertIn("slice_cycle", codes(self.validate()[1]))
        bad = self.slice("A")
        bad["run_dir"] = "../x"
        self.write_plan([bad])
        self.assertIn("slice_run_dir", codes(self.validate()[1]))

    def write_evidence(self, **kw):
        record = {"evidence_id": "E0001", "source_agent": "tester", "finding": "Observed.",
                  "artifacts": [{"path": "out.txt", "sha256": "a" * 64}], "ledger_ids": ["AC1"],
                  "affected_slices": ["A"], "created_at": TS, "reopen_request": None}
        record.update(kw)
        directory = self.project / "evidence"
        directory.mkdir(exist_ok=True)
        (directory / "E0001.json").write_text(json.dumps(record), encoding="utf-8")

    def test_evidence_reopen_rules(self):
        reopen = {"status": "submitted", "contradiction": "c", "consequence": "q"}
        self.write_evidence(reopen_request=reopen)
        self.assertEqual(self.validate()[1]["status"], "PASS")
        self.write_evidence(reopen_request=reopen, ledger_ids=[])
        self.assertIn("reopen_no_ledger_ids", codes(self.validate()[1]))
        self.write_evidence(reopen_request=reopen, ledger_ids=["NOPE"])
        self.assertIn("evidence_ledger_ref", codes(self.validate()[1]))

    def test_extra_key_fails(self):
        data = self.read_ledger(1)
        data["entries"][0]["extra"] = 1
        self.ledger_path(1).write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("entry_fields", codes(self.validate()[1]))

    def test_orphan_source_file_fails(self):
        (self.project / "sources/S0002.txt").write_bytes(b"x")
        self.assertIn("orphan_source_text", codes(self.validate()[1]))


if __name__ == "__main__":
    unittest.main()
