from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHON = r"C:\Users\cupid\AppData\Local\Programs\Python\Python312\python.exe"
OUT = Path(__file__).resolve().parent
COMMANDS = [
    ("focused-contracts", ["-m", "unittest", "tests.test_contracts", "-v"]),
    ("complete-tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("receipt-app", ["-m", "unittest", "discover", "-s", "demo/receipt", "-p", "test_receipt_calculator.py", "-v"]),
    ("structured-app", ["-m", "unittest", "discover", "-s", "demo/structured-flow", "-p", "test_sum_values.py", "-v"]),
    ("deterministic-contracts", ["reports/councilflow-e10/tester/run_contracts.py"]),
]
def sha(data): return hashlib.sha256(data).hexdigest()
results=[]
for name,args in COMMANDS:
    proc=subprocess.run([PYTHON,*args],cwd=ROOT,capture_output=True,check=False)
    (OUT/f"{name}.stdout.bin").write_bytes(proc.stdout)
    (OUT/f"{name}.stderr.bin").write_bytes(proc.stderr)
    (OUT/f"{name}.exit.txt").write_text(str(proc.returncode)+"\n",encoding="ascii")
    normalized=proc.stdout.replace(b"\r\n",b"\n")
    results.append({"name":name,"executable":PYTHON,"arguments":args,"working_directory":str(ROOT),"exit_code":proc.returncode,"stdout_path":f"reports/councilflow-e10/tester-attempt-2/{name}.stdout.bin","stderr_path":f"reports/councilflow-e10/tester-attempt-2/{name}.stderr.bin","stdout_length":len(proc.stdout),"stdout_sha256_raw":sha(proc.stdout),"stdout_length_crlf_to_lf_only":len(normalized),"stdout_sha256_crlf_to_lf_only":sha(normalized),"stderr_sha256_raw":sha(proc.stderr)})
candidate_paths=[".agents/skills/council-flow/scripts/contracts.py","tests/test_contracts.py",".agents/skills/council-flow/references/workflow.md",".agents/skills/council-flow/references/communication.md","reports/councilflow-e10/tester/run_contracts.py"]
candidate={p:sha((ROOT/p).read_bytes()) for p in candidate_paths}
frozen_paths={"docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md":"e97053e51723ff40b7a328a10c3c5f759289869d2cc9dfb55dc3c1869bb2b523","docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md":"99812898178506eaf88afbc5b31005bf4772f775fef7e46bc633289815167be2","docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md":"4655f3425ed8a312c28b2324e8d5b6730d568bf5ab3aa8c4e2439d9d4d438d6e"}
frozen={p:{"expected":v,"sha256":sha((ROOT/p).read_bytes()),"matches":sha((ROOT/p).read_bytes())==v} for p,v in frozen_paths.items()}
summary={"role":"tester","protocol":"council-flow","version":"1.0","task":"Gate 3 E10 remediation, rework attempt 2","candidate_sha256":candidate,"frozen_spec_hashes":frozen,"commands":results,"all_commands_exit_zero":all(r["exit_code"]==0 for r in results),"fixture_provenance":"Synthetic test input only; no authentic Owner-approved CSV fixture was available. SHA-256 records integrity only, not approval.","gate3":"NOT RUN","csv_experiment":"NOT RUN","notes":["No product/test files were changed by Tester.","The deterministic stdout hash uses raw_stdout.replace(b'\\r\\n', b'\\n') only.","No CSV application test suite was run; only receipt and structured-flow demo suites were run."]}
(OUT/"tester-result.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps({"results":[{"name":r["name"],"exit":r["exit_code"],"tests_output_sha256":r["stdout_sha256_crlf_to_lf_only"]} for r in results],"frozen_match":all(x["matches"] for x in frozen.values()),"all_zero":summary["all_commands_exit_zero"]},indent=2))
