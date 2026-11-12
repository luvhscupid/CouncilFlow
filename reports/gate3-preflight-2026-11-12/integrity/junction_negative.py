from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import sys


ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts


base = Path(tempfile.mkdtemp(prefix="councilflow-junction-"))
authorized = base / "authorized"
outside = base / "outside"
authorized.mkdir()
outside.mkdir()
target = outside / "evidence.txt"
target.write_bytes(b"correct junction target evidence\n")
junction = authorized / "escape"
command = [
    "powershell", "-NoProfile", "-Command",
    f"New-Item -ItemType Junction -Path '{junction}' -Target '{outside}' | Out-Null",
]
created = subprocess.run(command, capture_output=True)
record = {
    "method": "isolated Windows directory junction/reparse-point negative control",
    "authorized_root": str(authorized),
    "outside_target": str(target),
    "junction_path": str(junction),
    "creation_command": command,
    "creation_exit_code": created.returncode,
    "creation_stdout_raw": created.stdout.decode("utf-8", "replace"),
    "creation_stderr_raw": created.stderr.decode("utf-8", "replace"),
    "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "toctou_or_os_sandbox_claim": False,
}
if created.returncode != 0 or not junction.is_dir():
    record["status"] = "UNVERIFIED"
    record["reason"] = "junction/reparse-point creation was unavailable; see exact captured command output"
else:
    value = {
        "artifact_id": "junction-negative-control",
        "path": "escape/evidence.txt",
        "sha256": record["target_sha256"],
        "kind": "test-fixture",
    }
    try:
        contracts.artifact(value, authorized)
    except contracts.ContractError as exc:
        record["validator_error_code"] = exc.code
        record["validator_error"] = str(exc)
        record["status"] = "PASS" if exc.code == "artifact_path" else "FAIL"
    else:
        record["status"] = "FAIL"
        record["reason"] = "validator accepted a digest-correct target outside the authorized root"
output = ROOT / "reports/gate3-preflight-2026-11-12/integrity/junction-negative.json"
output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(record, indent=2, ensure_ascii=False))
