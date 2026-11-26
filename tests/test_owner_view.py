"""ADR-001 M7: the generated, read-only Owner view.

Fixture: ledger v1 (G1, AC1, AC2) is audited, then ledger v2 adds an unconfirmed Assumption (A1),
an open question (Q1) and a Decision (D1). Slices A and B are pinned to v1. T0001 is a Tester retest.

One test per ADR-001 section 4 field:
  goal, confirmed requirements, provisional assumptions, open questions, decision history,
  current ledger version, slice readiness and execution status, QA results, audit findings,
  unconfirmed default budget usage.
Plus: stale marker, a rejected write path, never writes the ledger, exact question wording,
and the dashboard reads the generated file only.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/council-flow/scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ps = load("councilflow_project_state_m7", "project_state.py")
ov = load("councilflow_owner_view_m7", "owner_view.py")
dash = load("councilflow_dashboard_m7", "dashboard.py")

TS = "2026-11-26T10:00:00Z"
TS2 = "2026-11-26T11:00:00Z"
# Exact wording must survive: runs of spaces, a tab, a newline, accents, quotes.
WORDING = "Should  the report use\tSQLite or  Postgres?\nAnswer “yes” or no — café "
DEFAULT = "SQLite  (single file)"


def run(module, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = module.main([str(a) for a in args])
    return code, json.loads(out.getvalue())


def tree(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()}


class OwnerViewTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "repo"
        self.project = self.root / ".councilflow" / "project"
        (self.tmp / "owner.txt").write_bytes(b"Owner says keep it simple\n")
        (self.tmp / "criteria.json").write_text(
            json.dumps([{"id": "AC1", "criterion": "First."}, {"id": "AC2", "criterion": "Second."}]),
            encoding="utf-8")
        (self.tmp / "rerun.txt").write_bytes(b"rerun output\n")
        self.assertEqual(run(ps, "init", "--project", self.project, "--budget", "3")[0], 0)
        self.assertEqual(run(ps, "source-add", "--project", self.project, "--file", self.tmp / "owner.txt",
                             "--received-at", TS)[0], 0)
        self.assertEqual(run(ps, "bootstrap", "--project", self.project, "--criteria",
                             self.tmp / "criteria.json", "--source-id", "S0001", "--goal", "Ship it",
                             "--created-at", TS)[0], 0)
        self.write_plan()
        self.audit()
        self.write_ledger_v2()
        self.write_retest()
        self.write_question_packet()
        self.assertEqual(run(ps, "validate", "--project", self.project)[1]["status"], "PASS")

    # --- fixture builders ----------------------------------------------------

    def write_plan(self):
        def item(sid, ids, status, readiness):
            return {"slice_id": sid, "ledger_version": 1, "ledger_ids": ids, "depends_on": [],
                    "readiness": readiness, "status": status, "run_dir": None, "model_routing": None}
        plan = {"schema": "councilflow-plan", "version": "1.0", "plan_version": 1,
                "slices": [item("A", ["AC1"], "DONE", "READY"),
                           item("B", ["AC2"], "DONE", "PROCEED_WITH_ASSUMPTIONS")]}
        (self.project / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def audit(self):
        entries = {"entries": [
            {"ledger_id": "AC1", "verdict": "gap", "kind": "implementation", "finding": "AC1 edge case missing.",
             "slice_ids": ["A"], "consequence": None},
            {"ledger_id": "AC2", "verdict": "pass", "kind": "none", "finding": "AC2 holds.",
             "slice_ids": [], "consequence": None}],
            "reruns": [{"command": "python -m unittest", "exit_code": 0, "output": str(self.tmp / "rerun.txt")}]}
        path = self.tmp / "entries.json"
        path.write_text(json.dumps(entries), encoding="utf-8")
        code, out = run(ps, "audit-record", "--project", self.project, "--ledger-version", 1, "--entries", path,
                        "--route-used", "sonnet", "--route-source", "role_default",
                        "--route-reason", "Reviewer default.", "--created-at", TS2)
        self.assertEqual(code, 0, out)

    def ledger_path(self, number):
        return self.project / "ledger" / f"L{number:04d}.json"

    def write_ledger_v2(self, number=2, extra=()):
        previous = self.ledger_path(number - 1)
        data = json.loads(previous.read_text(encoding="utf-8"))

        def entry(eid, kind, content, status):
            return {"id": eid, "type": kind, "content": content, "source_ids": ["S0001"], "evidence_ids": [],
                    "status": status, "created_at": TS2, "version_introduced": number,
                    "supersedes": [], "affected_slices": []}
        new = [entry(*e) for e in extra] if extra else [
            entry("A1", "Assumption", "Use SQLite.", "unconfirmed"),
            entry("Q1", "Open", WORDING, "open"),
            entry("D1", "Decision", "Keep the report single page.", "active")]
        ledger = {"schema": "councilflow-ledger", "version": "1.0", "ledger_version": number,
                  "previous_sha256": hashlib.sha256(previous.read_bytes()).hexdigest(),
                  "created_at": TS2, "entries": data["entries"] + new}
        self.ledger_path(number).write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_retest(self):
        art = {"path": str(self.tmp / "rerun.txt"), "sha256": hashlib.sha256(b"rerun output\n").hexdigest()}
        evidence = {"evidence_id": "E0001", "source_agent": "tester", "finding": "Retest passed.",
                    "artifacts": [art], "ledger_ids": ["AC1"], "affected_slices": ["A"],
                    "created_at": TS2, "reopen_request": None}
        retest = {"retest_id": "T0001", "slice_id": "A", "ledger_version": 1, "ledger_ids": ["AC1"],
                  "result": "pass", "evidence_id": "E0001", "oracle": art,
                  "model_routing": {"tester": {"hint": None, "used": "sonnet", "source": "role_default",
                                               "reason": "Tester default."}}, "created_at": TS2}
        (self.project / "evidence").mkdir(exist_ok=True)
        (self.project / "retest").mkdir(exist_ok=True)
        (self.project / "evidence" / "E0001.json").write_text(json.dumps(evidence), encoding="utf-8")
        (self.project / "retest" / "T0001.json").write_text(json.dumps(retest), encoding="utf-8")

    def write_question_packet(self):
        packet = {"question_id": "Q1", "text": WORDING, "blocking": False, "decision_class": "cheap_reversible",
                  "affected_slices": ["B"], "permitted_default": DEFAULT, "reason": "Needed to pick storage."}
        (self.project / "questions").mkdir(exist_ok=True)
        (self.project / "questions" / "Q1.json").write_text(json.dumps(packet), encoding="utf-8")

    def generate(self, **kw):
        code, out = run(ov, "generate", "--project", self.project, "--generated-at", TS2)
        self.assertEqual(code, 0, out)
        return json.loads((self.project / "owner-view.json").read_text(encoding="utf-8"))

    # --- one test per ADR-001 section 4 field --------------------------------

    def test_field_current_project_goal(self):
        self.assertEqual(self.generate()["goal"]["content"], "Ship it")

    def test_field_confirmed_requirements(self):
        view = self.generate()
        self.assertEqual([e["id"] for e in view["confirmed_requirements"]], ["AC1", "AC2"])
        self.assertEqual(view["confirmed_requirements"][0]["content"], "First.")

    def test_field_provisional_assumptions(self):
        view = self.generate()
        self.assertEqual([e["id"] for e in view["provisional_assumptions"]], ["A1"])
        self.assertEqual(view["provisional_assumptions"][0]["status"], "unconfirmed")

    def test_field_open_questions(self):
        questions = self.generate()["open_questions"]
        self.assertEqual([q["id"] for q in questions], ["Q1"])
        self.assertEqual(questions[0]["blocking"], False)
        self.assertEqual(questions[0]["reversibility"], "cheap_reversible")
        self.assertEqual(questions[0]["affected_slices"], ["B"])

    def test_field_decision_history(self):
        history = self.generate()["decision_history"]
        self.assertEqual([(e["id"], e["content"]) for e in history], [("D1", "Keep the report single page.")])

    def test_field_current_ledger_version(self):
        view = self.generate()
        self.assertEqual(view["ledger_version"], 2)
        self.assertEqual(view["ledger_sha256"], hashlib.sha256(self.ledger_path(2).read_bytes()).hexdigest())
        self.assertIs(view["read_only"], True)
        self.assertEqual(view["authoritative_source"], "ledger")

    def test_field_slice_readiness_and_execution_status(self):
        slices = {s["slice_id"]: s for s in self.generate()["slices"]}
        self.assertEqual((slices["A"]["readiness"], slices["A"]["status"]), ("READY", "DONE"))
        self.assertEqual((slices["B"]["readiness"], slices["B"]["status"]), ("PROCEED_WITH_ASSUMPTIONS", "DONE"))
        self.assertTrue(slices["A"]["pinned_to_older_ledger"])

    def test_field_qa_results(self):
        qa = self.generate()["qa_results"]
        self.assertEqual([(r["retest_id"], r["slice_id"], r["result"], r["ledger_version"]) for r in qa],
                         [("T0001", "A", "pass", 1)])
        self.assertTrue(qa[0]["stale"], "a v1 retest is stale against ledger v2")

    def test_field_audit_findings(self):
        findings = {f["ledger_id"]: f for f in self.generate()["audit_findings"]}
        self.assertEqual((findings["AC1"]["verdict"], findings["AC1"]["kind"]), ("gap", "implementation"))
        self.assertEqual(findings["AC1"]["finding"], "AC1 edge case missing.")
        self.assertEqual(findings["AC2"]["verdict"], "pass")

    def test_field_unconfirmed_default_budget_usage(self):
        self.assertEqual(self.generate()["default_budget"], {"limit": 3, "used": 1, "remaining": 2, "exceeded": False})

    def test_every_section_four_field_is_a_view_key(self):
        view = self.generate()
        for key in ("goal", "confirmed_requirements", "provisional_assumptions", "open_questions",
                    "decision_history", "ledger_version", "slices", "qa_results", "audit_findings",
                    "default_budget"):
            self.assertIn(key, view)
        self.assertEqual(set(view), ov.VIEW_FIELDS)

    # --- ledger version and stale marker -------------------------------------

    def test_fresh_view_is_not_stale(self):
        self.generate()
        code, out = run(ov, "status", "--project", self.project)
        self.assertEqual(code, 0)
        self.assertFalse(out["stale"])
        self.assertEqual((out["view_ledger_version"], out["latest_ledger_version"]), (2, 2))

    def test_newer_ledger_marks_the_view_stale_without_editing_it(self):
        self.generate()
        before = (self.project / "owner-view.json").read_bytes()
        self.write_ledger_v2(number=3, extra=[("D2", "Decision", "Add a footer.", "active")])
        code, out = run(ov, "status", "--project", self.project)
        self.assertEqual(code, 0)
        self.assertTrue(out["stale"])
        self.assertEqual((out["view_ledger_version"], out["latest_ledger_version"]), (2, 3))
        self.assertEqual((self.project / "owner-view.json").read_bytes(), before)

    def test_changed_ledger_bytes_mark_the_view_stale(self):
        self.generate()
        path = self.ledger_path(2)
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertTrue(run(ov, "status", "--project", self.project)[1]["stale"])

    def test_a_project_that_fails_validation_yields_no_view(self):
        self.ledger_path(2).write_text("{not json", encoding="utf-8")
        code, out = run(ov, "generate", "--project", self.project)
        self.assertEqual(code, 1)
        self.assertFalse((self.project / "owner-view.json").exists())

    # --- the view never writes authoritative state ---------------------------

    def test_generate_adds_only_the_view_file(self):
        before = tree(self.project)
        self.generate()
        after = tree(self.project)
        self.assertEqual({k: v for k, v in after.items() if k != "owner-view.json"}, before)
        self.assertEqual(set(after) - set(before), {"owner-view.json"})

    def test_rejected_write_paths(self):
        before = tree(self.project)
        targets = [self.ledger_path(3), self.ledger_path(2), self.project / "plan.json",
                   self.project / "evidence" / "E0002.json", self.project / "retest" / "T0002.json",
                   self.project / "audit" / "A0002.json", self.project / "sources" / "S0002.json",
                   self.project / "questions" / "Q2.json", self.project / "project.json",
                   self.project / "elsewhere.json", self.project / "ledger" / ".." / "plan.json"]
        for target in targets:
            code, out = run(ov, "generate", "--project", self.project, "--output", target)
            self.assertEqual(code, 1, str(target))
            self.assertEqual({e["code"] for e in out["errors"]}, {"write_refused"}, str(target))
        self.assertEqual(tree(self.project), before)

    def test_will_not_replace_a_file_that_is_not_an_owner_view(self):
        other = self.tmp / "notes.json"
        other.write_text('{"keep": true}', encoding="utf-8")
        code, out = run(ov, "generate", "--project", self.project, "--output", other)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(other.read_text(encoding="utf-8")), {"keep": True})
        code, _ = run(ov, "generate", "--project", self.project, "--output", self.tmp / "notes.txt")
        self.assertEqual(code, 1)

    def test_a_path_outside_the_project_and_a_regeneration_are_allowed(self):
        target = self.tmp / "shared" / "view.json"
        self.assertEqual(run(ov, "generate", "--project", self.project, "--output", target)[0], 0)
        self.assertEqual(run(ov, "generate", "--project", self.project, "--output", target)[0], 0)

    def test_the_module_has_no_decision_or_ledger_write_interface(self):
        source = (SCRIPTS / "owner_view.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"project_state\.(bootstrap|source_add|init|retest_record|audit_record)\b")
        self.assertNotRegex(source, r"\bapprove\b|\banswer\b\s*=|record_decision")
        parser_text = ov.__doc__
        self.assertIn("never", parser_text)
        with self.assertRaises(SystemExit):
            run(ov, "decide", "--project", self.project)

    # --- pending question wording and default are preserved exactly ----------

    def test_pending_question_wording_and_default_are_exact(self):
        view = self.generate()
        question = view["open_questions"][0]
        ledger_entry = next(e for e in json.loads(self.ledger_path(2).read_text(encoding="utf-8"))["entries"]
                            if e["id"] == "Q1")
        self.assertEqual(question["wording"], WORDING)
        self.assertEqual(question["wording"], ledger_entry["content"])
        self.assertEqual(question["default"], DEFAULT)
        self.assertTrue(question["default_stored"])
        self.assertTrue(question["packet_wording_matches"])
        raw = (self.project / "owner-view.json").read_text(encoding="utf-8")
        self.assertEqual(json.loads(raw)["open_questions"][0]["wording"].encode("utf-8"), WORDING.encode("utf-8"))

    def test_a_question_without_a_stored_default_says_so(self):
        (self.project / "questions" / "Q1.json").unlink()
        question = self.generate()["open_questions"][0]
        self.assertEqual(question["wording"], WORDING)
        self.assertIsNone(question["default"])
        self.assertFalse(question["default_stored"])

    def test_a_packet_that_words_the_question_differently_is_flagged_not_substituted(self):
        path = self.project / "questions" / "Q1.json"
        packet = json.loads(path.read_text(encoding="utf-8"))
        packet["text"] = "A different wording"
        path.write_text(json.dumps(packet), encoding="utf-8")
        question = self.generate()["open_questions"][0]
        self.assertEqual(question["wording"], WORDING)
        self.assertFalse(question["packet_wording_matches"])

    # --- the dashboard reads the generated file only -------------------------

    def embedded(self):
        dash.publish_run(self.root, "task-1")
        page = (self.root / ".councilflow" / "runs" / "task-1" / "dashboard.html").read_text(encoding="utf-8")
        match = re.search(r'<script id="councilflow-run-data" type="application/json">(.*?)</script>', page, re.S)
        return json.loads(match.group(1))

    def test_dashboard_embeds_the_generated_view_with_exact_wording(self):
        self.generate()
        owner = self.embedded()["ownerView"]
        self.assertEqual(owner["view"]["open_questions"][0]["wording"], WORDING)
        self.assertEqual(owner["view"]["open_questions"][0]["default"], DEFAULT)
        self.assertEqual(owner["view"]["ledger_version"], 2)
        self.assertFalse(owner["freshness"]["stale"])

    def test_dashboard_shows_the_stale_marker(self):
        self.generate()
        self.write_ledger_v2(number=3, extra=[("D2", "Decision", "Add a footer.", "active")])
        owner = self.embedded()["ownerView"]
        self.assertTrue(owner["freshness"]["stale"])
        self.assertEqual(owner["freshness"]["latest_ledger_version"], 3)

    def test_dashboard_without_a_view_embeds_none_and_does_not_generate_one(self):
        self.assertIsNone(self.embedded()["ownerView"])
        self.assertFalse((self.project / "owner-view.json").exists())

    def test_dashboard_reports_an_unreadable_view_instead_of_reading_the_ledger(self):
        (self.project / "owner-view.json").write_text('{"schema": "other"}', encoding="utf-8")
        owner = self.embedded()["ownerView"]
        self.assertIsNone(owner["view"])
        self.assertIn("owner-view.json", owner["error"])

    def test_dashboard_publisher_never_loads_project_state(self):
        source = (SCRIPTS / "dashboard.py").read_text(encoding="utf-8")
        self.assertNotIn("project_state", source)
        self.assertNotIn("planner_contract", source)

    def test_bundle_and_styles_carry_the_owner_view(self):
        bundle = (ROOT / ".agents/skills/council-flow/dashboard/app.js").read_text(encoding="utf-8")
        self.assertIn("Out of date:", bundle)
        self.assertIn("Owner view", bundle)
        source = (ROOT / "demo/dashboard/app/src/views/OwnerView.jsx").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"fetch\(|XMLHttpRequest|WebSocket|<button|<input")


if __name__ == "__main__":
    unittest.main()
