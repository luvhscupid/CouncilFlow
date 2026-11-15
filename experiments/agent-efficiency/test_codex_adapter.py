import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from codex_adapter import parse_stream, process
from recorder import validate
from digest import expand_bytes
import codex_adapter

FIXTURES=Path(__file__).parent/"fixtures"

class CodexAdapterTests(unittest.TestCase):
    def test_fixture_usage_provenance_and_digest(self):
        raw=(FIXTURES/"codex-exec-sanitized.jsonl").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            result=process(raw,artifact_dir=d,run_id="codex-fixture",repository_revision="abc123",elapsed_ms=99,source="synthetic-fixture")
            item=result["record"]; validate(item)
            self.assertEqual(item["usage"]["input"],120)
            self.assertEqual(item["usage"]["cached_input"],30)
            self.assertIsNone(item["usage"]["reported_cost"])
            self.assertEqual(item["acceptance"]["status"],"unknown")
            self.assertEqual(result["source"]["input_sha256"],hashlib.sha256(raw).hexdigest())
            self.assertNotIn(b"sanitized synthetic fixture",expand_bytes(result["digest"],"stdout"))
            self.assertEqual(item["usage_scope"],"turn")
            self.assertIsNone(item["upstream_model"])
            self.assertIsNone(result["process_exit_code"])
            self.assertIsNone(result["digest"]["exit_code"])
            self.assertEqual(item["source_kind"],"codex-exec-jsonl-synthetic-fixture")

    def test_partial_interrupted_and_missing_usage(self):
        item=parse_stream(b'{"type":"thread.started","thread_id":"t"}\n{"type":"turn.started"}\n',run_id="partial")["record"]
        self.assertIsNone(item["usage"]["input"])
        self.assertIn("no completed",item["notes"][0])

    def test_malformed_and_unsupported_events_are_explicit(self):
        result=parse_stream(b'{oops}\n{"type":"future.event"}\n{"type":"turn.started"}\n{"type":"turn.completed","usage":{}}',run_id="bad")
        self.assertEqual(len(result["unsupported_or_malformed"]),2)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["record"]["usage"]["output"])

    def test_rejects_fabricated_negative_or_boolean_count(self):
        result=parse_stream(b'{"type":"turn.completed","usage":{"input_tokens":true,"output_tokens":-2}}',run_id="invalid")
        self.assertIsNone(result["record"]["usage"]["input"])
        self.assertIsNone(result["record"]["usage"]["output"])

class CodexC1Tests(unittest.TestCase):
    def events(self, *events):
        return b''.join((json.dumps(e)+'\n').encode() for e in events)

    def completed(self, **usage):
        return self.events({'type':'thread.started','thread_id':'synthetic-id'},
                           {'type':'turn.started'}, {'type':'turn.completed','usage':usage})

    def test_documented_item_updates_and_error_events(self):
        raw=self.events({'type':'turn.started'}, {'type':'item.updated','item':{'type':'reasoning','text':'PRIVATE'}},
                        {'type':'turn.failed','error':{'message':'PRIVATE'}}, {'type':'error','message':'PRIVATE'})
        result=parse_stream(raw)
        self.assertEqual(result['completion_status'],'failed')
        self.assertFalse(result['complete'])
        self.assertEqual(result['unsupported_or_malformed'],[])
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_latest_turn_separate_from_prior_turn_and_item_deltas(self):
        raw=self.events({'type':'thread.started','thread_id':'synthetic-id'}, {'type':'turn.started'},
                        {'type':'item.updated','usage':{'input_tokens':99999}},
                        {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':3}},
                        {'type':'turn.started'}, {'type':'turn.completed','usage':{'input_tokens':20,'output_tokens':4}})
        result=parse_stream(raw)
        self.assertTrue(result['complete'])
        self.assertEqual(result['record']['usage']['input'],20)
        self.assertEqual([t['usage']['input'] for t in result['turn_usage']],[10,20])
        self.assertEqual(result['record']['usage_scope'],'turn')
        self.assertIsNone(result['session_usage'])

    def test_cumulative_incremental_wrappers_are_unknown_not_summed(self):
        raw=self.completed(total_token_usage={'input_tokens':100},last_token_usage={'input_tokens':20})
        result=parse_stream(raw)
        self.assertIsNone(result['record']['usage']['input'])
        self.assertEqual(result['record']['usage_scope'],'unknown')
        self.assertFalse(result['complete'])

    def test_duplicate_terminal_is_not_double_counted(self):
        raw=self.completed(input_tokens=10)+self.events({'type':'turn.completed','usage':{'input_tokens':10}})
        result=parse_stream(raw)
        self.assertEqual(result['completed_turns'],1)
        self.assertFalse(result['complete'])
        self.assertEqual(len(result['turn_usage']),1)

    def test_final_started_or_failed_turn_does_not_reuse_previous_usage(self):
        for tail in ([{'type':'turn.started'}], [{'type':'turn.started'},{'type':'turn.failed','error':{'message':'private'}}]):
            with self.subTest(tail=tail):
                result=parse_stream(self.completed(input_tokens=10)+self.events(*tail))
                self.assertFalse(result['complete'])
                self.assertIsNone(result['record']['usage']['input'])

    def test_failed_cancelled_and_nonzero_process_status_are_explicit(self):
        raw=self.completed(input_tokens=2)
        self.assertEqual(parse_stream(raw,process_exit_code=1)['completion_status'],'failed')
        self.assertEqual(parse_stream(raw,process_exit_code=130,cancelled=True)['completion_status'],'cancelled')
        self.assertEqual(parse_stream(raw,process_exit_code=0)['process_exit_code'],0)
        self.assertIsNone(parse_stream(raw)['process_exit_code'])
        self.assertEqual(parse_stream(b'',cancelled=True)['completion_status'],'cancelled')
        with tempfile.TemporaryDirectory() as d:
            result=process(raw,artifact_dir=d,process_exit_code=1)
            self.assertFalse(result['complete'])
            self.assertIn('COMMAND_FAILED',result['digest']['flags'])
            self.assertIn('DIGEST_INCOMPLETE',result['digest']['flags'])

    def test_invalid_utf8_unknown_versions_and_nonobjects_are_safe(self):
        for raw in (b'\xff\n',b'[]\n',b'{"type":[]}\n',b'{"type":"future.event","text":"PRIVATE"}\n',
                    b'{"type":"turn.completed","schema_version":"future","usage":{"input_tokens":2}}\n',
                    b'{"type":"turn.completed","usage":{"input_tokens":NaN}}\n'):
            with self.subTest(raw=raw):
                result=parse_stream(raw)
                self.assertFalse(result['complete'])
                self.assertTrue(result['unsupported_or_malformed'])
                self.assertNotIn('PRIVATE',json.dumps(result))

    def test_missing_model_usage_and_billing_stay_unknown(self):
        result=parse_stream(self.completed())
        item=result['record']
        self.assertIsNone(item['upstream_model'])
        self.assertTrue(all(item['usage'][k] is None for k in ('input','output','cached_input','cache_creation','reported_cost')))
        self.assertIsNone(result['source']['effective_provider_route'])
        validate(item)

    def test_optional_reported_cache_write_and_reasoning_are_not_added(self):
        result=parse_stream(self.completed(input_tokens=20,cached_input_tokens=5,cache_write_input_tokens=3,
                                          output_tokens=7,reasoning_output_tokens=2))
        item=result['record']
        self.assertEqual(item['usage']['cache_creation'],3)
        self.assertEqual(item['usage']['input'],20)
        self.assertEqual(item['usage']['output'],7)
        self.assertEqual(result['turn_usage'][0]['reasoning_output_tokens'],2)

    def test_multiple_threads_and_models_are_not_silently_combined(self):
        raw=self.completed(input_tokens=10)+self.events({'type':'thread.started','thread_id':'second'},
                {'type':'turn.started'},{'type':'turn.completed','model':'fixture-a','usage':{'input_tokens':20}},
                {'type':'turn.started'},{'type':'turn.completed','model':'fixture-b','usage':{'input_tokens':30}})
        result=parse_stream(raw)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['record']['usage']['input'])
        self.assertIsNone(result['record']['upstream_model'])
        self.assertEqual(result['turn_usage'],[])

    def test_model_identity_is_observed_not_defaulted_or_echoed_unsafely(self):
        for model,expected in (('fixture-model','fixture-model'),('sk-secret-fixture',None),({'bad':'object'},None)):
            with self.subTest(model=model):
                raw=self.events({'type':'turn.started'},{'type':'turn.completed','model':model,'usage':{}})
                result=parse_stream(raw)
                self.assertEqual(result['record']['upstream_model'],expected)
                self.assertNotIn('sk-secret',json.dumps(result))

    def test_no_raw_payload_reasoning_error_or_tool_output_is_stored(self):
        marker='PRIVATE_REASONING_API_KEY_FIXTURE'
        raw=self.events({'type':'thread.started','thread_id':marker},{'type':'turn.started'},
                        {'type':'item.completed','item':{'type':'reasoning','text':marker}},
                        {'type':'item.updated','item':{'type':'command_execution','command':marker,'aggregated_output':marker}},
                        {'type':'item.completed','item':{'type':'agent_message','text':marker}},
                        {'type':'turn.failed','error':{'message':marker}})
        with tempfile.TemporaryDirectory() as d:
            result=process(raw,artifact_dir=d)
            self.assertNotIn(marker,json.dumps(result))
            for path in Path(d).iterdir(): self.assertNotIn(marker.encode(),path.read_bytes())
            self.assertEqual(result['source']['input_sha256'],hashlib.sha256(raw).hexdigest())

    def test_windows_space_paths_cli_file_and_stdin_and_record_compatibility(self):
        raw=self.completed(input_tokens=12,output_tokens=3)
        with tempfile.TemporaryDirectory(prefix='c1 windows space ') as d:
            root=Path(d); events=root/'events with spaces.jsonl'; events.write_bytes(raw)
            records=root/'records.jsonl'
            for index,from_stdin in enumerate((False,True)):
                args=[sys.executable,codex_adapter.__file__]
                if not from_stdin: args.append(str(events))
                args.extend(['--artifacts',str(root/f'artifacts {index}'),'--records',str(records),
                             '--source','synthetic-fixture','--cli-version','0.169.0-alpha.11.1','--process-exit-code','0'])
                proc=subprocess.run(args,input=raw if from_stdin else None,capture_output=True)
                self.assertEqual(proc.returncode,0,proc.stderr)
                result=json.loads(proc.stdout)
                self.assertEqual(result['source']['cli_version'],'0.169.0-alpha.11.1')
                self.assertEqual(result['record']['usage']['input'],12)
            for line in records.read_text().splitlines(): validate(json.loads(line))

    def test_parse_failure_cli_returns_two_and_does_not_leak_error_content(self):
        with tempfile.TemporaryDirectory() as d:
            proc=subprocess.run([sys.executable,codex_adapter.__file__,'--artifacts',d],
                                input=b'{bad PRIVATE_SECRET}\n',capture_output=True)
            self.assertEqual(proc.returncode,2,proc.stderr)
            self.assertNotIn(b'PRIVATE_SECRET',proc.stdout)

    def test_parser_never_spawns_codex_or_mutates_environment(self):
        from unittest.mock import patch
        import os
        before=dict(os.environ)
        with tempfile.TemporaryDirectory() as d, patch('subprocess.Popen',side_effect=AssertionError('unexpected process')):
            process(self.completed(input_tokens=1),artifact_dir=d)
        self.assertEqual(dict(os.environ),before)

    def test_sanitized_digest_is_valid_json_with_no_invented_process_identity(self):
        with tempfile.TemporaryDirectory() as d:
            result=process(self.completed(input_tokens=2),artifact_dir=d,process_exit_code=0)
            self.assertEqual(result['digest']['command'],[])
            self.assertEqual(result['digest']['exit_code'],0)
            self.assertEqual(result['digest']['streams']['stdout']['parse_errors'],[])
            self.assertEqual(len(json.loads(expand_bytes(result['digest'],'stdout'))['events']),3)

    def test_duplicate_fields_and_invalid_usage_objects_are_incomplete(self):
        for raw in (b'{"type":"turn.started","type":"turn.completed"}\n',
                    self.events({'type':'turn.started'},{'type':'turn.completed','usage':[]})):
            with self.subTest(raw=raw):
                result=parse_stream(raw)
                self.assertFalse(result['complete'])
                self.assertTrue(result['unsupported_or_malformed'])


if __name__ == '__main__': unittest.main()
