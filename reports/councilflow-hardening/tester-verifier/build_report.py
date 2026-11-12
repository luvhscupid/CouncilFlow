import hashlib,json
from pathlib import Path
root=Path.cwd(); d=root/'reports/councilflow-hardening/tester-verifier'
def digest(path): return hashlib.sha256((root/path).read_bytes()).hexdigest()
def ref(aid,path,kind): return {'artifact_id':aid,'path':path,'sha256':digest(path),'kind':kind}
manifest='reports/councilflow-hardening/worker-final/candidate-manifest.json'
base='reports/councilflow-hardening/manager/base-candidate-a002.json'
candidate={'artifact_id':'CFH-CANDIDATE-A004','path':manifest,'sha256':digest(manifest),'kind':'candidate-manifest'}
inputref={'artifact_id':'CFH-CURRENT-BASE-A002','path':base,'sha256':digest(base),'kind':'candidate-manifest'}
oracle={'artifact_id':'CFH-ORACLE-A004','path':'reports/councilflow-hardening/manager/oracle-a004-final.json','sha256':digest('reports/councilflow-hardening/manager/oracle-a004-final.json'),'kind':'verification-strategy'}
integ=ref('CFH-TESTER-INTEGRITY-A004','reports/councilflow-hardening/tester-verifier/integrity-checks.json','verification-record')
suites=ref('CFH-TESTER-SUITES-A004','reports/councilflow-hardening/tester-verifier/suite-executions.json','execution-record')
# Each raw stdout/stderr retained, hashes in suite-executions.json.
checks=[
 {'name':'Current product and contract suites (tests plus five demo/verification suites)','status':'passed','evidence_ref':suites},
 {'name':'Historical restoration initial suite','status':'failed','evidence_ref':ref('CFH-RESTORE-INITIAL-STDERR','reports/councilflow-hardening/tester-verifier/suite-7.stderr.bin','execution-output')},
 {'name':'Historical restoration final suite','status':'failed','evidence_ref':ref('CFH-RESTORE-FINAL-STDERR','reports/councilflow-hardening/tester-verifier/suite-8.stderr.bin','execution-output')},
 {'name':'Both operational JSON examples validate with repository-root artifact hashing','status':'passed','evidence_ref':ref('CFH-EXAMPLE-COMMANDS','reports/councilflow-hardening/tester-verifier/integrity-checks.json','verification-record')},
 {'name':'Stale candidate digest negative control is rejected','status':'passed','evidence_ref':ref('CFH-STALE-NEGATIVE-STDERR','reports/councilflow-hardening/tester-verifier/example-stale-negative.stderr.bin','execution-output')},
 {'name':'P004 publish, Worker assignment/report, and Tester assignment causal sequence','status':'passed','evidence_ref':ref('CFH-P004-SEQUENCE-STDOUT','reports/councilflow-hardening/tester-verifier/p004-context-sequence.stdout.bin','execution-output')},
 {'name':'P004 E1-E10 criteria exact text compared with frozen Gate3 and approved C3','status':'passed','evidence_ref':integ},
 {'name':'Full Plan checksum manifest (20 entries)','status':'passed','evidence_ref':integ},
 {'name':'A004 snapshot SHA-256, ZIP CRC, safe paths, exclusions, and manifest file bytes','status':'passed','evidence_ref':integ},
 {'name':'Worker execution record manifest hash consistency','status':'failed','evidence_ref':integ},
 {'name':'Symlink escape execution on this Windows host','status':'unverified','evidence_ref':ref('CFH-SUITE-STDERR','reports/councilflow-hardening/tester-verifier/suite-1.stderr.bin','execution-output')},
 {'name':'Frozen native Gate 3 live experiment and E1-E10 runtime outcomes','status':'unverified','evidence_ref':ref('CFH-ASSIGNMENT','reports/councilflow-hardening/manager/tester-final-assign.json','assignment')},
 {'name':'Authentic Owner fixture required for live E10 comparison','status':'unverified','evidence_ref':ref('CFH-GATE3-FROZEN','docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md','specification')},
]
jobreport={
 'protocol':'council-flow','version':'1.0','message_id':'CFH-M021','message_type':'job.report','plan_id':'CFH-P004','plan_revision':1,'task_id':'CFH-T004','attempt_id':'CFH-A004',
 'sender':{'role':'tester','instance_id':'/root/tester_verifier'},'recipient':{'role':'manager','instance_id':'/root'},'in_reply_to':'CFH-M020',
 'payload':{
  'status':'failed','summary':'The A004 candidate passed the six current product and contract suites, both root-bound examples, stale-digest rejection, P004 sequence, E1-E10 exact-text comparison, Full Plan checksums, and snapshot integrity. Two historical restoration suites fail on obsolete created_at fixtures; the Windows symlink test is privilege-skipped. Worker execution.json has a conflicting top-level manifest digest. Gate3 live runtime outcomes are unverified and were not assigned.',
  'acceptance_ids':['HF-03','HF-04','HF-05'],'candidate_ref':candidate,'input_candidate_ref':inputref,'oracle_ref':oracle,
  'findings':[
   'Executed all eight assigned unittest suites: 134 tests passed, 5 errored, and 1 skipped across 140 tests. The first six suites all passed (124 pass, one skip); reports/restoration/verification/initial had 3 errors of 8 and reports/restoration/verification/final had 2 errors of 7.',
   'The two restoration suites synthesize CouncilFlow messages with obsolete created_at fields rejected by the current 1.0 contract. The initial restoration suite also attempts symlink creation and fails with Windows WinError 1314; no junction or TOCTOU experiment was run.',
   'Both operational example packets passed root-bound validation. The copied stale-digest job.report negative exited 1 with artifact_hash, as expected. The P004 ordered publish/worker/tester-assignment sequence validated.',
   'P004 E1-E10 criterion bodies match exactly: E1-E3 and E5-E10 against frozen Gate3 v0.2; E4 against approved C3. This confirms criteria wording only, not live Gate3 behavior or Owner fixture fidelity.',
   'All 20 Full Plan checksum entries matched. A004 manifest SHA-256 is 6a0f0fad405da97cee6fc76f17afbfc78814a8f8e6ddcc2267ffa84834affcf9; all nine source files matched sizes and hashes. Candidate snapshot SHA-256 matched 8988dbb471618705c4acab392aaaba65c87b13f6df05ea18d7595b879b409a2d; ZIP CRC passed, all nine paths were safe, and no excluded Git/cache/temp metadata was present.',
   'Worker execution.json top-level manifest_sha256 is 307c08ff8e44dfb2ab132a43294c52f33f730c9b4ccb990a828c392debfd5586, inconsistent with recomputed manifest bytes. Its candidate_manifest_sha256 field matches the recomputed and assignment digest 6a0f0fad405da97cee6fc76f17afbfc78814a8f8e6ddcc2267ffa84834affcf9. The manifest/assignment hashes and actual candidate bytes control identity; the inconsistent execution field remains a Worker evidence defect.',
   'The symlink test was skipped in the main tests suite due WinError 1314; no junction or TOCTOU test ran. The assigned Gate3 experiment was not run. The frozen source states no authentic Owner fixture was identified, so live E1-E10 outcomes and E10 fixture comparison remain unverified.'
  ],
  'errors':[], 'checks':checks,
  'deterministic_commands':[{
   'command_id':'CFH-TESTER-JOB-REPORT-ROOT-A004','command':str(Path(__import__('sys').executable).resolve()),
   'arguments':['.agents/skills/council-flow/scripts/contracts.py','message','docs/CouncilFlow-Full-Plan/examples/job.report.json','--root','.'],
   'workdir':str(root.resolve()),'candidate_ref':candidate,'input_refs':[inputref],'exit_code':0,
   'stdout_sha256':'9c0e58ec75ef29742d82a29008db9dc6016e44ad3e316963d23533e5bb82b8bd','acceptance_id':'HF-04',
   'evidence_ref':ref('CFH-JOB-REPORT-STDOUT','reports/councilflow-hardening/tester-verifier/example-job-report.stdout.bin','execution-output')
  }]
 },
 'evidence_refs':[ref('CFH-PLAN-004','reports/councilflow-hardening/planner-correction-p004/plan.json','plan'),candidate,inputref,oracle,ref('CFH-SNAPSHOT-A004','reports/councilflow-hardening/worker-final/candidate-snapshot.zip','source-snapshot'),integ,suites]
}
(d/'job-report.json').write_text(json.dumps(jobreport,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
