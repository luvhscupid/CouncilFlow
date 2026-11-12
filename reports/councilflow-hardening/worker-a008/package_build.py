from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path.cwd(); OUT=ROOT/'reports/councilflow-hardening/worker-a008'; OUT.mkdir(parents=True,exist_ok=True)
DIST=ROOT/'dist'; DIST.mkdir(exist_ok=True); ARCH=DIST/'council-flow.zip'; SUM=DIST/'council-flow.zip.sha256'
def sha(b): return hashlib.sha256(b).hexdigest()
def safe(n):
 if '\\' in n: return False
 p=PurePosixPath(n)
 return not p.is_absolute() and bool(p.parts) and all(x not in ('','.','..') for x in p.parts) and not (len(p.parts[0])>1 and p.parts[0][1]==':')
def excluded(n):
 p=[x.lower() for x in n.split('/')]
 return (any(x in {'.git','__pycache__','.pytest_cache','.codex-runtime','.codebase-memory','runtime','credentials','secrets'} for x in p)
  or any(x.endswith(('.pyc','.pyo','.tmp','.temp')) for x in p)
  or any(x in {'.env','.env.local','credentials.json','token.json'} for x in p)
  or 'councilflow-hardening' in p)
def walk(rel, out):
 base=ROOT/rel
 if not base.is_dir(): raise RuntimeError(f'missing allowlisted dir {rel}')
 for f in base.rglob('*'):
  if f.is_dir(): continue
  if f.is_symlink(): raise RuntimeError(f'symlink in allowlist {f}')
  n=f.relative_to(ROOT).as_posix()
  if not excluded(n): out.add(n)
entries=set()
for n in ['README.md','RELEASE.md']: entries.add(n)
for d in ['.agents/skills/council-flow','demo','tests','docs/gate3/CouncilFlow-Gate3-v0.2','docs/CouncilFlow-Full-Plan','reports/demo','reports/csv-summary']: walk(d,entries)
for n in ['docs/gate3/README.md','reports/final.md','reports/requirements-traceability.md','reports/gate3b-results.md']: entries.add(n)
agents=sorted((ROOT/'.codex/agents').glob('council-*.toml'))
if len(agents)!=4: raise RuntimeError(f'expected four native TOML files, got {len(agents)}')
entries.update(f.relative_to(ROOT).as_posix() for f in agents)
for n in entries:
 if not safe(n) or excluded(n): raise RuntimeError(f'unsafe/forbidden allowlist path {n}')
files=[]
for n in sorted(entries):
 b=(ROOT/Path(*n.split('/'))).read_bytes(); files.append({'path':n,'sha256':sha(b),'size':len(b)})
with zipfile.ZipFile(ARCH,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for row in files:
  info=zipfile.ZipInfo(row['path'],date_time=(2020,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
  z.writestr(info,(ROOT/Path(*row['path'].split('/'))).read_bytes())
archive=ARCH.read_bytes(); archive_sha=sha(archive); SUM.write_text(f'{archive_sha}  council-flow.zip\n',encoding='ascii',newline='\n')
required={'.agents/skills/council-flow/SKILL.md','.agents/skills/council-flow/scripts/contracts.py','.agents/skills/council-flow/policies/roles.yaml','README.md','RELEASE.md','docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md','docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md','docs/CouncilFlow-Full-Plan/README.md','tests/test_contracts.py','demo/receipt/receipt_calculator.py'}
with zipfile.ZipFile(ARCH) as z:
 names=z.namelist()
 if len(names)!=len(set(names)) or z.testzip() is not None: raise RuntimeError('duplicate entries or bad CRC')
 if not required.issubset(names): raise RuntimeError(f'missing required entries {required-set(names)}')
 if any(not safe(n) or excluded(n) or n.startswith(('reports/runtime/','reports/councilflow-hardening/')) or n=='dist/council-flow.zip' for n in names): raise RuntimeError('unsafe/forbidden archive path')
 for row in files:
  b=z.read(row['path'])
  if len(b)!=row['size'] or sha(b)!=row['sha256']: raise RuntimeError(f'archive/worktree mismatch {row["path"]}')
commands=[]
with tempfile.TemporaryDirectory(prefix='councilflow-a008-extract-') as t:
 temp=Path(t)
 with zipfile.ZipFile(ARCH) as z: z.extractall(temp)
 suites=[['-m','unittest','discover','-s',s,'-v'] for s in ['tests','demo/receipt','demo/csv-summary','demo/structured-flow','reports/demo/verification','reports/csv-summary/verification']]
 suites += [['.agents/skills/council-flow/scripts/contracts.py','message',f'docs/CouncilFlow-Full-Plan/examples/{f}','--root','.'] for f in ['job.assign.json','job.report.json']]
 for i,args in enumerate(suites,1):
  p=subprocess.run([sys.executable,*args],cwd=temp,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
  op=OUT/f'extracted-command-{i}.stdout.bin'; ep=OUT/f'extracted-command-{i}.stderr.bin';op.write_bytes(p.stdout);ep.write_bytes(p.stderr)
  row={'name':f'extracted-command-{i}','command':sys.executable,'arguments':args,'working_directory':str(temp),'exit_code':p.returncode,'stdout_sha256_crlf_to_lf_only':sha(p.stdout.replace(b'\r\n',b'\n')),'stderr_sha256_raw':sha(p.stderr),'stdout_path':str(op.relative_to(ROOT)).replace('\\','/'),'stderr_path':str(ep.relative_to(ROOT)).replace('\\','/'),'summary':(p.stderr or p.stdout).decode('utf-8','replace').strip().splitlines()[-1] if (p.stderr or p.stdout) else ''}
  commands.append(row)
  if p.returncode: raise RuntimeError(f'package extracted check failed: {args}: {p.returncode}')
priorp=ROOT/'reports/councilflow-hardening/worker-a007/candidate-manifest.json'; prior=json.loads(priorp.read_text(encoding='utf-8'))
cum={r['path']:r for r in prior['files']}
for n in ['RELEASE.md','dist/council-flow.zip','dist/council-flow.zip.sha256']:
 b=(ROOT/Path(*n.split('/'))).read_bytes();cum[n]={'path':n,'sha256':sha(b),'size':len(b)}
manifest={'candidate_id':'CFH-CANDIDATE-A008','plan_id':'CFH-P004','plan_revision':1,'task_id':'CFH-T004','attempt_id':'CFH-A008','baseline_commit':'2d695a22a1bb596a527b0d118edc073d6d25553f','input_candidate_ref':{'artifact_id':'CFH-CANDIDATE-A007','path':'reports/councilflow-hardening/worker-a007/candidate-manifest.json','sha256':sha(priorp.read_bytes()),'kind':'candidate-manifest'},'files':[cum[k] for k in sorted(cum)],'distribution_archive':{'path':'dist/council-flow.zip','sha256':archive_sha,'size':len(archive),'entry_count':len(entries)}}
mp=OUT/'candidate-manifest.json'; snap=OUT/'candidate-snapshot.zip'
# Snapshot includes the package outputs and all cumulative source bytes.
with zipfile.ZipFile(snap,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for row in manifest['files']:
  info=zipfile.ZipInfo(row['path'],date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,(ROOT/Path(*row['path'].split('/'))).read_bytes())
with zipfile.ZipFile(snap) as z:
 if z.testzip() is not None: raise RuntimeError('candidate snapshot CRC failure')
 for row in manifest['files']:
  if sha(z.read(row['path']))!=row['sha256']: raise RuntimeError(f'candidate snapshot mismatch: {row["path"]}')
snap_sha=sha(snap.read_bytes());manifest['snapshot_ref']={'artifact_id':'CFH-A008-SOURCE-SNAPSHOT','path':'reports/councilflow-hardening/worker-a008/candidate-snapshot.zip','kind':'source-snapshot','sha256':snap_sha}
mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); manifest_sha=sha(mp.read_bytes())
execd={'protocol':'council-flow','version':'1.0','candidate_id':'CFH-CANDIDATE-A008','manifest_path':'reports/councilflow-hardening/worker-a008/candidate-manifest.json','manifest_sha256':manifest_sha,'snapshot_path':'reports/councilflow-hardening/worker-a008/candidate-snapshot.zip','snapshot_sha256':snap_sha,'archive_path':'dist/council-flow.zip','archive_sha256':archive_sha,'archive_entry_count':len(entries),'crc_valid':True,'safe_paths':True,'all_packaged_hashes_match_worktree':True,'extracted_checks':commands,'note':'Package verification evidence is outside the archive to avoid self-reference; this does not establish native activation.'}
(OUT/'execution.json').write_text(json.dumps(execd,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
verify={'archive':'dist/council-flow.zip','sha256':archive_sha,'checksum_file':'dist/council-flow.zip.sha256','entry_count':len(entries),'crc':'PASS','safe_paths':'PASS','required_contents':'PASS','forbidden_contents_absent':'PASS','all_bytes_match_worktree':'PASS','checksum_matches':SUM.read_text(encoding='ascii').strip()==f'{archive_sha}  council-flow.zip','extracted_checks':commands,'historical_reports_only':'PASS','current_hardening_evidence_excluded':True}
(OUT/'package-verification.json').write_text(json.dumps(verify,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'archive':str(ARCH),'sha256':archive_sha,'entries':len(entries),'candidate_manifest_sha256':manifest_sha,'snapshot_sha256':snap_sha,'extracted_commands':len(commands)},indent=2))
