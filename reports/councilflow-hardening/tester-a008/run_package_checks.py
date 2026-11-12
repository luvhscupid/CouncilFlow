import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path.cwd().resolve()
EVIDENCE = ROOT / "reports/councilflow-hardening/tester-a008"
ARCHIVE = ROOT / "dist/council-flow.zip"
CHECKSUM = ROOT / "dist/council-flow.zip.sha256"
EXTRACTED = EVIDENCE / "relocated"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


EVIDENCE.mkdir(parents=True, exist_ok=True)
assert ARCHIVE.is_file() and CHECKSUM.is_file()
archive_sha = file_digest(ARCHIVE)
assert CHECKSUM.read_text(encoding="utf-8").strip().split()[0] == archive_sha

with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == 118 and len(set(names)) == 118
    required = [
        ".agents/skills/council-flow/SKILL.md",
        ".agents/skills/council-flow/scripts/contracts.py",
        ".agents/skills/council-flow/references/communication.md",
        ".agents/skills/council-flow/policies/roles.yaml",
        "README.md", "RELEASE.md", "tests/test_contracts.py", "demo/README.md",
        "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
        "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
        "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
        "docs/CouncilFlow-Full-Plan/examples/job.assign.json",
        "docs/CouncilFlow-Full-Plan/examples/job.report.json",
        "docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt",
        "reports/final.md", "reports/requirements-traceability.md",
    ]
    assert all(item in names for item in required)
    agents = [n for n in names if re.fullmatch(
        r"\.codex/agents/council-(planner|worker|tester|reviewer)\.toml", n
    )]
    assert len(agents) == 4
    forbidden = []
    mismatches = []
    for name in names:
        path = PurePosixPath(name)
        low = name.lower()
        if path.is_absolute() or ".." in path.parts or "\\" in name or re.match(r"^[A-Za-z]:", name):
            forbidden.append(("unsafe", name))
        if ".git" in path.parts or "__pycache__" in path.parts or low.endswith(".pyc"):
            forbidden.append(("cache/git", name))
        if ".codex-runtime" in low or "reports/runtime/" in low or "credential" in low or "secret" in low or low == ".env" or low.endswith("/.env"):
            forbidden.append(("runtime/private", name))
        if "councilflow-hardening" in low or name == "dist/council-flow.zip":
            forbidden.append(("temporary/self", name))
        local = ROOT.joinpath(*path.parts)
        if not local.is_file() or file_digest(local) != digest(archive.read(name)):
            mismatches.append(name)
    assert not forbidden, forbidden
    assert not mismatches, mismatches

if EXTRACTED.exists():
    shutil.rmtree(EXTRACTED)
EXTRACTED.mkdir(parents=True)
with zipfile.ZipFile(ARCHIVE) as archive:
    archive.extractall(EXTRACTED)
    extracted_hashes = []
    for name in archive.namelist():
        path = EXTRACTED.joinpath(*PurePosixPath(name).parts)
        assert path.is_file() and file_digest(path) == digest(archive.read(name)), name
        extracted_hashes.append(name)

commands = []


def run(label: str, args: list[str], cwd: Path, expected: int = 0):
    executable = sys.executable
    result = subprocess.run([executable, *args], cwd=cwd, capture_output=True)
    stdout_path = EVIDENCE / f"{label}.stdout.bin"
    stderr_path = EVIDENCE / f"{label}.stderr.bin"
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    record = {
        "name": label,
        "command": executable,
        "arguments": args,
        "working_directory": str(cwd),
        "exit_code": result.returncode,
        "stdout_sha256_crlf_to_lf_only": digest(result.stdout.replace(b"\r\n", b"\n")),
        "stderr_sha256_raw": digest(result.stderr),
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
    }
    commands.append(record)
    if result.returncode != expected:
        raise RuntimeError(f"{label} exit {result.returncode}, expected {expected}: {result.stderr.decode('utf-8', 'replace')}")
    return result


suites = [
    ("suite-tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("suite-receipt", ["-m", "unittest", "discover", "-s", "demo/receipt", "-v"]),
    ("suite-csv-summary", ["-m", "unittest", "discover", "-s", "demo/csv-summary", "-v"]),
    ("suite-structured-flow", ["-m", "unittest", "discover", "-s", "demo/structured-flow", "-v"]),
    ("suite-demo-verification", ["-m", "unittest", "discover", "-s", "reports/demo/verification", "-v"]),
    ("suite-csv-verification", ["-m", "unittest", "discover", "-s", "reports/csv-summary/verification", "-v"]),
]
for name, args in suites:
    run(name, args, EXTRACTED)

assign_cmd = [".agents/skills/council-flow/scripts/contracts.py", "message", "docs/CouncilFlow-Full-Plan/examples/job.assign.json", "--root", "."]
report_cmd = [".agents/skills/council-flow/scripts/contracts.py", "message", "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", "."]
run("example-job-assign", assign_cmd, EXTRACTED)
run("example-job-report", report_cmd, EXTRACTED)

stale = EXTRACTED / ".tester-stale-job-report.json"
data = json.loads((EXTRACTED / "docs/CouncilFlow-Full-Plan/examples/job.report.json").read_text(encoding="utf-8"))
data["payload"]["candidate_ref"]["sha256"] = "0" * 64
stale.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
run("example-stale-negative", [".agents/skills/council-flow/scripts/contracts.py", "message", ".tester-stale-job-report.json", "--root", "."], EXTRACTED, expected=1)
stale.unlink()

report = {
    "archive_sha256": archive_sha,
    "checksum_matches": True,
    "entry_count": len(names),
    "crc": "PASS",
    "safe_paths": "PASS",
    "required_contents": "PASS",
    "forbidden_contents_absent": "PASS",
    "all_archived_bytes_match_worktree": "PASS",
    "all_extracted_hashes_match": "PASS",
    "relocated_root": EXTRACTED.relative_to(ROOT).as_posix(),
    "runs": commands,
}
(EVIDENCE / "independent-package-checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"archive_sha256": archive_sha, "entry_count": len(names), "commands": len(commands), "relocated": str(EXTRACTED)}))
