/** Disposable presentation data. No contract validation, filesystem access, or execution. */
export const SCHEMA = 'councilflow-dashboard-view/1';
export const MAX_BYTES = 2 * 1024 * 1024;
export const ROLES = ['Planner', 'Manager', 'Worker', 'Tester', 'Reviewer'];
export const PROVENANCE = ['Host-observed', 'Structurally validated', 'Execution evidence', 'Agent-reported', 'Derived', 'Synthetic demonstration'];
export const STAGES = ['Not started', 'Worker reported', 'Tester passed', 'Tester failed', 'Reviewer checked', 'Planner accepted', 'Planner rejected'];
export const KINDS = ['contract', 'source-fidelity', 'worker', 'tester', 'reviewer', 'rerun', 'planner'];
const fail = message => { throw new Error(message); };
const obj = (v, keys, path) => {
  if (!v || typeof v !== 'object' || Array.isArray(v)) fail(`${path}: expected an object.`);
  for (const key of Object.keys(v)) if (!keys.includes(key)) fail(`${path}: unsupported field ${key}.`);
};
const str = (v, path, max = 1000) => {
  if (typeof v !== 'string' || !v.trim() || v.length > max || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(v)) fail(`${path}: expected nonempty text, at most ${max} characters.`);
};
const nullable = (v, check) => { if (v != null) check(v); };
const one = (v, choices, path) => { if (!choices.includes(v)) fail(`${path}: unsupported value.`); };
const num = (v, path) => { if (!Number.isSafeInteger(v) || v < 0) fail(`${path}: expected a nonnegative safe integer.`); };
const arr = (v, path, max) => { if (!Array.isArray(v) || v.length > max) fail(`${path}: expected an array with at most ${max} items.`); };
const id = (v, path) => { if (typeof v !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}$/.test(v)) fail(`${path}: invalid identifier.`); };
const unique = (rows, key, path) => { if (new Set(rows.map(r => r[key])).size !== rows.length) fail(`${path}: duplicate ${key}.`); };
const date = (v, path) => nullable(v, x => { if (typeof x !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/.test(x) || !Number.isFinite(Date.parse(x)) || new Date(x).toISOString().replace('.000Z','Z') !== x.replace('.000Z','Z')) fail(`${path}: expected a valid UTC timestamp.`); });

// Inspect before parsing: cap nesting and reject duplicate object keys, including escaped aliases.
function guardJSON(text) {
  const stack = []; let inString = false, escaped = false, start = 0;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inString) {
      if (escaped) { escaped = false; continue; }
      if (c === '\\') { escaped = true; continue; }
      if (c === '"') {
        inString = false;
        let j = i + 1; while (/\s/.test(text[j] ?? '') && j < text.length) j++;
        if (text[j] === ':' && stack.at(-1)?.keys) {
          const key = JSON.parse(text.slice(start, i + 1));
          if (stack.at(-1).keys.has(key)) fail('Duplicate JSON key. Export a snapshot with unique fields.');
          stack.at(-1).keys.add(key);
        }
      }
    } else if (c === '"') { inString = true; start = i; }
    else if (c === '{' || c === '[') {
      stack.push(c === '{' ? { keys: new Set() } : {});
      if (stack.length > 16) fail('Input nesting exceeds 16 levels.');
    } else if (c === '}' || c === ']') stack.pop();
  }
}

export function parseSnapshot(text) {
  if (typeof text !== 'string' || new TextEncoder().encode(text).length > MAX_BYTES) fail('Input exceeds the 2 MiB limit. Import a smaller sanitized snapshot.');
  let v;
  try { guardJSON(text); v = JSON.parse(text); }
  catch (e) { if (e instanceof SyntaxError) fail('Malformed JSON. Import a valid dashboard snapshot.'); throw e; }
  obj(v, ['view_schema','synthetic','run_id','title','status','phase','active_attempt','source','started_at','last_observed_at','criteria','attempts','roles','activity','evidence','metrics','blockers'], 'snapshot');
  if (v.view_schema !== SCHEMA) fail(`Unsupported schema version. Expected ${SCHEMA}.`);
  if (typeof v.synthetic !== 'boolean') fail('synthetic: explicitly set true or false.');
  id(v.run_id, 'run_id'); str(v.title, 'title', 500);
  one(v.status, ['queued','active','waiting-for-Owner','blocked','failed','completed','cancelled','interrupted','unknown'], 'status');
  one(v.phase, [...ROLES, 'Owner', 'Unknown'], 'phase');
  obj(v.source, ['label','original_criteria_ref'], 'source'); str(v.source.label, 'source.label'); nullable(v.source.original_criteria_ref, x => str(x, 'original_criteria_ref'));
  date(v.started_at, 'started_at'); date(v.last_observed_at, 'last_observed_at');
  if (v.started_at && v.last_observed_at && Date.parse(v.started_at) > Date.parse(v.last_observed_at)) fail('Observed end precedes observed start.');
  arr(v.criteria, 'criteria', 200); unique(v.criteria, 'id', 'criteria');
  for (const c of v.criteria) { obj(c, ['id','text'], 'criterion'); id(c.id, 'criterion.id'); str(c.text, 'criterion.text', 2000); }
  arr(v.attempts, 'attempts', 50); unique(v.attempts, 'id', 'attempts');
  const criterionIds = new Set(v.criteria.map(c => c.id));
  for (const a of v.attempts) {
    obj(a, ['id','candidate','label','results'], 'attempt'); id(a.id, 'attempt.id'); str(a.candidate, 'candidate', 200); str(a.label, 'attempt.label', 200);
    arr(a.results, 'results', 200); unique(a.results, 'criterion_id', 'results');
    for (const r of a.results) {
      obj(r, ['criterion_id','stage','evidence_ids'], 'result'); if (!criterionIds.has(r.criterion_id)) fail('Result refers to an unknown original criterion.');
      one(r.stage, STAGES, 'result.stage'); arr(r.evidence_ids, 'evidence_ids', 30); for (const x of r.evidence_ids) id(x, 'evidence_id');
      if (new Set(r.evidence_ids).size !== r.evidence_ids.length) fail('Duplicate evidence reference.');
    }
  }
  if (v.attempts.length ? !v.attempts.some(a => a.id === v.active_attempt) : v.active_attempt != null) fail('active_attempt must identify an existing attempt, or be null for an empty run.');
  arr(v.evidence, 'evidence', 2000); unique(v.evidence, 'id', 'evidence');
  for (const e of v.evidence) {
    obj(e, ['id','kind','attempt_id','candidate','criterion_id','outcome','provenance','summary','reference','command','exit_code','stdout_sha256','compared_stdout_sha256','compared_exit_code'], 'evidence');
    id(e.id, 'evidence.id'); one(e.kind, KINDS, 'evidence.kind');
    if (!v.attempts.some(a => a.id === e.attempt_id && a.candidate === e.candidate)) fail('Evidence candidate/attempt binding is invalid.');
    if (!criterionIds.has(e.criterion_id)) fail('Evidence refers to an unknown criterion.');
    one(e.outcome, ['passed','failed','unverified','accepted','rejected'], 'evidence.outcome'); one(e.provenance, PROVENANCE, 'provenance');
    str(e.summary, 'evidence.summary', 2000); nullable(e.reference, x => str(x, 'reference')); nullable(e.command, x => str(x, 'command'));
    if (!v.synthetic && e.provenance === 'Synthetic demonstration') fail('Synthetic evidence requires a synthetic snapshot.');
    for (const k of ['exit_code','compared_exit_code']) nullable(e[k], x => { if (!Number.isSafeInteger(x)) fail(`${k}: invalid exit code.`); });
    for (const k of ['stdout_sha256','compared_stdout_sha256']) nullable(e[k], x => { if (typeof x !== 'string' || !/^[a-f0-9]{64}$/.test(x)) fail(`${k}: expected SHA-256.`); });
  }
  const evidenceIds = new Set(v.evidence.map(e => e.id));
  for (const a of v.attempts) for (const r of a.results) for (const ref of r.evidence_ids) {
    if (!evidenceIds.has(ref)) fail('Missing referenced evidence.');
    const e = v.evidence.find(e => e.id === ref);
    if (e.attempt_id !== a.id || e.criterion_id !== r.criterion_id) fail('Cross-attempt or cross-criterion evidence reference.');
  }
  arr(v.roles, 'roles', 5); unique(v.roles, 'role', 'roles');
  for (const r of v.roles) {
    obj(r, ['role','state','model','assignment','last_activity','attempt_id','tokens'], 'role'); one(r.role, ROLES, 'role');
    one(r.state, ['not observed','active','waiting','stopped','failed','unknown'], 'role.state');
    for (const k of ['model','assignment','last_activity']) nullable(r[k], x => str(x, `role.${k}`));
    nullable(r.attempt_id, x => { if (!v.attempts.some(a => a.id === x)) fail('Role has an unknown attempt.'); }); nullable(r.tokens, x => num(x, 'role.tokens'));
  }
  arr(v.activity, 'activity', 5000); unique(v.activity, 'id', 'activity');
  for (const e of v.activity) {
    obj(e, ['id','at','role','category','tone','label','detail','provenance','attempt_id'], 'event'); id(e.id, 'event.id'); date(e.at, 'event.at');
    one(e.role, [...ROLES,'Unattributed'], 'event.role'); one(e.category, ['handoff','implementation','verification','decision','system'], 'event.category');
    one(e.tone, ['info','success','warning','failure'], 'event.tone'); str(e.label, 'event.label'); nullable(e.detail, x => str(x, 'event.detail', 2000)); one(e.provenance, PROVENANCE, 'event.provenance');
    nullable(e.attempt_id, x => { if (!v.attempts.some(a => a.id === x)) fail('Event has an unknown attempt.'); });
    if (e.at && v.last_observed_at && Date.parse(e.at) > Date.parse(v.last_observed_at)) fail('Event occurs after the snapshot last observation.');
    if (!v.synthetic && e.provenance === 'Synthetic demonstration') fail('Synthetic events require a synthetic snapshot.');
  }
  obj(v.metrics ?? {}, ['tokens','files_changed','tests_passed','tests_failed','messages','token_scope'], 'metrics');
  for (const k of ['tokens','files_changed','tests_passed','tests_failed','messages']) nullable(v.metrics?.[k], x => num(x, `metrics.${k}`));
  nullable(v.metrics?.token_scope, x => str(x, 'token_scope'));
  if ((v.metrics?.tokens != null || v.roles.some(r => r.tokens != null)) && !v.metrics?.token_scope) fail('Token counters need an explicit scope and attribution note.');
  arr(v.blockers ?? [], 'blockers', 100);
  for (const b of v.blockers ?? []) { obj(b, ['kind','text'], 'blocker'); one(b.kind, ['blocker','failed check','missing evidence','Owner decision'], 'blocker.kind'); str(b.text, 'blocker.text'); }
  return v;
}

/** Count only a candidate-bound full chain; these remain imported assertions, not authentication. */
export function project(snapshot, attemptId = snapshot.active_attempt, now = Date.now()) {
  const attempt = snapshot.attempts.find(a => a.id === attemptId);
  const rows = snapshot.criteria.map(c => {
    const result = attempt?.results.find(r => r.criterion_id === c.id);
    const evidence = (result?.evidence_ids ?? []).map(id => snapshot.evidence.find(e => e.id === id));
    const has = (kind, outcome = 'passed') => evidence.some(e => e.kind === kind && e.outcome === outcome);
    const rerun = evidence.some(e => e.kind === 'rerun' && e.outcome === 'passed' && e.command && e.exit_code === 0 && e.compared_exit_code === 0 && e.stdout_sha256 && e.stdout_sha256 === e.compared_stdout_sha256 && evidence.some(t => t.kind === 'tester' && t.outcome === 'passed' && t.command === e.command && t.exit_code === e.exit_code && t.stdout_sha256 === e.stdout_sha256));
    const knownFailure = snapshot.evidence.some(e => e.attempt_id === attempt?.id && e.criterion_id === c.id && ['failed','rejected','unverified'].includes(e.outcome));
    const accepted = result?.stage === 'Planner accepted' && Boolean(snapshot.source.original_criteria_ref) && KINDS.filter(k => !['rerun','planner'].includes(k)).every(k => has(k)) && rerun && has('planner', 'accepted') && !knownFailure;
    return { ...c, stage: result?.stage ?? 'Not started', evidence, accepted, incomplete: result?.stage === 'Planner accepted' && !accepted };
  });
  const accepted = rows.filter(r => r.accepted).length;
  const total = rows.length;
  const age = snapshot.last_observed_at ? now - Date.parse(snapshot.last_observed_at) : null;
  return { attempt, rows, accepted, total, percent: total ? Math.round(accepted / total * 1000) / 10 : null,
    stale: age == null || age > 15 * 60 * 1000, age,
    elapsed: snapshot.started_at && snapshot.last_observed_at ? (Date.parse(snapshot.last_observed_at) - Date.parse(snapshot.started_at)) / 1000 : null,
    activity: snapshot.activity.filter(e => !e.attempt_id || e.attempt_id === attemptId).slice().reverse() };
}
