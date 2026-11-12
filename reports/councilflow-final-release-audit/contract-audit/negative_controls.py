"""Read-only synthetic negative controls against production validation, not native proof."""
import copy, hashlib, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests'))
import test_contracts as t

def cases():
 yield 'valid_baseline', t.sequence(), True
 data=t.sequence()
 failed=copy.deepcopy(data[-1]); failed['message_id']='EARLIER-CHECK'; failed['payload']['status']='failed'; failed['payload']['results'][0]['status']='failed'
 data.insert(-1,failed)
 yield 'mandatory_planner_failure_bypassed',data,False
 data=t.sequence()
 failed=t.report('EARLIER','reviewer','M6',status='failed')
 failed['payload']['comparison']['independent_rerun'].update(status='MISMATCH',stdout_sha256='b'*64)
 data.insert(6,failed)
 yield 'mandatory_reviewer_failure_hidden',data,False
 data=t.sequence()
 data[3]['payload']['acceptance_ids']=['AC1'];data[4]['payload']['acceptance_ids']=['AC1']
 data[5]['payload']['acceptance_ids']=['AC2'];data[6]['payload']['acceptance_ids']=['AC2']
 yield 'independent_required_coverage_split',data,False
 data=t.sequence()[:7]
 data[-1]['payload']['status']='failed';data[-1]['payload']['comparison']['discrepancies']=['AC1 incomplete despite matching deterministic rerun']
 yield 'truthful_reviewer_failure_with_match',data,True
 data=t.sequence();data[-1]['sender']['instance_id']='different-planner'
 yield 'original_planner_replaced',data,False
 data=t.sequence();a=copy.deepcopy(data[0]);a['message_id']='REPUBLISH';a['payload']['objective']='Changed objective';a['payload']['scope']=['other/**'];data.insert(1,a)
 yield 'publication_objective_scope_changed',data,False

def main():
 results=[]
 for name,data,expected in cases():
  try:t.c.validate_sequence(data); actual=True;error=None
  except t.c.ContractError as exc:actual=False;error={'code':exc.code,'field':exc.field,'detail':exc.detail}
  results.append({'case':name,'expected_valid':expected,'actual_valid':actual,'satisfied':expected==actual,'error':error})
 print(json.dumps({'kind':'synthetic-negative-controls','production_sha256':hashlib.sha256((ROOT/'.agents/skills/council-flow/scripts/contracts.py').read_bytes()).hexdigest(),'results':results},indent=2))
 return 0 if all(r['satisfied'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
