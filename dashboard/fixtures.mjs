import { SCHEMA, ROLES, KINDS, parseSnapshot } from './projection.mjs';
const hash = 'a'.repeat(64);
const criteria = [
  ['AC1','Preserve the original acceptance criteria'],
  ['AC2','Reject malformed and oversized inputs'],
  ['AC3','Keep evidence bound to its candidate'],
  ['AC4','Verify keyboard and mobile navigation'],
  ['AC5','Preserve rework and attempt history'],
  ['AC6','Document the offline installation'],
].map(([id,text]) => ({id,text}));
function evidence(attempt, candidate, criterion, kind, outcome) {
  return { id: `${attempt}-${criterion}-${kind}`, kind, attempt_id: attempt, candidate, criterion_id: criterion, outcome,
    provenance: 'Synthetic demonstration', summary: {
      contract: 'Controlled packets passed structural validation. This is not sender authentication.',
      'source-fidelity': 'Original criterion text compared with the frozen input.',
      worker: 'Worker reported the candidate and developer checks.', tester: 'Tester reported an independent command execution.',
      reviewer: 'Reviewer compared the candidate, original criteria and Tester evidence.',
      rerun: 'Reviewer rerun matched exit code and CRLF-to-LF normalized stdout SHA-256.', planner: 'Planner recorded a final criterion decision for this candidate.'
    }[kind], reference: `synthetic:${attempt}/${criterion}/${kind}`,
    ...(['tester','rerun'].includes(kind) ? {command:'python -m unittest discover -s tests',exit_code:outcome==='failed'?1:0,stdout_sha256:hash} : {}),
    ...(kind === 'rerun' ? {compared_exit_code:0,compared_stdout_sha256:hash} : {}) };
}
function demo() {
  const v = { view_schema: SCHEMA, synthetic:true, run_id:'demo-observer-017', title:'CouncilFlow / Offline evidence viewer', status:'active', phase:'Reviewer', active_attempt:'attempt-2',
    source:{label:'Bundled synthetic fixture · no host connection',original_criteria_ref:'synthetic:owner-plan-v1'}, started_at:'2026-11-17T07:00:00Z',last_observed_at:'2026-11-17T07:18:42Z',criteria,
    attempts:[],evidence:[],roles:[],activity:[],metrics:{tokens:null,files_changed:12,tests_passed:38,tests_failed:0,messages:17,token_scope:null},
    blockers:[{kind:'missing evidence',text:'AC4 is waiting for the Reviewer rerun. Tester success is not final acceptance.'}] };
  for (const [index, stages] of [[1,['Planner accepted','Tester failed','Reviewer checked','Not started','Worker reported','Not started']],[2,['Planner accepted','Planner accepted','Planner accepted','Reviewer checked','Tester passed','Worker reported']]]) {
    const attempt=`attempt-${index}`,candidate=`candidate-v${index}`;
    const results=criteria.map((c,i) => {
      const stage=stages[i];
      const kinds=stage === 'Planner accepted' ? KINDS : stage === 'Reviewer checked' ? ['worker','tester','reviewer'] : stage.startsWith('Tester') ? ['worker','tester'] : stage === 'Worker reported' ? ['worker'] : [];
      const items=kinds.map(k => evidence(attempt,candidate,c.id,k,k==='planner'?'accepted':k==='tester'&&stage==='Tester failed'?'failed':'passed'));
      v.evidence.push(...items); return {criterion_id:c.id,stage,evidence_ids:items.map(e=>e.id)};
    });
    v.attempts.push({id:attempt,candidate,label:index===1?'Attempt 1 · superseded':'Attempt 2 · current candidate',results});
  }
  v.roles=ROLES.map(role=>({role,state:role==='Reviewer'?'active':role==='Manager'?'waiting':'stopped',model:null,assignment:{Planner:'Check the original criteria',Manager:'Coordinate verification',Worker:'Produce candidate-v2',Tester:'Verify input safeguards',Reviewer:'Compare evidence and rerun AC4'}[role],last_activity:{Planner:'Accepted AC1–AC3 for candidate-v2',Manager:'Dispatched independent Reviewer',Worker:'Reported candidate-v2',Tester:'Reported 38 checks passed',Reviewer:'Comparing AC4 evidence'}[role],attempt_id:'attempt-2',tokens:null}));
  const events=[
    ['Planner','decision','success','Published the frozen plan','Six original criteria retained.'],
    ['Manager','handoff','info','Validated the Worker assignment','Work scoped to the offline viewer.'],
    ['Worker','implementation','info','Started the first candidate','Synthetic activity; no agents are running.'],
    ['Tester','verification','failure','AC2 failed input validation','Oversized input was not rejected. Rework required.'],
    ['Manager','decision','warning','Opened attempt 2','Attempt 1 remains available in the history selector.'],
    ['Worker','implementation','success','Produced candidate-v2','Added bounded parsing and safe text rendering.'],
    ['Tester','verification','success','Reported 38 checks passed','Execution report is distinct from Planner acceptance.'],
    ['Planner','decision','success','Accepted AC1, AC2 and AC3','Final decisions are bound to candidate-v2.'],
    ['Manager','handoff','info','Dispatched Reviewer for AC4','Independent comparison and deterministic rerun required.'],
    ['Reviewer','verification','info','Comparing keyboard and mobile evidence','AC4 remains unaccepted until the complete chain is present.'],
  ];
  v.activity=events.map(([role,category,tone,label,detail],i)=>({id:`event-${i}`,at:`2026-11-17T07:${String(i*2).padStart(2,'0')}:${i===9?'42':'00'}Z`,role,category,tone,label,detail,provenance:'Synthetic demonstration',attempt_id:i<4?'attempt-1':'attempt-2'}));
  return v;
}
export function fixture(name='review') {
  const v=demo();
  if(name==='interrupted') { v.run_id='demo-interrupted';v.status='interrupted';v.phase='Worker';v.roles.forEach(r=>r.state='unknown');v.metrics={};v.blockers=[{kind:'blocker',text:'The record ends without a role stop event. Current execution state is unknown.'},{kind:'Owner decision',text:'Review the original host records before deciding how to resume. This viewer cannot authorize resumption.'}]; }
  if(name==='failed') {v.run_id='demo-failed';v.status='failed';v.active_attempt='attempt-1';v.phase='Tester';v.metrics.tests_failed=1;v.blockers=[{kind:'failed check',text:'AC2 failed. Candidate-v1 requires rework; later acceptance is not carried backward.'}];}
  if(name==='empty') {v.run_id='demo-empty';v.title='No run records yet';v.status='queued';v.phase='Unknown';v.active_attempt=null;v.started_at=null;v.last_observed_at=null;v.criteria=[];v.attempts=[];v.roles=[];v.activity=[];v.evidence=[];v.metrics={};v.blockers=[];}
  if(name==='stress') {
    v.title='CouncilFlow / A long project name that must remain readable on a small screen / Candidate verification and original-criteria preservation across repeated rework attempts';
    v.activity=Array.from({length:1000},(_,i)=>({...v.activity[9],id:`stress-${i}`,label:`Observation ${i+1}: verification evidence recorded`,at:'2026-11-17T07:18:42Z'}));
  }
  return parseSnapshot(JSON.stringify(v));
}
