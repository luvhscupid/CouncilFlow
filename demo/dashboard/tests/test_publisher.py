import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PUBLISHER = ROOT / ".agents" / "skills" / "council-flow" / "scripts" / "dashboard.py"
SPEC = importlib.util.spec_from_file_location("councilflow_dashboard", PUBLISHER)
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


def write_packet_run(root, task_id, objective="Show this run"):
    run = root / ".councilflow" / "runs" / task_id
    messages = run / "messages"
    messages.mkdir(parents=True)
    plan = {
        "protocol": "council-flow",
        "plan_id": f"plan-{task_id}",
        "plan_revision": 1,
        "task_id": task_id,
        "attempt_id": "attempt-01",
        "objective": objective,
        "acceptance": [{"id": "LIVE-TEST-01", "text": "Use its own run data."}],
    }
    plan_bytes = (json.dumps(plan, separators=(",", ":")) + "\n").encode("utf-8")
    (run / "plan.json").write_bytes(plan_bytes)
    publication = {
        "protocol": "council-flow",
        "version": "1.0",
        "message_id": f"publish-{task_id}",
        "message_type": "plan.publish",
        "plan_id": plan["plan_id"],
        "plan_revision": 1,
        "task_id": task_id,
        "attempt_id": "attempt-01",
        "sender": {"role": "planner", "instance_id": "/root/planner"},
        "recipient": {"role": "manager", "instance_id": "/root"},
        "in_reply_to": None,
        "payload": {
            "objective": plan["objective"],
            "scope": ["Read packet records"],
            "acceptance_ids": ["LIVE-TEST-01"],
            "plan_ref": {
                "artifact_id": f"plan-artifact-{task_id}",
                "path": f".councilflow/runs/{task_id}/plan.json",
                "sha256": hashlib.sha256(plan_bytes).hexdigest(),
                "kind": "plan",
            },
        },
        "evidence_refs": [],
    }
    (messages / "plan-publish.json").write_text(json.dumps(publication) + "\n", encoding="utf-8")
    return run


class DashboardPublisherTests(unittest.TestCase):
    def test_stale_artifact_hash_does_not_hide_the_missing_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = write_packet_run(root, "task-stale")
            messages = run / "messages"
            publication = json.loads((messages / "plan-publish.json").read_bytes())
            assignment = {**publication, "message_type": "job.assign", "message_id": "assign-stale",
                          "sender": publication["recipient"], "recipient": {"role": "worker", "instance_id": "worker"},
                          "in_reply_to": publication["message_id"],
                          "payload": {"objective": "Review inputs", "scope": ["Read files"],
                                      "acceptance_ids": ["LIVE-TEST-01"], "instructions": ["Check the input"]}}
            stale = {**assignment, "evidence_refs": [{**publication["payload"]["plan_ref"], "sha256": "0" * 64}]}
            child = {**assignment, "message_id": "unlinked-child", "in_reply_to": "assign-stale"}
            (messages / "stale.json").write_text(json.dumps(stale), encoding="utf-8")
            (messages / "child.json").write_text(json.dumps(child), encoding="utf-8")

            issues = " ".join(dashboard.publish_run(root, "task-stale")["issues"])

            self.assertIn("stale.json: artifact_hash at evidence_refs", issues)
            self.assertIn("child.json", issues)
            self.assertIn("assign-stale", issues)
            self.assertNotIn("unknown_field at $: data,path", issues)

    def test_unknown_packet_field_names_the_file_and_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = write_packet_run(root, "task-field")
            packet = run / "messages" / "plan-publish.json"
            data = json.loads(packet.read_bytes())
            data["unexpected"] = True
            packet.write_text(json.dumps(data), encoding="utf-8")

            issues = " ".join(dashboard.publish_run(root, "task-field")["issues"])

            self.assertIn("plan-publish.json: unknown_field at $: unexpected", issues)

    def test_publisher_embeds_valid_task_and_opens_its_snapshot_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-one")
            opened = []

            result = dashboard.publish_run(root, "task-one", open_browser=True,
                                           opener=lambda url: opened.append(url) or True)

            page = Path(result["snapshot_path"]).read_text(encoding="utf-8")
            self.assertTrue(result["opened"])
            self.assertEqual(len(opened), 1)
            self.assertTrue(opened[0].startswith("file:///"))
            self.assertNotIn('http-equiv="refresh" content="2"', page)
            self.assertIn('id="councilflow-run-data"', page)
            self.assertIn('"task_id":"task-one"', page)
            self.assertIn("function buildSnapshot", page)
            self.assertIn('id="councilflow-root"', page)
            self.assertIn("CouncilFlow dashboard bundle", page)

    def test_project_board_follows_the_latest_run_and_links_the_others(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "my-project"
            root.mkdir()
            write_packet_run(root, "task-one")
            write_packet_run(root, "task-two")
            write_packet_run(root, "never-published")
            opened = []

            dashboard.publish_run(root, "task-one")
            result = dashboard.publish_run(root, "task-two", open_browser=True,
                                           opener=lambda url: opened.append(url) or True)

            project = root / ".councilflow" / "dashboard.html"
            self.assertEqual(Path(result["project_path"]), project.resolve())
            self.assertTrue(opened[0].endswith("/my-project/.councilflow/dashboard.html"))
            page = project.read_text(encoding="utf-8")
            self.assertIn('"task_id":"task-two"', page)
            self.assertNotIn('"task_id":"task-one"', page)
            self.assertIn('"board":"project"', page)
            self.assertIn('"project":"my-project"', page)
            self.assertIn('"href":"runs/task-one/dashboard.html"', page)
            self.assertIn('"href":"runs/task-two/dashboard.html"', page)
            self.assertNotIn("never-published", page)
            task_page = Path(result["snapshot_path"]).read_text(encoding="utf-8")
            self.assertIn('"board":"task"', task_page)
            self.assertIn('"href":"../task-one/dashboard.html"', task_page)

    def test_version_1_1_reopen_packet_is_not_reported_as_broken(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = write_packet_run(root, "task-v11")
            evidence = run / "evidence.txt"
            evidence.write_bytes(b"observation")
            ref = {"artifact_id": "E1", "path": ".councilflow/runs/task-v11/evidence.txt",
                   "sha256": hashlib.sha256(b"observation").hexdigest(), "kind": "evidence"}
            publication = json.loads((run / "messages" / "plan-publish.json").read_text(encoding="utf-8"))
            reopen = {**publication, "version": "1.1", "message_id": "reopen-1", "message_type": "evidence.reopen",
                      "sender": {"role": "worker", "instance_id": "/root/worker"},
                      "recipient": {"role": "manager", "instance_id": "/root"}, "in_reply_to": publication["message_id"],
                      "payload": {"evidence_id": "E0001", "ledger_ids": ["R1"], "affected_slices": ["S1"],
                                  "contradiction": "x", "consequence": "y", "evidence_ref": ref},
                      "evidence_refs": [ref]}
            (run / "messages" / "reopen.json").write_text(json.dumps(reopen) + "\n", encoding="utf-8")

            result = dashboard.publish_run(root, "task-v11")

            page = Path(result["snapshot_path"]).read_text(encoding="utf-8")
            self.assertIn("reopen-1", page)
            self.assertNotIn("sequence:", page)

    def test_malformed_message_is_embedded_as_a_visible_issue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = write_packet_run(root, "task-broken")
            (run / "messages" / "malformed.json").write_text("{nope", encoding="utf-8")

            result = dashboard.publish_run(root, "task-broken")

            page = Path(result["snapshot_path"]).read_text(encoding="utf-8")
            self.assertIn("malformed.json", page)
            self.assertIn("could not read valid JSON", page)

    def test_each_task_writes_a_distinct_snapshot_and_keeps_manual_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-one")
            write_packet_run(root, "task-two")

            one = dashboard.publish_run(root, "task-one")
            two = dashboard.publish_run(root, "task-two")

            self.assertNotEqual(one["snapshot_path"], two["snapshot_path"])
            first = Path(one["snapshot_path"]).read_text(encoding="utf-8")
            second = Path(two["snapshot_path"]).read_text(encoding="utf-8")
            self.assertIn('"task_id":"task-one"', first)
            self.assertNotIn('"task_id":"task-two"', first)
            self.assertIn('"task_id":"task-two"', second)
            self.assertIn("Open run folder", second)
            self.assertIn("Choose message files", second)
            self.assertIn("Project list", second)
            self.assertIn(f'"project":{json.dumps(root.resolve().name)}', second)

    def test_republishing_replaces_the_same_task_page_with_new_packets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = write_packet_run(root, "task-updates")
            first = dashboard.publish_run(root, "task-updates")
            assignment = {
                "protocol": "council-flow", "version": "1.0", "message_id": "assign-task-updates",
                "message_type": "job.assign", "plan_id": "plan-task-updates", "plan_revision": 1,
                "task_id": "task-updates", "attempt_id": "attempt-01",
                "sender": {"role": "manager", "instance_id": "/root"},
                "recipient": {"role": "worker", "instance_id": "/root/worker"},
                "in_reply_to": "publish-task-updates",
                "payload": {
                    "objective": "Implement the accepted task", "scope": ["Dashboard"],
                    "acceptance_ids": ["LIVE-TEST-01"], "instructions": ["Keep packet files authoritative."],
                },
                "evidence_refs": [],
            }
            (run / "messages" / "worker-assign.json").write_text(json.dumps(assignment) + "\n", encoding="utf-8")

            second = dashboard.publish_run(root, "task-updates")

            self.assertEqual(first["snapshot_path"], second["snapshot_path"])
            self.assertEqual(second["packet_count"], 2)
            page = Path(second["snapshot_path"]).read_text(encoding="utf-8")
            self.assertIn('"message_id":"assign-task-updates"', page)
            self.assertNotIn('<script src="', page)
            self.assertNotIn('<link rel="stylesheet"', page)

    def test_invalid_task_id_cannot_escape_the_runs_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                dashboard.publish_run(Path(temporary), "../other-task")

    def test_packet_text_cannot_break_out_of_embedded_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-html", "</script><script>alert(1)</script>")

            result = dashboard.publish_run(root, "task-html")

            page = Path(result["snapshot_path"]).read_text(encoding="utf-8")
            self.assertNotIn("</script><script>alert(1)", page)
            self.assertIn("\\u003c/script\\u003e\\u003cscript\\u003e", page)

    def test_refused_run_directory_is_not_created_on_disk(self):
        # A path whose containment check fails must not leave a directory behind.
        # Here the runs folder is itself a junction to a folder outside the root,
        # so the new task directory would land outside the repository.
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            outside = Path(temporary) / "outside"
            (root / ".councilflow").mkdir(parents=True)
            outside.mkdir()
            runs = root / ".councilflow" / "runs"
            if os.name == "nt":
                made = subprocess.run(["cmd", "/c", "mklink", "/J", str(runs), str(outside)], capture_output=True, text=True)
                if made.returncode != 0:
                    self.skipTest(f"cannot create a directory junction: {made.stderr.strip()}")
            else:
                os.symlink(outside, runs, target_is_directory=True)
            with self.assertRaises(ValueError):
                dashboard.publish_run(root, "escaped-task")
            self.assertFalse((outside / "escaped-task").exists())



def embedded(page):
    start = page.index('<script id="councilflow-run-data" type="application/json">') + len(
        '<script id="councilflow-run-data" type="application/json">')
    return json.loads(page[start:page.index("</script>", start)])


class DashboardContextTests(unittest.TestCase):
    def test_snapshot_carries_file_times_policy_and_no_invented_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-context")
            result = dashboard.publish_run(root, "task-context")
            data = embedded(Path(result["snapshot_path"]).read_text(encoding="utf-8"))
            self.assertEqual(data["taskId"], "task-context")
            self.assertTrue(data["generatedAt"].endswith("+00:00"))
            self.assertIsNone(data["efficiency"])
            self.assertEqual(data["policy"]["order"][0], "owner")
            self.assertIn("worker", data["policy"]["roles"])
            for entry in data["files"]:
                self.assertRegex(entry["modified"], r"^\d{4}-\d{2}-\d{2}T")

    def test_efficiency_records_are_validated_and_filtered_to_the_task(self):
        recorder_path = PUBLISHER.parent / "efficiency" / "recorder.py"
        spec = importlib.util.spec_from_file_location("recorder_for_test", recorder_path)
        recorder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recorder)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-usage")
            mine = recorder.record(run_id="task-usage", harness="codex", route="codex/native-or-configured",
                                   upstream_model="example-model", usage={"input": 1200, "output": 300})
            other = recorder.record(run_id="other-task", harness="unknown", route="manual")
            records = root / "records.jsonl"
            records.write_text("\n".join([json.dumps(mine), json.dumps(other), "{\"bad\": true}"]) + "\n",
                               encoding="utf-8")
            result = dashboard.publish_run(root, "task-usage", efficiency_records=records)
            efficiency = embedded(Path(result["snapshot_path"]).read_text(encoding="utf-8"))["efficiency"]
            self.assertEqual(efficiency["matched"], 1)
            self.assertEqual(efficiency["other_runs"], 1)
            self.assertEqual(efficiency["invalid"], 1)
            self.assertEqual(efficiency["records"][0]["upstream_model"], "example-model")

    def test_missing_efficiency_file_is_reported_not_fatal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_packet_run(root, "task-missing")
            result = dashboard.publish_run(root, "task-missing", efficiency_records=root / "absent.jsonl")
            efficiency = embedded(Path(result["snapshot_path"]).read_text(encoding="utf-8"))["efficiency"]
            self.assertEqual(efficiency["records"], [])
            self.assertIn("absent.jsonl", efficiency["error"])


if __name__ == "__main__":
    unittest.main()
