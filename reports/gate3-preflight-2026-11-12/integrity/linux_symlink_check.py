from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "dist/council-flow.zip"
RUN = ROOT / "reports/gate3-preflight-2026-11-12/integrity"
archive_sha = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
extract = Path(tempfile.mkdtemp(prefix="councilflow-linux-extract-"))
with zipfile.ZipFile(ARCHIVE) as archive:
    archive.extractall(extract)

arguments = [
    "-m", "unittest",
    "tests.test_contracts.JSONContractTests.test_artifact_path_shape",
    "tests.test_contracts.JSONContractTests.test_artifact_stale_digest_is_rejected",
    "tests.test_contracts.JSONContractTests.test_artifact_in_root_symlink_is_allowed_when_supported",
    "tests.test_contracts.JSONContractTests.test_artifact_symlink_escape_is_rejected_when_supported",
    "-v",
]
process = subprocess.run(
    [sys.executable, *arguments], cwd=extract, capture_output=True, check=False
)
(RUN / "linux-symlink.stdout.bin").write_bytes(process.stdout)
(RUN / "linux-symlink.stderr.bin").write_bytes(process.stderr)
stderr = process.stderr.decode("utf-8", "replace")
summary = [line for line in stderr.splitlines() if line.startswith("Ran ") or line.startswith("OK") or line.startswith("FAILED")]
record = {
    "platform": platform.platform(),
    "python": sys.version,
    "executable": sys.executable,
    "arguments": arguments,
    "cwd": str(extract),
    "candidate_sha256": archive_sha,
    "exit_code": process.returncode,
    "stdout_path": "reports/gate3-preflight-2026-11-12/integrity/linux-symlink.stdout.bin",
    "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
    "stderr_path": "reports/gate3-preflight-2026-11-12/integrity/linux-symlink.stderr.bin",
    "stderr_sha256": hashlib.sha256(process.stderr).hexdigest(),
    "summary": summary,
    "symlink_skips": sum("skipped" in line.lower() for line in stderr.splitlines()),
    "status": "PASS" if process.returncode == 0 and "OK" in stderr and "skipped=" not in stderr else "FAIL",
    "extraction_path": str(extract),
    "scope_limit": "Focused path tests only; this is not an OS sandbox or TOCTOU test.",
}
(RUN / "linux-symlink.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(record, indent=2, ensure_ascii=False))
