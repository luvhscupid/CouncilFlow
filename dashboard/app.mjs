import { parseSnapshot, project, ROLES, KINDS, MAX_BYTES } from './projection.mjs';
import { fixture } from './fixtures.mjs';
const $ = id => document.getElementById(id);
const text = (id,value) => { $(id).textContent = value; };
// Imported strings only cross textContent. No HTML, markdown, URLs, paths, or commands execute.
function el(tag, cls, value) { const e=document.createElement(tag); if(cls)e.className=cls; if(value!=null)e.textContent=value; return e; }
function badge(value, cls='neutral') { return el('span',`badge ${cls}`,value); }
function button(label, fn, cls='') { const b=el('button',cls,label);b.type='button';b.addEventListener('click',fn);return b; }
const fmt = n => n == null ? 'Not reported' : new Intl.NumberFormat().format(n);
const time = value => value ? new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit',timeZone:'UTC',hour12:false}).format(new Date(value))+' UTC' : 'Not reported';
const stamp = value => value ? new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'medium',timeZone:'UTC'}).format(new Date(value))+' UTC' : 'Not reported';
const duration = seconds => seconds == null ? 'Not reported' : `${Math.floor(seconds/60)}m ${seconds%60}s`;
const kindLabel = {contract:'Contract validation','source-fidelity':'Source fidelity',worker:'Worker evidence',tester:'Tester execution',reviewer:'Reviewer comparison',rerun:'Independent rerun',planner:'Final Planner decision'};
let snapshot=fixture(), selected=snapshot.active_attempt, limit=50, returnFocus=null, imported=null;
let view;

function inspect(title, nodes) {
  returnFocus=document.activeElement;
  text('inspector-title',title);$('inspector-content').replaceChildren(...nodes);$('inspector').showModal();
}
function evidenceNodes(items) {
  if(!items.length)return [el('p','empty','No evidence reported. Inspect the original host records before relying on a claim.')];
  return items.map(e=>{
    const d=el('article','evidence-item');d.append(el('h3','',kindLabel[e.kind]),badge(e.outcome,e.outcome==='failed'||e.outcome==='rejected'?'failure':'neutral'),el('p','',e.summary),el('p','provenance',e.provenance));
    const dl=el('dl','evidence-fields');
    for(const [key,value] of Object.entries({ID:e.id,Attempt:e.attempt_id,Candidate:e.candidate,Criterion:e.criterion_id,Reference:e.reference,Command:e.command,'Exit code':e.exit_code,'Tester exit code':e.compared_exit_code,'Rerun stdout SHA-256':e.stdout_sha256,'Tester stdout SHA-256':e.compared_stdout_sha256})) {
      dl.append(el('dt','',key),el('dd','mono',value??'Not reported'));
    }
    d.append(dl,el('small','','References and commands are inert text. No artifacts are opened or executed.'));return d;
  });
}
function inspectCriterion(row) {
  const introduction=el('p','',row.text), history=el('div','history');history.append(el('h3','','Candidate history'));
  for(const a of snapshot.attempts) {
    const r=a.results.find(r=>r.criterion_id===row.id);
    history.append(el('p','',`${a.id} / ${a.candidate}: ${r?.stage??'Not started'}${a.id===snapshot.active_attempt?' · current candidate':' · historical'}`));
  }
  inspect(`${row.id} · ${row.accepted?'Planner accepted':row.incomplete?'Unverified acceptance claim':row.stage}`,[introduction,history,...evidenceNodes(row.evidence)]);
}
function render() {
  view=project(snapshot,selected);
  const historical=selected!==snapshot.active_attempt;
  text('run-id',snapshot.run_id);text('title',snapshot.title);text('run-meta',`${snapshot.source.label} · ${snapshot.run_id}`);
  const banner=$('source-banner');banner.replaceChildren(badge(snapshot.synthetic?'DEMO DATA':'IMPORTED SNAPSHOT',snapshot.synthetic?'demo':'neutral'),el('span','',snapshot.synthetic?'Synthetic demonstration. No agents are running in this viewer.':'Imported assertions; source authenticity and execution have not been independently verified here.'));
  const status=$('run-status');status.textContent=snapshot.status;status.className=`badge ${['failed','interrupted','blocked'].includes(snapshot.status)?'warning':'neutral'}`;
  text('fraction',`${view.accepted} / ${view.total}`);text('percentage',view.percent==null?'Not assessable':`${view.percent}%`);
  text('progress-caption',view.total?`Original criteria accepted for ${view.attempt?.candidate??'no candidate'}${historical?' · historical view':''}.`:'No original criteria available. Import a sanitized run to assess acceptance.');
  const seg=$('segments');seg.replaceChildren(...view.rows.map(r=>{const s=el('span',r.accepted?'accepted':r.stage.includes('failed')||r.stage.includes('rejected')?'failed':r.stage==='Not started'?'pending':'intermediate');s.title=`${r.id}: ${r.stage}`;return s;}));
  const groups=new Map();for(const r of view.rows) {const name=r.incomplete?'Unverified acceptance':r.stage;groups.set(name,(groups.get(name)??0)+1);}
  $('stage-counts').replaceChildren(...Array.from(groups,([name,count])=>el('span','',`${count} ${name}`)));
  text('operation',snapshot.phase==='Unknown'?'No phase reported':`${snapshot.phase} checkpoint`);
  const role=snapshot.roles.find(r=>r.role===snapshot.phase);
  text('operation-detail',role?.assignment??'No current assignment reported.');
  const timing=$('timing');timing.replaceChildren();
  for(const [label,value] of [['Observed duration',duration(view.elapsed)],['Last observation',stamp(snapshot.last_observed_at)],['Freshness',view.stale?'Stale / state unconfirmed':'Within 15-minute freshness window']])timing.append(el('dt','',label),el('dd','',value));
  const phases=['Owner','Planner','Manager','Worker','Tester','Reviewer','Manager','Planner','Owner'];
  $('phase-rail').replaceChildren(...phases.map((p,i)=>{const item=el('li',p===snapshot.phase?'current':'');item.append(el('span','phase-node',String(i+1)),el('span','',p));if(p===snapshot.phase)item.setAttribute('aria-label',`${p}: recorded phase role; exact handoff occurrence not reported`);return item;}));
  const notices=[...(snapshot.blockers??[])];
  if(view.stale)notices.unshift({kind:'stale snapshot',text:'No recent observation. A missing stop event does not prove a role is still running. Freshness uses a 15-minute viewer-clock heuristic.'});
  if(historical)notices.unshift({kind:'historical candidate',text:'You are inspecting a previous attempt. The run overview phase and role desk retain the latest snapshot state.'});
  if(view.rows.some(r=>r.incomplete))notices.push({kind:'missing evidence',text:'A Planner acceptance claim lacks the complete candidate-bound evidence chain and is excluded from final progress.'});
  $('attention').replaceChildren(...notices.map(b=>{const e=el('div','notice');e.append(el('strong','',b.kind),el('span','',b.text));return e;}));
  $('role-cards').replaceChildren(...ROLES.map(name=>{
    const r=snapshot.roles.find(r=>r.role===name), observed=r?.state??'not observed';
    const d=el('details',`role-card ${observed==='active'?'recorded-active':''}`),s=el('summary','');
    const top=el('div','role-top');top.append(el('span','role-initial',name.slice(0,1)),el('strong','',name),el('span','expand','+'));
    s.append(top,badge(observed==='active'?'Recorded active':observed,observed==='failed'?'failure':'neutral'),el('p','role-assignment',r?.assignment??'No assignment reported'),el('span','model',`Model: ${r?.model??'Not reported'}`));
    const content=el('div','role-detail');content.append(el('p','',r?.last_activity??'Activity not reported'),el('p','mono',`Attempt: ${r?.attempt_id??'Not reported'}`),el('p','',`Tokens: ${fmt(r?.tokens)}`),el('small','','Role state is recorded at import, not a live process indicator. Host identity mapping is not established by a role name.'));
    d.append(s,content);return d;
  }));
  const attempt=$('attempt');attempt.replaceChildren(...snapshot.attempts.map(a=>{const o=el('option','',a.label);o.value=a.id;return o;}));attempt.value=selected??'';attempt.disabled=!snapshot.attempts.length;
  $('criteria-list').replaceChildren(...view.rows.map(row=>{
    const b=button('',()=>inspectCriterion(row),'criterion-row');
    b.setAttribute('aria-label',`${row.id}: ${row.text}. ${row.accepted?'Final Planner accepted':row.stage}. Inspect evidence`);
    const title=el('span','criterion-title');title.append(el('span','mono criterion-id',row.id),el('strong','',row.text),el('small',row.accepted?'success-text':row.incomplete?'warning-text':'',row.incomplete?'Unverified acceptance claim':row.stage));b.append(title);
    for(const k of ['worker','tester','reviewer','planner']) {
      const e=row.evidence.find(e=>e.kind===k), rejected=e&&['failed','rejected'].includes(e.outcome), passed=e&&['passed','accepted'].includes(e.outcome);
      const cell=el('span',`check ${rejected?'bad':passed?'good':''}`,rejected?'×':passed?'✓':'–');cell.setAttribute('aria-hidden','true');b.append(cell);
    }return b;
  }));
  if(!view.rows.length)$('criteria-list').append(el('p','empty','No original criteria reported. Choose a demo scenario or import a run.'));
  renderEvents();
  $('trust-list').replaceChildren(...KINDS.map(kind=>{
    const items=snapshot.evidence.filter(e=>e.attempt_id===selected&&e.kind===kind);
    const failed=items.some(e=>['failed','rejected'].includes(e.outcome));
    const b=button('',()=>inspect(kindLabel[kind],evidenceNodes(items)),'trust-row');b.append(el('span','',kindLabel[kind]),badge(!items.length?'Missing':failed?'Failure reported':`${items.length} records`,failed?'failure':!items.length?'warning':'neutral'),el('span','open-detail','Inspect'));return b;
  }));
  const metrics=snapshot.metrics??{};
  const values=[['Reported tokens',fmt(metrics.tokens),metrics.token_scope??'Token scope and attribution were not reported. Per-role counters are not summed automatically.'],['Files changed',fmt(metrics.files_changed),'Snapshot-reported file count. File contents and paths are not loaded.'],['Tests passed / failed',`${fmt(metrics.tests_passed)} / ${fmt(metrics.tests_failed)}`,'Reported execution summary, independent of final Planner acceptance.'],['Messages exchanged',fmt(metrics.messages),'Snapshot-reported message count. This viewer does not intercept messages.'],['Attempts',fmt(snapshot.attempts.length),'Count of distinct attempts included in the imported snapshot.'],['Observed duration',duration(view.elapsed),'Difference between observed start and last observation, never a live countdown.']];
  $('metrics').replaceChildren(...values.map(([label,value,detail])=>{const b=button('',()=>inspect(label,[el('p','metric-value',value),el('p','',detail),el('p','provenance',snapshot.synthetic?'Synthetic demonstration':'Agent-reported / imported snapshot')]),'metric');b.append(el('span','',label),el('strong','',value),el('small','','Inspect scope'));return b;}));
}
function renderEvents() {
  const role=$('role-filter').value,type=$('type-filter').value;
  const rows=view.activity.filter(e=>(role==='all'||e.role===role)&&(type==='all'||e.category===type));
  text('event-count',`${rows.length} matching events · newest records first`);
  $('events').replaceChildren(...rows.slice(0,limit).map(e=>{
    const d=el('details',`event ${e.tone}`), s=el('summary','');
    const meta=el('span','event-meta');meta.append(el('time','mono',time(e.at)),el('strong','event-role',e.role),el('span','event-tone',e.tone));
    s.append(meta,el('span','event-label',e.label),el('span','provenance',`${e.provenance} · ${e.category}`));
    const body=el('div','event-detail');body.append(el('p','',e.detail??'No further detail reported.'),el('small','mono',`${e.id} / ${e.attempt_id??'Session-level, unattributed attempt'}`));d.append(s,body);return d;
  }));
  if(!rows.length)$('events').append(el('p','empty','No matching activity. Change the filters or import a run with activity records.'));
  $('more').hidden=rows.length<=limit;
}
function load(v) {snapshot=v;selected=v.active_attempt;limit=50;$('role-filter').value='all';$('type-filter').value='all';render();}
$('scenario').addEventListener('change',()=>{const value=$('scenario').value;load(value==='imported'?imported:fixture(value));text('import-status',value==='imported'?'Imported snapshot restored.':'Demonstration fixture loaded.');});
$('attempt').addEventListener('change',()=>{selected=$('attempt').value;limit=50;render();});
for(const id of ['role-filter','type-filter'])$(id).addEventListener('change',()=>{limit=50;renderEvents();});
$('more').addEventListener('click',()=>{limit+=50;renderEvents();});
$('import').addEventListener('click',()=>$('file').click());
$('file').addEventListener('change',async()=>{
  const f=$('file').files?.[0];if(!f)return;
  try {
    if(f.size>MAX_BYTES)throw new Error('Input exceeds the 2 MiB limit. Import a smaller sanitized snapshot.');
    const v=parseSnapshot(await f.text());imported=v;load(v);$('import-status').className='';
    let option=$('scenario').querySelector('[value="imported"]');if(!option){option=el('option','','Imported run');option.value='imported';$('scenario').append(option);}
    $('scenario').value='imported';text('import-status','Snapshot imported locally. Its assertions have not been authenticated.');
  }catch(e){text('import-status',`${e.message} Previous run preserved.`);$('import-status').className='import-error';}
  finally{$('file').value='';}
});
$('scenario').addEventListener('change',()=>{$('import-status').className='';});
$('close-inspector').addEventListener('click',()=>$('inspector').close());
$('inspector').addEventListener('close',()=>returnFocus?.focus());
$('theme').addEventListener('click',()=>{const light=document.documentElement.dataset.theme!=='light';document.documentElement.dataset.theme=light?'light':'dark';text('theme',light?'Dark theme':'Light theme');});
function updateNavigation() {
  const target=location.hash||'#overview';
  for(const link of document.querySelectorAll('.sidebar nav a')) {
    if(link.getAttribute('href')===target)link.setAttribute('aria-current','location');
    else link.removeAttribute('aria-current');
  }
}
window.addEventListener('hashchange',updateNavigation);
updateNavigation();
render();
