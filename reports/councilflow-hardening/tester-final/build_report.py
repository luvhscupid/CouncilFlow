import json,hashlib,sys
from pathlib import Path
root=Path(r'E:\Saint\PROJECTS\CouncilFlow-main')
out=root/'reports/councilflow-hardening/tester-final'
assignment=json.loads((root/'reports/councilflow-hardening/manager/tester-final-assign.json').read_text(encoding='utf-8'))
execution_path=out/'execution.json'; execdata=json.loads(execution_path.read_text(encoding='utf-8'))
criteria_path=out/'criteria-check.json'
def ref(aid,path,kind):
 p=root/path
 return {'artifact_id':aid,'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':kind}
candidate=assignment['payload']['candidate_ref']; oracle=assignment['payload']['oracle_ref']
execution_ref=ref('CFH-TESTER-FINAL-EXECUTION','reports/councilflow-hardening/tester-final/execution.json','execution-record')
criteria_ref=ref('CFH-TESTER-CRITERIA-CHECK','reports/councilflow-hardening/tester-final/criteria-check.json','comparison-record')
checks=[
 ('Full repository regression suite', 'passed','HF-04'),
 ('Plan, failed A001 report, rework decision, and A002 report sequence', 'passed','HF-03'),
 ('job.assign example validates with root-bound hashes','passed','HF-03'),
 ('job.report example validates with root-bound hashes','failed','HF-03'),
 ('A001 input candidate source hashes remain available and exact','failed','HF-03'),
 ('Planner E1-E10 criteria match frozen spec/C3 wording exactly','failed','HF-04'),
 ('Normative frozen Gate3 and C3 bytes unchanged from baseline','passed','HF-05'),
 ('Full Plan bundle checksums','passed','HF-04'),
 ('Policy validator','passed','HF-04')]
report={'protocol':'council-flow','version':'1.0','message_id':'CFH-M011','message_type':'job.report',
 'plan_id':'CFH-P001','plan_revision':1,'task_id':'CFH-T001','attempt_id':'CFH-A002',
 'sender':{'role':'tester','instance_id':'/root/tester_final'},'recipient':{'role':'manager','instance_id':'/root'},
 'in_reply_to':'CFH-M010','payload':{'status':'failed',
  'summary':'The 82-test suite and plan/rework sequence passed, but root-bound job.report example validation failed; the A001 input candidate’s changed test file is not preserved at its recorded hash; and the Planner omitted/altered portions of frozen E4/E7/E9 text. The Gate3 experiment was not run.',
  'acceptance_ids':assignment['payload']['acceptance_ids'],'candidate_ref':candidate,'oracle_ref':oracle,
  'findings':['Command 3 (job.report example with --root .) exited 1: its candidate_ref uses a zero digest for the real receipt_calculator.py path.','Candidate A002’s own changed files match its manifest, but the A001 input manifest’s tests/test_contracts.py hash no longer matches the worktree after A002 edited that file; no immutable A001 source snapshot was found in assigned artifacts.','Criteria comparison against frozen Gate3 v0.2 plus approved C3 found E4 omits C3 final safeguards, E7 uses different AUTHORIZATION wording, and E9 omits the optional-inspection sentence. Exact matching rows and hashes are in criteria-check.json.','The Owner’s E10 frozen fixture for a qualifying Gate3 experiment was not supplied for this run; prior reports/gate3b/frozen-task.txt belongs to an earlier separate task and is not treated as this mission’s fixture.','Symlink regression was skipped on this Windows host (WinError 1314); junction and TOCTOU execution were not performed. This run does not establish OS containment or native Gate3 activation.'],
  'errors':[],'checks':[{'name':name,'status':status,'evidence_ref':execution_ref if name!='Planner E1-E10 criteria match frozen spec/C3 wording exactly' else criteria_ref} for name,status,_ in checks],
  'deterministic_commands':[{'command_id':'CFH-EXAMPLE-JOB-ASSIGN','command':execdata['commands'][1]['command'],
    'arguments':execdata['commands'][1]['arguments'],'workdir':execdata['commands'][1]['workdir'],
    'candidate_ref':candidate,'input_refs':[ref('CFH-CONTRACTS-PY','.agents/skills/council-flow/scripts/contracts.py','source'),ref('CFH-JOB-ASSIGN-EXAMPLE','docs/CouncilFlow-Full-Plan/examples/job.assign.json','json-example')],
    'exit_code':execdata['commands'][1]['exit_code'],'stdout_sha256':execdata['commands'][1]['stdout_sha256_crlf_to_lf'],
    'acceptance_id':'HF-03','evidence_ref':execution_ref}]},
 'evidence_refs':[execution_ref,criteria_ref,ref('CFH-TESTER-PLAN-FAILURE','reports/councilflow-hardening/tester-plan/execution.json','execution-record'),
    ref('CFH-A001-CANDIDATE','reports/councilflow-hardening/worker/candidate-manifest.json','candidate-manifest'),
    ref('CFH-A002-CANDIDATE','reports/councilflow-hardening/worker-rework/candidate-manifest.json','candidate-manifest')]
}
path=out/'job-report.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(path)
