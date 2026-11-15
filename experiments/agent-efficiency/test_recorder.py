import json
import unittest
from pathlib import Path
from recorder import record, validate, parse_codex_event, parse_claude_json, append_jsonl

class RecorderTests(unittest.TestCase):
    def test_unknown_claude_gateway_route_is_explicit_and_narrow(self):
        item=record(run_id="unknown",harness="claude-code",route="claude-code/unknown/stream-json")
        validate(item)
        self.assertIsNone(item["gateway"])
        with self.assertRaises(ValueError): validate({**item,"gateway":"xkiro"})
        with self.assertRaises(ValueError): validate({**item,"route":"claude-code/unapproved/stream-json"})

    def test_codex_partial_and_unknown_are_null(self):
        item=parse_codex_event({"type":"task_complete","model":"fixture-model","usage":{"input_tokens":12,"output_tokens":3}},run_id="fixture-codex")
        validate(item)
        self.assertEqual(item["usage"]["input"],12)
        self.assertIsNone(item["usage"]["cached_input"])
        self.assertIn("not reported",item["usage"]["availability"]["cached_input"])
        with self.assertRaises(ValueError): parse_codex_event({"type":"future_event"},run_id="x")

    def test_claude_xkiro_identity_and_cost_not_inferred(self):
        item=parse_claude_json({"usage":{"input_tokens":20,"cache_read_input_tokens":4,"output_tokens":7}},run_id="fixture-claude",upstream_model="fixture-upstream")
        validate(item)
        self.assertEqual(item["route"],"claude-code/xkiro/fixture-upstream")
        self.assertIsNone(item["usage"]["reported_cost"])

    def test_acceptance_requires_external_provenance(self):
        base=record(run_id="a",harness="unknown",route="unknown",acceptance={"status":"accepted","evidence_ref":None,"provenance":"unverified"})
        with self.assertRaises(ValueError): validate(base)
        base["acceptance"]={"status":"accepted","evidence_ref":"test-report#1","provenance":"external-check"}
        validate(base)

    def test_malformed_and_jsonl(self):
        base=record(run_id="fixture",harness="unknown",route="unknown")
        with self.assertRaises(ValueError): validate({**base,"unexpected":1})
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"runs.jsonl"; append_jsonl(path,base)
            self.assertEqual(json.loads(path.read_text().strip()),base)

if __name__ == "__main__": unittest.main()
