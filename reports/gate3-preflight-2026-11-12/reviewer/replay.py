from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath


ROOT = Path.cwd().resolve()
RUN = ROOT / "reports/gate3-preflight-2026-11-12/reviewer"
TESTER_REPORT_PATH = ROOT / "reports/gate3-preflight-2026-11-12/tester/tester-result.json"
tester = json.loads(TESTER_REPORT_PATH.read_text(encoding="utf-8"))
declared = tester["deterministic_command"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


candidate_path = ROOT / declared["candidate_ref"]["path"]
candidate_sha = digest(candidate_path.read_bytes())
cwd = Path(declared["working_directory"])
input_checks = []
for ref in declared["input_refs"]:
    path = cwd.joinpath(*PurePosixPath(ref["path"]).parts)
    actual = digest(path.read_bytes())
    input_checks.append({
        "path": ref["path"],
        "expected_sha256": ref["sha256"],
        "actual_sha256": actual,
        "matches": actual == ref["sha256"],
    })

execution = subprocess.run(
    [declared["command"], *declared["arguments"]],
    cwd=cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)
stdout_path = RUN / "reviewer-rerun.stdout.bin"
stderr_path = RUN / "reviewer-rerun.stderr.bin"
stdout_path.write_bytes(execution.stdout)
stderr_path.write_bytes(execution.stderr)
normalized = execution.stdout.replace(b"\r\n", b"\n")
reviewer_normalized_sha = digest(normalized)
tester_stdout = ROOT.joinpath(*PurePosixPath(declared["evidence_ref"]["path"]).parts)
tester_stderr = ROOT.joinpath(*PurePosixPath(tester["evidence_refs"][1]["path"]).parts)
tester_raw_stdout = tester_stdout.read_bytes()
tester_raw_stderr = tester_stderr.read_bytes()
reference_checks = {
    "nested_and_top_level_stdout_refs_equal": declared["evidence_ref"] == declared["top_level_evidence_ref"],
    "nested_stdout_ref_matches_bytes": digest(tester_raw_stdout) == declared["evidence_ref"]["sha256"],
    "nested_stderr_ref_matches_bytes": digest(tester_raw_stderr) == declared["stderr_sha256_raw"],
    "top_level_stdout_ref_matches_bytes": digest(tester_raw_stdout) == declared["top_level_evidence_ref"]["sha256"],
}
result = {
    "record_type": "independent-native-reviewer-technical-result",
    "format": "UTF-8 JSON",
    "role": "reviewer",
    "native_instance": "/root/reviewer",
    "council_flow_envelope": "NOT EMITTED: no real task/attempt/message IDs or approved oracle_ref were supplied; none invented.",
    "tester_report": {
        "path": TESTER_REPORT_PATH.relative_to(ROOT).as_posix(),
        "sha256": digest(TESTER_REPORT_PATH.read_bytes()),
    },
    "candidate": {
        "path": declared["candidate_ref"]["path"],
        "expected_sha256": declared["candidate_ref"]["sha256"],
        "actual_sha256": candidate_sha,
        "matches": candidate_sha == declared["candidate_ref"]["sha256"],
    },
    "independent_rerun": {
        "executable": declared["command"],
        "arguments": declared["arguments"],
        "working_directory": str(cwd),
        "candidate_sha256": candidate_sha,
        "input_refs": declared["input_refs"],
        "input_checks": input_checks,
        "exit_code": execution.returncode,
        "stdout_raw_path": stdout_path.relative_to(ROOT).as_posix(),
        "stdout_sha256_raw": digest(execution.stdout),
        "stdout_sha256_crlf_to_lf_only": reviewer_normalized_sha,
        "stderr_raw_path": stderr_path.relative_to(ROOT).as_posix(),
        "stderr_sha256_raw": digest(execution.stderr),
        "tester_exit_code": declared["exit_code"],
        "tester_stdout_sha256_raw": declared["stdout_sha256_raw"],
        "tester_stdout_sha256_crlf_to_lf_only": declared["stdout_sha256_crlf_to_lf_only"],
        "exit_matches": execution.returncode == declared["exit_code"],
        "normalized_stdout_matches": reviewer_normalized_sha == declared["stdout_sha256_crlf_to_lf_only"],
        "command_evidence_ref": {
            "path": stdout_path.relative_to(ROOT).as_posix(),
            "sha256": digest(execution.stdout),
            "kind": "execution-output",
        },
    },
    "tester_command_reference_checks": reference_checks,
    "comparison": {
        "status": "MATCH" if execution.returncode == declared["exit_code"] and reviewer_normalized_sha == declared["stdout_sha256_crlf_to_lf_only"] else "MISMATCH",
        "scope": "Repeatability for this single declared command and exact bindings only.",
        "gate3_outcome": "NOT CLAIMED; this is not a Gate 3 observation.",
    },
    "evidence_refs": [
        {"path": stdout_path.relative_to(ROOT).as_posix(), "sha256": digest(execution.stdout), "kind": "execution-output"},
        {"path": stderr_path.relative_to(ROOT).as_posix(), "sha256": digest(execution.stderr), "kind": "execution-output"},
    ],
}
(RUN / "reviewer-result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(result, indent=2, ensure_ascii=False))
if (
    not result["candidate"]["matches"]
    or not all(item["matches"] for item in input_checks)
    or not all(reference_checks.values())
    or result["comparison"]["status"] != "MATCH"
):
    raise SystemExit(1)
