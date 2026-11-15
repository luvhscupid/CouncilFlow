import json
import tempfile
import unittest
from pathlib import Path
from codex_adapter import parse_stream, process
from recorder import validate

FIXTURES=Path(__file__).parent/"fixtures"

class CodexAdapterTests(unittest.TestCase):
    def test_fixture_usage_provenance_and_digest(self):
        raw=(FIXTURES/"codex-exec-sanitized.jsonl").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            result=process(raw,artifact_dir=d,run_id="codex-fixture",repository_revision="abc123",elapsed_ms=99)
            item=result["record"]; validate(item)
            self.assertEqual(item["usage"]["input"],120)
            self.assertEqual(item["usage"]["cached_input"],30)
            self.assertIsNone(item["usage"]["reported_cost"])
            self.assertEqual(item["acceptance"]["status"],"unknown")
            self.assertEqual(result["digest"]["streams"]["stdout"]["bytes"],len(raw))

    def test_partial_interrupted_and_missing_usage(self):
        item=parse_stream(b'{"type":"thread.started","thread_id":"t"}\n{"type":"turn.started"}\n',run_id="partial")["record"]
        self.assertIsNone(item["usage"]["input"])
        self.assertIn("no completed",item["notes"][0])

    def test_malformed_and_unsupported_events_are_explicit(self):
        result=parse_stream(b'{oops}\n{"type":"future.event"}\n{"type":"turn.completed","usage":{}}',run_id="bad")
        self.assertEqual(len(result["unsupported_or_malformed"]),2)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["record"]["usage"]["output"])

    def test_rejects_fabricated_negative_or_boolean_count(self):
        result=parse_stream(b'{"type":"turn.completed","usage":{"input_tokens":true,"output_tokens":-2}}',run_id="invalid")
        self.assertIsNone(result["record"]["usage"]["input"])
        self.assertIsNone(result["record"]["usage"]["output"])

if __name__=="__main__": unittest.main()
