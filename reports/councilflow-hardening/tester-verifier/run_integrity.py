import hashlib,json,re,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
root=Path.cwd(); d=root/'reports/councilflow-hardening/tester-verifier'; d.mkdir(exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def run(name,args):
 p=subprocess.run([sys.executable,*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (d/f'{name}.stdout.bin').write_bytes(p.stdout); (d/f'{name}.stderr.bin').write_bytes(p.stderr)
 return {'name':name,'command':str(Path(sys.executable).resolve()),'arguments':args,'working_directory':str(root.resolve()),'candidate_ref':{'artifact_id':'CFH-CANDIDATE-A004','path':'reports/councilflow-hardening/worker-final/candidate-manifest.json','sha256':sha((root/'reports/councilflow-hardening/worker-final/candidate-manifest.json').read_bytes()),'kind':'candidate-manifest'},'input_refs':[{'artifact_id':'CFH-CURRENT-BASE-A002','path':'reports/councilflow-hardening/manager/base-candidate-a002.json','sha256':sha((root/'reports/councilflow-hardening/manager/base-candidate-a002.json').read_bytes()),'kind':'candidate-manifest'}],'exit_code':p.returncode,'stdout_sha256_crlf_to_lf_only':sha(p.stdout.replace(b'\r\n',b'\n')),'stderr_sha256_raw':sha(p.stderr),'stdout_evidence':f'reports/councilflow-hardening/tester-verifier/{name}.stdout.bin','stderr_evidence':f'reports/councilflow-hardening/tester-verifier/{name}.stderr.bin','stdout_raw':p.stdout.decode('utf-8','replace'),'stderr_raw':p.stderr.decode('utf-8','replace')}
assign_args=['.agents/skills/council-flow/scripts/contracts.py','message','docs/CouncilFlow-Full-Plan/examples/job.assign.json','--root','.']
report_args=['.agents/skills/council-flow/scripts/contracts.py','message','docs/CouncilFlow-Full-Plan/examples/job.report.json','--root','.']
neg=json.loads((root/'docs/CouncilFlow-Full-Plan/examples/job.report.json').read_text(encoding='utf-8'))
neg['payload']['candidate_ref']['sha256']='0'*64
negp=d/'stale-job-report.json'; negp.write_text(json.dumps(neg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
seqargs=['.agents/skills/council-flow/scripts/contracts.py','sequence','reports/councilflow-hardening/planner-correction-p004/plan-publish.json','reports/councilflow-hardening/manager/worker-final-assign.json','reports/councilflow-hardening/worker-final/job-report.json','reports/councilflow-hardening/manager/tester-final-assign.json','--root','.']
commands=[run('example-job-assign',assign_args),run('example-job-report',report_args),run('example-stale-negative',['.agents/skills/council-flow/scripts/contracts.py','message',str(negp.relative_to(root)),'--root','.']),run('p004-context-sequence',seqargs)]
manifest_path=root/'reports/councilflow-hardening/worker-final/candidate-manifest.json'; mbytes=manifest_path.read_bytes(); manifest=json.loads(mbytes); ex=json.loads((root/'reports/councilflow-hardening/worker-final/execution.json').read_text(encoding='utf-8'))
files=[]
for x in manifest['files']:
 p=PurePosixPath(x['path']); full=root.joinpath(*p.parts); b=full.read_bytes(); files.append({'path':x['path'],'manifest_sha256':x['sha256'],'actual_sha256':sha(b),'size_expected':x['size'],'size_actual':len(b),'matches':x['sha256']==sha(b) and x['size']==len(b)})
zpath=root/manifest['snapshot_ref']['path']; zbytes=zpath.read_bytes(); zipfiles=[]; crc=[]
with zipfile.ZipFile(zpath) as z:
 crc=z.testzip();
 for i in z.infolist():
  n=i.filename; p=PurePosixPath(n); b=z.read(i); zipfiles.append({'path':n,'size':i.file_size,'sha256':sha(b),'safe':not p.is_absolute() and '..' not in p.parts and not n.startswith(('\\','/')),'excluded': any(s in n.lower() for s in ['.git/','__pycache__/','.pyc','.pytest_cache/','.mypy_cache/','/tmp/','\\temp\\'])})
# checksums format conventional sha256<2 spaces>path
sumfile=root/'docs/CouncilFlow-Full-Plan/SHA256SUMS.txt'; sums=[]
for line in sumfile.read_text(encoding='utf-8').splitlines():
 if not line.strip(): continue
 h,path=line.split(None,1); path=path.lstrip('* '); f=root/'docs/CouncilFlow-Full-Plan'/path
 sums.append({'path':path,'expected':h,'actual':sha(f.read_bytes()) if f.is_file() else None,'matches':f.is_file() and h==sha(f.read_bytes())})
# E1-E10 compare extracted normalized section bodies against P004. Remove markdown heading marks only; exact remaining text.
plan=json.loads((root/'reports/councilflow-hardening/planner-correction-p004/plan.json').read_text(encoding='utf-8')); ac={x['id']:x['criterion'] for x in plan['acceptance']}
frozen=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md').read_text(encoding='utf-8').replace('\r\n','\n')
c3=(root/'docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md').read_text(encoding='utf-8').replace('\r\n','\n')
def section(text, eid):
 m=re.search(r'(?m)^#{2,4} '+eid+r' —[^\n]*\n',text)
 if not m: return None
 tail=text[m.end():]; n=re.search(r'(?m)^#{2,4} ',tail)
 body=tail[:n.start()] if n else tail
 return body.strip()
def criterionbody(c):
 return c.split('\n',1)[1].strip()
criteria=[]
for eid in [f'E{i}' for i in range(1,11)]:
 src=section(c3 if eid=='E4' else frozen,eid)
 planned=criterionbody(ac[eid])
 criteria.append({'id':eid,'planned_matches_canonical_body_exact':planned==src,'planned_sha256':sha(planned.encode()),'canonical_sha256':sha(src.encode()) if src is not None else None,'canonical_source':'docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md' if eid=='E4' else 'docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md','has_source':src is not None})
# worker execution hash conflicts
exec_checks={'execution_top_manifest_sha256':ex.get('manifest_sha256'),'execution_candidate_manifest_sha256':ex.get('candidate_manifest_sha256'),'recomputed_manifest_sha256':sha(mbytes),'assignment_expected_manifest_sha256':'6a0f0fad405da97cee6fc76f17afbfc78814a8f8e6ddcc2267ffa84834affcf9','execution_top_matches_recomputed':ex.get('manifest_sha256')==sha(mbytes),'execution_candidate_field_matches_recomputed':ex.get('candidate_manifest_sha256')==sha(mbytes),'snapshot_expected_sha256':manifest['snapshot_ref']['sha256'],'snapshot_actual_sha256':sha(zbytes),'snapshot_matches':sha(zbytes)==manifest['snapshot_ref']['sha256'],'worker_execution_zip_crc_valid_field':ex.get('zip_crc_valid'),'worker_execution_extracted_hashes_match_field':ex.get('extracted_hashes_match')}
result={'commands':commands,'manifest_sha256':sha(mbytes),'manifest_file_checks':files,'manifest_all_match':all(x['matches'] for x in files),'snapshot_sha256':sha(zbytes),'snapshot_matches_manifest':sha(zbytes)==manifest['snapshot_ref']['sha256'],'snapshot_zip_crc_error':crc,'snapshot_paths':zipfiles,'snapshot_paths_safe':all(x['safe'] for x in zipfiles),'snapshot_excluded_metadata_present':[x['path'] for x in zipfiles if x['excluded']],'snapshot_entries_equal_manifest_paths':set(x['path'] for x in zipfiles)==set(x['path'] for x in manifest['files']),'full_plan_checksums':sums,'full_plan_checksums_all_match':all(x['matches'] for x in sums),'criteria':criteria,'criteria_all_exact':all(x['planned_matches_canonical_body_exact'] for x in criteria),'worker_execution_hash_audit':exec_checks}
(d/'integrity-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for c in commands: print(c['name'],c['exit_code'],c['stdout_sha256_crlf_to_lf_only'],c['stderr_raw'][:160].replace('\n',' | '))
print('manifest',result['manifest_sha256'],result['manifest_all_match'],'snapshot',result['snapshot_matches_manifest'],result['snapshot_zip_crc_error'],result['snapshot_paths_safe'],'excluded',result['snapshot_excluded_metadata_present'])
print('checksums',len(sums),result['full_plan_checksums_all_match'],'criteria',[(x['id'],x['planned_matches_canonical_body_exact']) for x in criteria])
print('worker-hash-audit',json.dumps(exec_checks))
