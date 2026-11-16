"""Independent Windows-local integration checks. Evidence only; no product edits."""
import argparse, hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/integration-gate3-efficiency'
PY=str(Path(sys.executable).resolve())
def sha(data): return hashlib.sha256(data).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
 out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=False)
 records=[]; observations={}
 def write(name,data): (out/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
 def run(name,arguments,cwd=ROOT,env=None):
  result=subprocess.run([PY,*arguments],cwd=cwd,env=env,capture_output=True,timeout=300)
  (out/(name+'.stdout')).write_bytes(result.stdout); (out/(name+'.stderr')).write_bytes(result.stderr)
  text=result.stderr.decode('utf-8',errors='replace')
  row={'name':name,'command':PY,'arguments':arguments,'workdir':str(cwd),'exit_code':result.returncode,'stdout_sha256':sha(result.stdout.replace(b'\r\n',b'\n')),'stdout_file':name+'.stdout','stderr_file':name+'.stderr','summary':text[-600:]}
  records.append(row); write('executions.json',records); print(json.dumps({'name':name,'exit':result.returncode,'summary':text[-110:]}),flush=True)
  if result.returncode: raise RuntimeError('failed '+name)
  return row
 def verify_manifest():
  c=json.loads((BASE/'worker/candidate.json').read_text())
  assert sha((BASE/'worker/candidate.json').read_bytes())=='2d00a9d6249925115efe0edae93dc01a10196d8b56c7105c5a63e77c28b60d45'
  for item in c['files']: assert sha((ROOT/item['path']).read_bytes())==item['sha256'],item['path']
  for name in c['deleted_paths']: assert not (ROOT/name).exists(),name
  return len(c['files'])
 observations['candidate_files_before']=verify_manifest()
 oracle=json.loads((BASE/'oracle.json').read_text())
 for item in oracle['files']: assert sha((BASE/'oracle'/item['path']).read_bytes())==item['sha256'],item['path']
 protected=json.loads((BASE/'preservation-before.json').read_text())['protected']
 for item in protected: assert sha(Path(item['path']).read_bytes())==item['sha256'],item['path']
 observations['protected_external_files']=len(protected)
 for item in oracle['files']:
  if item['path'].startswith(('docs/gate3/','.codex/agents/')): assert sha((ROOT/item['path']).read_bytes())==item['sha256'],item['path']
 observations['oracle_files']=len(oracle['files']); write('observations.json',observations)
 # Fresh original suites receive the candidate runtime, never the archived old runtime.
 with tempfile.TemporaryDirectory(prefix='councilflow-pristine-') as d:
  stage=Path(d); old=BASE/'oracle/experiments/agent-efficiency'; suite=stage/'efficiency'; suite.mkdir()
  for name in ('test_recorder.py','test_digest.py','test_codex_adapter.py','test_claude_adapter.py'): shutil.copyfile(old/name,suite/name)
  shutil.copytree(old/'fixtures',suite/'fixtures')
  env={**os.environ,'PYTHONPATH':str(ROOT/'.agents/skills/council-flow/scripts/efficiency')}
  run('pristine-efficiency',['-B','-m','unittest','discover','-s',str(suite),'-v'],env=env)
  # Stage release source and overlay original behavior/contract tests only.
  spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build_release.py'); builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
  sources=builder.source_bytes(ROOT); core=stage/'core'
  for name,data in sources.items():
   p=core/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
  original_tests=BASE/'oracle/tests'
  for name in ('test_contracts.py','test_original_source.py','test_workflow_recovery.py','test_codebase_memory_integration.py','test_release.py'): shutil.copyfile(original_tests/name,core/'tests'/name)
  for name in ('test_contracts','test_original_source','test_workflow_recovery','test_codebase_memory_integration','test_release'):
   run('pristine-'+name,['-B','-m','unittest','discover','-s','tests','-p',name+'.py','-v'],cwd=core)
  gate=stage/'gate'; app=gate/'demo/gate3-demo/app.py'; app.parent.mkdir(parents=True)
  shutil.copyfile(ROOT/'demo/gate3-demo/app.py',app); original=BASE/'oracle/gate3'
  shutil.copyfile(original/'demo/gate3-demo/test_app.py',app.with_name('test_app.py')); shutil.copytree(original/'owner-fixtures',gate/'owner-fixtures')
  run('pristine-gate3',['-B','-m','unittest','discover','-s',str(app.parent),'-v'],cwd=gate)
 suites=['tests','demo/gate3-demo','demo/receipt','demo/csv-summary','demo/structured-flow','reports/demo/verification','reports/csv-summary/verification']
 for i,suite in enumerate(suites): run('checkout-%02d'%i,['-B','-m','unittest','discover','-s',suite,'-v'])
 run('package-d-offline',['-B','-m','unittest','discover','-s','experiments/agent-efficiency','-v'])
 run('release-build',['tools/build_release.py']); first=(ROOT/'dist/council-flow.zip').read_bytes()
 run('release-rebuild',['tools/build_release.py']); assert (ROOT/'dist/council-flow.zip').read_bytes()==first
 manifest=json.loads((ROOT/'dist/council-flow.manifest.json').read_text())
 assert sha(first)==manifest['sha256']==(ROOT/'dist/council-flow.zip.sha256').read_text().split()[0]
 with tempfile.TemporaryDirectory(prefix='councilflow-extracted-') as d:
  extracted=Path(d)/'extracted'; sources=builder.source_bytes(ROOT)
  with zipfile.ZipFile(ROOT/'dist/council-flow.zip') as z:
   assert z.testzip() is None; assert set(z.namelist())==set(sources)
   for name in z.namelist():
    assert builder.safe_name(name) and not builder.excluded(name),name
    assert not name.startswith(('experiments/','owner-fixtures/','reports/integration-','reports/gate3-preparation/')),name
    assert z.read(name)==sources[name],name
   z.extractall(extracted)
  for i,suite in enumerate(suites): run('extracted-%02d'%i,['-B','-m','unittest','discover','-s',suite,'-v'],cwd=extracted)
 observations.update({'release_sha256':sha(first),'archive_entries':len(sources),'crc':'PASS','source_bytes':'PASS','deterministic_rebuild':'PASS','extracted_suites':'PASS','candidate_files_after':verify_manifest(),'pristine_static_limit':'Original test_skill_files.py blanket local-import ban superseded by authorized runtime relocation; current narrowed static guard executed in core suite. All original behavioral checks independently executed.'})
 # This exact command is suitable for Reviewer rerun.
 row=run('deterministic-csv',['-B','demo/gate3-demo/app.py','demo/gate3-demo/inputs/amount.csv','amount'])
 assert (out/'deterministic-csv.stdout').read_bytes()==b'5\r\n' or (out/'deterministic-csv.stdout').read_bytes()==b'5\n'
 observations['deterministic_command']=row
 for item in protected: assert sha(Path(item['path']).read_bytes())==item['sha256'],item['path']
 write('observations.json',observations); print(json.dumps({'status':'PASS','executions':len(records),'release_sha256':sha(first)}),flush=True)
if __name__=='__main__': main()
