import tempfile
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from claude_adapter import parse_stream, process
import claude_adapter
from recorder import record, validate
from digest import expand_bytes

FIXTURE=Path(__file__).parent/"fixtures"/"claude-stream-sanitized.jsonl"

class ClaudeAdapterTests(unittest.TestCase):
    def test_fixture_distinguishes_harness_gateway_model_and_route(self):
        with tempfile.TemporaryDirectory() as d:
            result=process(FIXTURE.read_bytes(),artifact_dir=d,run_id="claude-fixture",gateway="xkiro",upstream_model="fixture-upstream-a")
            item=result["record"]
            self.assertEqual((item["harness"],item["gateway"],item["upstream_model"]),("claude-code","xkiro",None))
            self.assertEqual(result["configured_model"],"fixture-upstream-a")
            self.assertEqual(result["reported_model"],"fixture-upstream-a")
            self.assertIsNone(result["effective_upstream_model"])
            self.assertEqual(item["route"],"claude-code/xkiro/stream-json")
            self.assertEqual(item["usage"]["cached_input"],12)
            self.assertIsNone(item["usage"]["reported_cost"])
            self.assertEqual(result["source"]["input_sha256"],hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
            self.assertEqual(result["digest"]["command"],[])
            self.assertIsNone(result["digest"]["exit_code"])

    def test_missing_cache_prices_and_usage_remain_unknown(self):
        result=parse_stream(b'{"type":"result","subtype":"success"}',run_id="no-usage")
        item=result["record"]
        self.assertIsNone(item["usage"]["cache_creation"])
        self.assertIsNone(item["usage"]["reported_cost"])
        self.assertFalse(item["usage"]["availability"]["cached_input"]=="")

    def test_retry_only_from_gateway_metadata_and_model_change_stays_unknown(self):
        data=(b'{"type":"system","subtype":"init","model":"m1","gateway":{"retry_count":2}}\n'
              b'{"type":"assistant","message":{"model":"m2"}}\n'
              b'{"type":"result","subtype":"success","usage":{"input_tokens":1}}')
        result=parse_stream(data,run_id="changed"); item=result["record"]
        self.assertIsNone(item["upstream_model"])
        self.assertTrue(any("model changed" in n for n in item["notes"]))
        self.assertEqual(result["gateway_retry_count_snapshot"],2)

    def test_partial_malformed_and_unknown_events_flag_incomplete(self):
        result=parse_stream(b'{bad}\n{"type":"assistant","message":{}}\n{"type":"future"}',run_id="partial")
        self.assertFalse(result["complete"])
        self.assertEqual(len(result["unsupported_or_malformed"]),2)
        self.assertIsNone(result["record"]["usage"]["input"])

class ClaudeC2Tests(unittest.TestCase):
    def events(self,*events):
        return b''.join((json.dumps(e)+'\n').encode() for e in events)

    def result(self,**usage):
        return {'type':'result','subtype':'success','is_error':False,'usage':usage}

    def test_unknown_gateway_does_not_silently_claim_xkiro(self):
        result=parse_stream(self.events(self.result(input_tokens=3)))
        self.assertIsNone(result['record']['gateway'])
        self.assertEqual(result['record']['route'],'claude-code/unknown/stream-json')
        validate(result['record'])
        with self.assertRaises(ValueError):
            validate(record(run_id='x',harness='claude-code',gateway='xkiro',route='claude-code/unknown/stream-json'))
        with self.assertRaises(ValueError): parse_stream(b'',gateway='other')
        with self.assertRaises(ValueError): parse_stream(b'',gateway='xkiro',route='claude-code/unknown/stream-json')

    def test_configured_reported_and_effective_models_remain_separate(self):
        raw=self.events({'type':'system','subtype':'init','model':'reported-fixture'},self.result(input_tokens=1))
        result=parse_stream(raw,gateway='xkiro',gateway_source='configured',configured_model='configured-fixture')
        self.assertEqual(result['configured_model'],'configured-fixture')
        self.assertEqual(result['reported_model'],'reported-fixture')
        self.assertIsNone(result['effective_upstream_model'])
        self.assertIsNone(result['record']['upstream_model'])
        self.assertEqual(result['source']['configured_model_status'],'CONFIGURED')
        self.assertEqual(result['source']['gateway_provenance'],'configured')

    def test_model_changes_are_not_hidden(self):
        raw=self.events({'type':'system','subtype':'init','model':'fixture-a'},
                        {'type':'assistant','message':{'model':'fixture-b'}},self.result())
        result=parse_stream(raw)
        self.assertIsNone(result['reported_model'])
        self.assertEqual(result['reported_models'],['fixture-a','fixture-b'])
        self.assertIsNone(result['effective_upstream_model'])

    def test_latest_turn_result_is_not_added_to_steps_or_cumulative_model_snapshots(self):
        raw=self.events({'type':'assistant','message':{'id':'one','usage':{'input_tokens':8,'output_tokens':1}}},
                        {'type':'assistant','message':{'id':'one','usage':{'input_tokens':8,'output_tokens':1}}},
                        {'type':'result','subtype':'success','usage':{'input_tokens':8,'output_tokens':4},
                         'modelUsage':{'fixture':{'inputTokens':80,'outputTokens':40}}},
                        {'type':'user','message':{'content':'synthetic'}},
                        {'type':'result','subtype':'success','usage':{'input_tokens':9,'output_tokens':5},
                         'modelUsage':{'fixture':{'inputTokens':89,'outputTokens':45}}})
        result=parse_stream(raw)
        self.assertTrue(result['complete'])
        self.assertEqual(result['record']['usage']['input'],9)
        self.assertEqual(result['record']['usage_scope'],'turn')
        self.assertEqual(len(result['message_usage']),1)
        self.assertIsNone(result['message_usage'][0]['usage']['output'])
        self.assertEqual(result['result_snapshots'][-1]['model_usage_snapshot']['fixture']['input'],89)
        self.assertIsNone(result['session_usage'])

    def test_partial_deltas_are_not_added_or_persisted(self):
        raw=self.events({'type':'stream_event','event':{'type':'message_start','message':{'usage':{'input_tokens':5}}}},
                        {'type':'stream_event','event':{'type':'content_block_delta','delta':{'thinking':'PRIVATE'}}},
                        {'type':'stream_event','event':{'type':'message_delta','usage':{'output_tokens':99}}},
                        {'type':'stream_event','event':{'type':'message_stop'}},self.result(input_tokens=7,output_tokens=3))
        result=parse_stream(raw)
        self.assertTrue(result['complete'])
        self.assertEqual(result['record']['usage']['output'],3)
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_missing_and_partial_cache_counters_are_not_zero_filled(self):
        item=parse_stream(self.events(self.result(input_tokens=5,cache_read_input_tokens=0)))['record']
        self.assertEqual(item['usage']['cached_input'],0)
        self.assertIsNone(item['usage']['cache_creation'])
        self.assertTrue(item['usage']['availability']['cache_creation'])

    def test_failed_and_inconsistent_success_results_are_not_complete(self):
        for event in ({'type':'result','subtype':'error_during_execution','is_error':True,'errors':['PRIVATE']},
                      {'type':'result','subtype':'success','is_error':True}):
            result=parse_stream(self.events(event))
            self.assertFalse(result['complete'])
            self.assertEqual(result['completion_status'],'failed')
            self.assertNotIn('PRIVATE',json.dumps(result))

    def test_cancellation_aborted_messages_and_process_exit(self):
        result=parse_stream(self.events({'type':'assistant','aborted':True,'message':{}}))
        self.assertEqual(result['completion_status'],'cancelled')
        self.assertFalse(result['complete'])
        self.assertEqual(parse_stream(b'',cancelled=True)['completion_status'],'cancelled')
        self.assertEqual(parse_stream(self.events(self.result()),process_exit_code=1)['completion_status'],'failed')
        self.assertIsNone(parse_stream(self.events(self.result()))['process_exit_code'])

    def test_partial_after_result_cannot_reuse_previous_counters(self):
        result=parse_stream(self.events(self.result(input_tokens=10),{'type':'user','message':{'content':'synthetic'}}))
        self.assertFalse(result['complete'])
        self.assertIsNone(result['record']['usage']['input'])
        self.assertEqual(result['record']['usage_scope'],'unknown')

    def test_retry_counts_are_separate_snapshots_not_sums(self):
        raw=self.events({'type':'system','subtype':'api_retry','uuid':'retry-one','gateway':{'retry_count':2}},
                        {'type':'system','subtype':'api_retry','uuid':'retry-one','gateway':{'retry_count':2}},
                        self.result())
        result=parse_stream(raw)
        self.assertEqual(result['harness_retry_event_count'],1)
        self.assertEqual(result['gateway_retry_count_snapshot'],2)
        self.assertIsNone(result['gateway_usage'])
        self.assertIsNone(parse_stream(self.events(self.result()))['harness_retry_event_count'])

    def test_duplicate_results_are_not_added_and_conflicts_are_incomplete(self):
        a={**self.result(input_tokens=7),'uuid':'result-one'}
        result=parse_stream(self.events(a,a))
        self.assertEqual(len(result['result_snapshots']),1)
        self.assertTrue(result['complete'])
        result=parse_stream(self.events(a,{**a,'usage':{'input_tokens':8}}))
        self.assertFalse(result['complete'])

    def test_invalid_json_versions_shapes_and_counters_are_safe(self):
        for raw in (b'{bad PRIVATE}\n',b'\xff\n',b'[]\n',b'{"type":[]}\n',b'{"type":"result","type":"user"}\n',
                    b'{"type":"future","text":"PRIVATE"}\n',
                    b'{"type":"result","subtype":"success","schema_version":"future"}\n',
                    b'{"type":"result","subtype":"success","usage":{"input_tokens":NaN}}\n',
                    self.events(self.result(input_tokens=True)),self.events(self.result(output_tokens=-1))):
            with self.subTest(raw=raw):
                result=parse_stream(raw)
                self.assertFalse(result['complete'])
                self.assertTrue(result['unsupported_or_malformed'])
                self.assertNotIn('PRIVATE',json.dumps(result))

    def test_mixed_sessions_withhold_usage(self):
        raw=self.events({**self.result(input_tokens=2),'session_id':'one'},
                        {**self.result(input_tokens=3),'session_id':'two'})
        result=parse_stream(raw)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['record']['usage']['input'])
        self.assertEqual(result['result_snapshots'],[])

    def test_cost_estimates_and_gateway_payload_do_not_become_billing(self):
        raw=self.events({**self.result(input_tokens=9),'total_cost_usd':99,
                        'modelUsage':{'fixture':{'inputTokens':999,'costUSD':123}},
                        'gateway':{'usage':{'reported_cost':456},'authorization':'PRIVATE'}})
        result=parse_stream(raw)
        self.assertIsNone(result['record']['usage']['reported_cost'])
        self.assertIsNone(result['billing'])
        self.assertIsNone(result['upstream_usage'])
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_sensitive_payload_exclusion_and_sanitized_expansion(self):
        marker='PRIVATE_API_KEY_REASONING_FIXTURE'
        raw=self.events({'type':'system','subtype':'init','session_id':marker,'apiKeySource':marker,'cwd':marker},
                        {'type':'assistant','message':{'id':marker,'model':'sk-secret-fixture',
                         'content':[{'type':'thinking','thinking':marker}],'usage':{'input_tokens':1}}},
                        {'type':'user','message':{'content':marker}},
                        {**self.result(input_tokens=2),'result':marker,'errors':[marker]})
        with tempfile.TemporaryDirectory() as d:
            result=process(raw,artifact_dir=d)
            self.assertNotIn(marker,json.dumps(result))
            self.assertNotIn('sk-secret',json.dumps(result))
            for p in Path(d).iterdir(): self.assertNotIn(marker.encode(),p.read_bytes())
            self.assertEqual(result['source']['input_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertIn('events',json.loads(expand_bytes(result['digest'],'stdout')))

    def test_pretty_printed_json_and_windows_space_paths_file_stdin(self):
        raw=json.dumps(self.result(input_tokens=2),indent=2).encode()
        self.assertTrue(parse_stream(raw)['complete'])
        with tempfile.TemporaryDirectory(prefix='c2 windows space ') as d:
            root=Path(d); path=root/'input with spaces.json'; path.write_bytes(raw)
            records=root/'records.jsonl'
            for index,stdin in enumerate((False,True)):
                args=[sys.executable,claude_adapter.__file__]
                if not stdin: args.append(str(path))
                args+=['--artifacts',str(root/f'artifacts {index}'),'--records',str(records),
                       '--gateway','xkiro','--gateway-source','synthetic-fixture',
                       '--configured-model','fixture','--source','synthetic-fixture','--process-exit-code','0']
                proc=subprocess.run(args,input=raw if stdin else None,capture_output=True)
                self.assertEqual(proc.returncode,0,proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['record']['usage']['input'],2)
            for line in records.read_text().splitlines(): validate(json.loads(line))

    def test_parser_never_invokes_model_or_changes_environment(self):
        from unittest.mock import patch
        import os
        before=dict(os.environ)
        with tempfile.TemporaryDirectory() as d, patch('subprocess.Popen',side_effect=AssertionError('unexpected process')):
            process(self.events(self.result()),artifact_dir=d)
        self.assertEqual(dict(os.environ),before)

    def test_subagent_usage_and_abort_do_not_change_main_loop_status(self):
        raw=self.events(self.result(input_tokens=8),{'type':'assistant','parent_tool_use_id':'subagent',
                        'aborted':True,'message':{'model':'subagent-fixture','id':'subagent-msg','usage':{'input_tokens':999}}})
        result=parse_stream(raw)
        self.assertTrue(result['complete'])
        self.assertEqual(result['record']['usage']['input'],8)
        self.assertEqual(result['message_usage'],[])
        self.assertEqual(result['reported_models'],[])

    def test_open_stream_and_conflicting_message_snapshots_are_incomplete(self):
        raw=self.events({'type':'stream_event','event':{'type':'message_start'}},self.result())
        self.assertFalse(parse_stream(raw)['complete'])
        raw=self.events({'type':'assistant','message':{'id':'same','usage':{'input_tokens':1}}},
                        {'type':'assistant','message':{'id':'same','usage':{'input_tokens':2}}},self.result())
        self.assertFalse(parse_stream(raw)['complete'])

    def test_identity_survives_the_base_record_and_source_is_explicit(self):
        raw=self.events({'type':'system','subtype':'init','model':'reported-fixture','claude_code_version':'2.1.325'},self.result())
        result=parse_stream(raw,gateway='xkiro',gateway_source='configured',configured_model='configured-fixture',source='synthetic-fixture')
        self.assertTrue(any('CONFIGURED model' in n for n in result['record']['notes']))
        self.assertTrue(any('REPORTED main-loop' in n for n in result['record']['notes']))
        self.assertEqual(result['source']['reported_cli_versions'],['2.1.325'])
        self.assertEqual(result['source']['source'],'synthetic-fixture')
        self.assertEqual(result['record']['source_kind'],'claude-code-json-events-synthetic-fixture')

    def test_cli_failure_is_two_without_payload_leakage(self):
        with tempfile.TemporaryDirectory() as d:
            proc=subprocess.run([sys.executable,claude_adapter.__file__,'--artifacts',d],
                                input=b'{"type":"result","subtype":"error_during_execution","errors":["PRIVATE"]}',capture_output=True)
            self.assertEqual(proc.returncode,2,proc.stderr)
            self.assertNotIn(b'PRIVATE',proc.stdout)


if __name__=='__main__': unittest.main()
