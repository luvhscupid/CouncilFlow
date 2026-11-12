import hashlib, json, re, subprocess, sys
from pathlib import Path

root = Path(r'E:\Saint\PROJECTS\CouncilFlow-main')
evidence = root / 'reports/councilflow-hardening' / 'tester-final'
python = Path(sys.executable).resolve()
candidate = json.loads((root / 'reports/councilflow-hardening/worker-rework/candidate-manifest.json').read_text(encoding='utf-8'))
prev = json.loads((root / 'reports/councilflow-hardening/worker/candidate-manifest.json').read_text(encoding='utf-8'))
commands = [
    ['-m','unittest','discover','-s','tests','-v'],
    ['.agents/skills/council-flow/scripts/contracts.py','message','docs/CouncilFlow-Full-Plan/examples/job.assign.json','--root','.'],
    ['.agents/skills/council-flow/scripts/contracts.py','message','docs/CouncilFlow-Full-Plan/examples/job.report.json','--root','.'],
    ['.agents/skills/council-flow/scripts/contracts.py','sequence',
     'reports/councilflow-hardening/planner/plan-publish.json',
     'reports/councilflow-hardening/manager/worker-assign.json',
     'reports/councilflow-hardening/worker/job-report.json',
     'reports/councilflow-hardening/manager/tester-plan-assign.json',
     'reports/councilflow-hardening/tester-plan/job-report.json',
     'reports/councilflow-hardening/manager/rework-decision.json',
     'reports/councilflow-hardening/manager/worker-rework-assign.json',
     'reports/councilflow-hardening/worker-rework/job-report.json','--root','.'],
    ['.agents/skills/council-flow/scripts/contracts.py','policy','.agents/skills/council-flow/policies/roles.yaml'],
]
records=[]
for i,args in enumerate(commands,1):
    proc=subprocess.run([str(python),*args],cwd=root,capture_output=True,check=False)
    out=evidence / f'command-{i}.stdout.bin'; err=evidence / f'command-{i}.stderr.bin'
    out.write_bytes(proc.stdout);err.write_bytes(proc.stderr)
    records.append({'command':str(python),'arguments':args,'workdir':str(root),'exit_code':proc.returncode,
        'stdout_file':out.relative_to(root).as_posix(),'stderr_file':err.relative_to(root).as_posix(),
        'stdout_sha256_crlf_to_lf':hashlib.sha256(proc.stdout.replace(b'\r\n',b'\n')).hexdigest(),
        'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest(),
        'stdout_preview':proc.stdout[:400].decode('utf-8','replace'),
        'stderr_preview':proc.stderr[:800].decode('utf-8','replace')})

# Check each candidate's source hashes against the exact worktree.
def manifest_check(manifest):
    results=[]
    for item in manifest['files']:
        actual=hashlib.sha256((root/item['path']).read_bytes()).hexdigest()
        results.append({'path':item['path'],'expected':item['sha256'],'actual':actual,'match':actual==item['sha256']})
    return results

# Frozen normative bytes must still match the starting commit.
frozen=['docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md',
        'docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md',
        'docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md',
        'docs/gate3/CouncilFlow-Gate3-v0.2/SHA256SUMS.txt']
base=[]
for path in frozen:
    baseline=subprocess.run(['git','show',f'HEAD:{path}'],cwd=root,capture_output=True,check=False).stdout
    current=(root/path).read_bytes()
    base.append({'path':path,'head_sha256':hashlib.sha256(baseline).hexdigest(),
                 'current_sha256':hashlib.sha256(current).hexdigest(),'unchanged':baseline==current})

# Compare Planner's E1-E10 criterion strings with the frozen source, using the approved C3 E4 text.
plan=json.loads((root/'reports/councilflow-hardening/planner/plan.json').read_text(encoding='utf-8'))
frozen_text=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md').read_text(encoding='utf-8')
c3_text=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md').read_text(encoding='utf-8')

def section(text, heading):
    match=re.search(rf'(?m)^{re.escape(heading)}\s*$',text)
    if not match: return None
    end=re.search(r'(?m)^#{1,3} ',text[match.end():])
    body=text[match.end():match.end()+end.start()] if end else text[match.end():]
    return body.strip('\n')

criteria={x['id']:x['criterion'] for x in plan['acceptance'] if x['id'].startswith('E')}
criteria_results=[]
for n in range(1,11):
    key=f'E{n}'
    if n==4:
        head=re.search(r'(?m)^## (E4 — Custom-agent loading)$',c3_text)
        expected=head.group(1)+'\n'+section(c3_text,'## E4 — Custom-agent loading') if head else None
    else:
        hit=re.search(rf'(?m)^### (E{n} — .+)$',frozen_text)
        if hit:
            heading=hit.group(1)
            expected=heading+'\n'+section(frozen_text,'### '+heading)
        else: expected=None
    actual=criteria.get(key)
    criteria_results.append({'id':key,'matches_frozen_or_erratum':actual==expected,
       'actual_sha256':hashlib.sha256((actual or '').encode()).hexdigest(),
       'expected_sha256':hashlib.sha256((expected or '').encode()).hexdigest(),
       'actual_prefix':(actual or '')[:80], 'expected_prefix':(expected or '')[:80],
       'replacement_character_count':(actual or '').count('\ufffd')})

bundle=root/'docs/CouncilFlow-Full-Plan'
sums=[]
for line in (bundle/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    expected,path=line.split('  ',1)
    actual=hashlib.sha256((bundle/path).read_bytes()).hexdigest()
    sums.append({'path':path,'expected':expected,'actual':actual,'match':expected==actual})

summary={'python':str(python),'working_directory':str(root),'candidate_ref':{
    'artifact_id':'CFH-CANDIDATE-A002','path':'reports/councilflow-hardening/worker-rework/candidate-manifest.json',
    'sha256':hashlib.sha256((root/'reports/councilflow-hardening/worker-rework/candidate-manifest.json').read_bytes()).hexdigest()},
  'input_candidate_ref':{'artifact_id':'CFH-CANDIDATE-A001','path':'reports/councilflow-hardening/worker/candidate-manifest.json',
    'sha256':hashlib.sha256((root/'reports/councilflow-hardening/worker/candidate-manifest.json').read_bytes()).hexdigest()},
  'commands':records,'candidate_source_hash_checks':{'A001':manifest_check(prev),'A002':manifest_check(candidate)},
  'frozen_source_checks':base,'planner_E1_E10_exact_comparison':criteria_results,
  'full_plan_bundle_checksum_checks':sums,
  'gate3_experiment_executed':False,
  'filesystem_limits':{'symlink':'unit test skipped on Windows WinError 1314','junction':'not executed','TOCTOU':'not experimentally tested; documented limitation'}}
(evidence/'execution.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'command_exits':[x['exit_code'] for x in records],
 'candidate_hashes_match':all(x['match'] for y in summary['candidate_source_hash_checks'].values() for x in y),
 'frozen_unchanged':all(x['unchanged'] for x in base),
 'E_criteria_matches':[(x['id'],x['matches_frozen_or_erratum'],x['replacement_character_count']) for x in criteria_results],
 'bundle_checksum_mismatches':[x['path'] for x in sums if not x['match']]},ensure_ascii=False))
