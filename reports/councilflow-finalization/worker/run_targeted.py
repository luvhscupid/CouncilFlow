from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
commands = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_contracts.py", "-k", "tester_command_and_reviewer_rerun_artifacts_must_be_top_level_refs", "-v"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_codebase_memory_integration.py", "-v"],
]
rows = []
for index, command in enumerate(commands, start=1):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    stem = f"targeted-{index}"
    stdout_path = OUT / f"{stem}.stdout.bin"
    stderr_path = OUT / f"{stem}.stderr.bin"
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    rows.append({
        "command": sys.executable,
        "arguments": command[1:],
        "working_directory": str(ROOT),
        "exit_code": result.returncode,
        "stdout_sha256_crlf_to_lf_only": hashlib.sha256(result.stdout.replace(b"\r\n", b"\n")).hexdigest(),
        "stderr_sha256_raw": hashlib.sha256(result.stderr).hexdigest(),
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
    })
    if result.returncode:
        raise SystemExit(result.returncode)
report = {"results": rows, "all_passed": all(row["exit_code"] == 0 for row in rows)}
report_path = OUT / "targeted-execution.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
