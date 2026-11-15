import tempfile
import unittest
from pathlib import Path
from claude_adapter import parse_stream, process

FIXTURE=Path(__file__).parent/"fixtures"/"claude-stream-sanitized.jsonl"

class ClaudeAdapterTests(unittest.TestCase):
    def test_fixture_distinguishes_harness_gateway_model_and_route(self):
        with tempfile.TemporaryDirectory() as d:
            result=process(FIXTURE.read_bytes(),artifact_dir=d,run_id="claude-fixture",gateway="xkiro",upstream_model="fixture-upstream-a")
            item=result["record"]
            self.assertEqual((item["harness"],item["gateway"],item["upstream_model"]),("claude-code","xkiro","fixture-upstream-a"))
            self.assertEqual(item["route"],"claude-code/xkiro/stream-json")
            self.assertEqual(item["usage"]["cached_input"],12)
            self.assertIsNone(item["usage"]["reported_cost"])
            self.assertEqual(result["digest"]["streams"]["stdout"]["bytes"],FIXTURE.stat().st_size)

    def test_missing_cache_prices_and_usage_remain_unknown(self):
        result=parse_stream(b'{"type":"result","subtype":"success"}',run_id="no-usage")
        item=result["record"]
        self.assertIsNone(item["usage"]["cache_creation"])
        self.assertIsNone(item["usage"]["reported_cost"])
        self.assertFalse(item["usage"]["availability"]["cached_input"]=="")

    def test_retry_only_from_gateway_metadata_and_model_change_stays_unknown(self):
        data=(b'{"type":"assistant","model":"m1","gateway":{"retry_count":2},"usage":{"input_tokens":1}}\n'
              b'{"type":"result","model":"m2","usage":{"input_tokens":1}}')
        item=parse_stream(data,run_id="changed")["record"]
        self.assertIsNone(item["upstream_model"])
        self.assertTrue(any("model changed" in n for n in item["notes"]))
        self.assertTrue(any("retry_count=2" in n for n in item["notes"]))

    def test_partial_malformed_and_unknown_events_flag_incomplete(self):
        result=parse_stream(b'{bad}\n{"type":"assistant","message":{}}\n{"type":"future"}',run_id="partial")
        self.assertFalse(result["complete"])
        self.assertEqual(len(result["unsupported_or_malformed"]),2)
        self.assertIsNone(result["record"]["usage"]["input"])

if __name__=="__main__": unittest.main()
