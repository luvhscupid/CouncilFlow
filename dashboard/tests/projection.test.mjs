import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSnapshot, project, MAX_BYTES, SCHEMA } from '../projection.mjs';
import { fixture } from '../fixtures.mjs';
const parse = v => parseSnapshot(JSON.stringify(v));
test('fixtures validate and final acceptance excludes all intermediate stages',()=>{
  const v=fixture(),p=project(v);
  assert.equal(p.accepted,3);assert.equal(p.total,6);assert.equal(p.percent,50);
  assert.equal(project(v,'attempt-1').accepted,1);
  assert.equal(project(fixture('empty')).percent,null);
  assert.equal(fixture('stress').activity.length,1000);
});
test('new candidate never inherits old acceptance',()=>{
  const v=fixture();v.attempts.push({id:'attempt-3',candidate:'candidate-v3',label:'Rework',results:[]});v.active_attempt='attempt-3';
  assert.equal(project(parse(v)).accepted,0);assert.equal(project(v,'attempt-2').accepted,3);
});
test('known failures cannot be hidden by omitting a result reference',()=>{
  const v=fixture();v.evidence.push({...v.evidence.find(e=>e.id==='attempt-2-AC1-tester'),id:'other-failure',outcome:'failed'});
  assert.equal(project(parse(v)).accepted,2);
  const x=fixture();x.evidence.find(e=>e.id==='attempt-2-AC1-tester').stdout_sha256='b'.repeat(64);
  assert.equal(project(parse(x)).accepted,2);
});
test('missing, failed or mismatched verification cannot count as final acceptance',()=>{
  for(const kind of ['contract','source-fidelity','worker','tester','reviewer','rerun','planner']) {
    const v=fixture();const r=v.attempts[1].results[0];r.evidence_ids=r.evidence_ids.filter(id=>!id.endsWith('-'+kind));
    assert.equal(project(parse(v)).accepted,2,kind);
  }
  for(const change of [e=>e.stdout_sha256='b'.repeat(64),e=>e.exit_code=1,e=>e.compared_exit_code=1,e=>e.command=null,e=>e.outcome='unverified']) {
    const v=fixture();change(v.evidence.find(e=>e.id==='attempt-2-AC1-rerun'));assert.equal(project(parse(v)).accepted,2);
  }
  const v=fixture();v.source.original_criteria_ref=null;assert.equal(project(parse(v)).accepted,0);
});
test('malformed, oversized, nested, duplicate keys and escaped duplicate keys fail closed',()=>{
  assert.throws(()=>parseSnapshot('{'),/Malformed/);
  assert.throws(()=>parseSnapshot(' '.repeat(MAX_BYTES+1)),/2 MiB/);
  assert.throws(()=>parseSnapshot('['.repeat(17)+'0'+']'.repeat(17)),/nesting/);
  assert.throws(()=>parseSnapshot('{"a":1,"a":2}'),/Duplicate/);
  assert.throws(()=>parseSnapshot('{"a":1,"\\u0061":2}'),/Duplicate/);
});
test('version, strict allowlist, duplicate IDs and unsafe references fail closed',()=>{
  for(const change of [v=>v.view_schema='future/99',v=>v.secret='secret-shaped-content',v=>v.criteria.push(v.criteria[0]),v=>v.activity.push(v.activity[0]),v=>v.attempts[1].results[0].evidence_ids.push('missing'),v=>v.attempts[1].results[0].evidence_ids.push('attempt-1-AC1-worker'),v=>v.roles[0].role='Supervisor',v=>v.evidence[0].candidate='other',v=>v.run_id='../secret',v=>v.metrics.tokens=-1,v=>v.metrics.tokens=20,v=>v.roles[0].tokens=20]) {
    const v=fixture();change(v);assert.throws(()=>parse(v));
  }
});
test('missing optional metrics, role identities and times remain unknown',()=>{
  const v=fixture('interrupted');assert.equal(v.metrics.tokens,undefined);assert.equal(v.roles[0].model,null);
  assert.equal(project(v).stale,true);
  const empty=fixture('empty');assert.equal(project(empty).elapsed,null);assert.equal(project(empty).age,null);
});
test('timestamp chronology and invalid calendar dates are rejected',()=>{
  const v=fixture();v.last_observed_at='2026-02-31T07:18:42Z';assert.throws(()=>parse(v),/timestamp/);
  v.last_observed_at='2026-11-16T07:18:42Z';assert.throws(()=>parse(v),/precedes/);
  const x=fixture();x.activity[0].at='2027-01-01T00:00:00Z';assert.throws(()=>parse(x),/after/);
});
test('staleness is a viewer heuristic; duration freezes at last observed event',()=>{
  const v=fixture();const last=Date.parse(v.last_observed_at);
  assert.equal(project(v,undefined,last+1000).stale,false);
  assert.equal(project(v,undefined,last+16*60*1000).stale,true);
  assert.equal(project(v,undefined,last+99999999).elapsed,1122);
});
test('hostile text and paths remain inert strings, without fetching an artifact',()=>{
  const v=fixture();v.title='<img src=x onerror=alert(1)>';v.evidence[0].reference='../../private/secret';
  const x=parse(v);assert.equal(x.title,v.title);assert.equal(x.evidence[0].reference,v.evidence[0].reference);
});
test('non-demo imports cannot hide synthetic events',()=>{
  const v=fixture();v.synthetic=false;assert.throws(()=>parse(v),/Synthetic/);
  v.activity=[];assert.throws(()=>parse(v),/Synthetic evidence/);
});
test('minimal empty projection is supported with optional values missing',()=>{
  const v={view_schema:SCHEMA,synthetic:false,run_id:'empty',title:'Empty',status:'unknown',phase:'Unknown',source:{label:'Local sanitized projection'},criteria:[],attempts:[],roles:[],evidence:[],activity:[]};
  assert.equal(project(parse(v)).total,0);
});
