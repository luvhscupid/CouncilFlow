import hashlib,json
from pathlib import Path
root=Path('.')
report=(root/'docs/CouncilFlow-Full-Plan/examples/job.report.json').read_bytes()
report=report.replace(b'docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt',b'demo/receipt/receipt_calculator.py')
current_hash=(root/'docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt').read_bytes()
report=report.replace(hashlib.sha256(current_hash).hexdigest().encode(),b'0'*64)
expected_report='a27221ac7bc08519af93acb9681e10223c7d9ff4d7ba69897238c11b9d695596'
report_hash=hashlib.sha256(report).hexdigest()
print(json.dumps({'job_report_reconstruction_matches':report_hash==expected_report,'expected':expected_report,'actual':report_hash}))
if report_hash==expected_report:
 p=root/'reports/councilflow-hardening/worker-final/reconstructed/A001/docs/CouncilFlow-Full-Plan/examples/job.report.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(report)
sums=(root/'docs/CouncilFlow-Full-Plan/SHA256SUMS.txt').read_bytes()
sums=sums.replace(hashlib.sha256((root/'docs/CouncilFlow-Full-Plan/examples/job.report.json').read_bytes()).hexdigest().encode(),expected_report.encode())
lines=[line for line in sums.splitlines(keepends=True) if b'  examples/synthetic-candidate.txt' not in line]
sums=b''.join(lines)
expected_sums='769866090c81a20da1e9315d83c4296f1959a82fff36c6d122ce24f6b326249b'
sums_hash=hashlib.sha256(sums).hexdigest()
print(json.dumps({'sha256sums_reconstruction_matches':sums_hash==expected_sums,'expected':expected_sums,'actual':sums_hash}))
if sums_hash==expected_sums:
 p=root/'reports/councilflow-hardening/worker-final/reconstructed/A001/docs/CouncilFlow-Full-Plan/SHA256SUMS.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(sums)
