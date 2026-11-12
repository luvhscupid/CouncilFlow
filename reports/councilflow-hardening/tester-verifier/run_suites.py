import hashlib, json, os, subprocess, sys
from pathlib import Path
root=Path.cwd()
out=root/'reports/councilflow-hardening/tester-verifier'
commands=[
 ['-m','unittest','discover','-s','tests','-v'],
 ['-m','unittest','discover','-s','demo/receipt','-v'],
 ['-m','unittest','discover','-s','demo/csv-summary','-v'],
 ['-m','unittest','discover','-s','demo/structured-flow','-v'],
 ['-m','unittest','discover','-s','reports/demo/verification','-v'],
 ['-m','unittest','discover','-s','reports/csv-summary/verification','-v'],
 ['-m','unittest','discover','-s','reports/restoration/verification/initial','-v'],
 ['-m','unittest','discover','-s','reports/restoration/verification/final','-v'],
]
results=[]
for i,args in enumerate(commands,1):
    p=subprocess.run([sys.executable,*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out/f'suite-{i}.stdout.bin').write_bytes(p.stdout)
    (out/f'suite-{i}.stderr.bin').write_bytes(p.stderr)
    normalized=p.stdout.replace(b'\r\n',b'\n')
    results.append({'suite':args[4] if len(args)>4 else str(i),'command':str(Path(sys.executable).resolve()),'arguments':args,'working_directory':str(root.resolve()),'candidate_id':'CFH-CANDIDATE-A004','candidate_manifest_sha256':hashlib.sha256((root/'reports/councilflow-hardening/worker-final/candidate-manifest.json').read_bytes()).hexdigest(),'input_candidate_id':'CFH-CURRENT-BASE-A002','input_manifest_sha256':hashlib.sha256((root/'reports/councilflow-hardening/manager/base-candidate-a002.json').read_bytes()).hexdigest(),'exit_code':p.returncode,'stdout_sha256_crlf_to_lf_only':hashlib.sha256(normalized).hexdigest(),'stderr_sha256_raw':hashlib.sha256(p.stderr).hexdigest(),'stdout_evidence':f'reports/councilflow-hardening/tester-verifier/suite-{i}.stdout.bin','stderr_evidence':f'reports/councilflow-hardening/tester-verifier/suite-{i}.stderr.bin','stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr)})
    print(i,p.returncode,results[-1]['stdout_sha256_crlf_to_lf_only'], 'stdout',len(p.stdout),'stderr',len(p.stderr))
(out/'suite-executions.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
