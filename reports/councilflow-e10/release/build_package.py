from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "dist" / "council-flow.zip"
CHECKSUM = ROOT / "dist" / "council-flow.zip.sha256"
OUT = ROOT / "reports" / "councilflow-e10" / "release"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        "\\" not in name
        and not path.is_absolute()
        and bool(path.parts)
        and all(part not in ("", ".", "..") for part in path.parts)
        and not (len(path.parts[0]) > 1 and path.parts[0][1] == ":")
    )


def excluded(name: str) -> bool:
    parts = [part.lower() for part in name.split("/")]
    return (
        any(part in {".git", "__pycache__", ".pytest_cache", ".codex-runtime", ".codebase-memory", "runtime", "credentials", "secrets"} for part in parts)
        or any(part.endswith((".pyc", ".pyo", ".tmp", ".temp")) for part in parts)
        or any(part in {".env", ".env.local", "credentials.json", "token.json"} for part in parts)
        or "councilflow-hardening" in parts
        or "councilflow-finalization" in parts
        or "gate3-next" in parts
    )


def walk(relative: str, entries: set[str]) -> None:
    directory = ROOT / relative
    if not directory.is_dir():
        raise RuntimeError(f"missing allowlisted directory: {relative}")
    for path in directory.rglob("*"):
        if path.is_dir():
            continue
        if path.is_symlink():
            raise RuntimeError(f"symlink inside allowlist: {path.relative_to(ROOT)}")
        name = path.relative_to(ROOT).as_posix()
        if not excluded(name):
            entries.add(name)


entries: set[str] = {"README.md", "RELEASE.md"}
for directory in (
    ".agents/skills/council-flow",
    "demo",
    "tests",
    "docs/gate3/CouncilFlow-Gate3-v0.2",
    "docs/CouncilFlow-Full-Plan",
    "reports/demo",
    "reports/csv-summary",
):
    walk(directory, entries)
for name in (
    "docs/gate3/README.md",
):
    entries.add(name)

agent_files = sorted((ROOT / ".codex" / "agents").glob("council-*.toml"))
if len(agent_files) != 4:
    raise RuntimeError(f"expected four CouncilFlow TOML roles, found {len(agent_files)}")
entries.update(path.relative_to(ROOT).as_posix() for path in agent_files)

for name in entries:
    if not safe_path(name) or excluded(name):
        raise RuntimeError(f"unsafe or forbidden allowlist path: {name}")
    if not (ROOT / Path(*name.split("/"))).is_file():
        raise RuntimeError(f"allowlisted path is missing or not a file: {name}")

manifest = [
    {
        "path": name,
        "size": len((ROOT / Path(*name.split("/"))).read_bytes()),
        "sha256": sha256((ROOT / Path(*name.split("/"))).read_bytes()),
    }
    for name in sorted(entries)
]
manifest_path = OUT / "package-manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for row in manifest:
        info = zipfile.ZipInfo(row["path"], date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (ROOT / Path(*row["path"].split("/"))).read_bytes())

archive_bytes = ARCHIVE.read_bytes()
archive_digest = sha256(archive_bytes)
CHECKSUM.write_text(f"{archive_digest}  council-flow.zip\n", encoding="ascii", newline="\n")

required = {
    ".agents/skills/council-flow/SKILL.md",
    ".agents/skills/council-flow/references/codebase-memory.md",
    ".agents/skills/council-flow/scripts/contracts.py",
    ".agents/skills/council-flow/policies/roles.yaml",
    "README.md",
    "RELEASE.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
    "docs/CouncilFlow-Full-Plan/README.md",
    "docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt",
    "tests/test_contracts.py",
    "tests/test_codebase_memory_integration.py",
}
forbidden_prefixes = (".git/", "reports/councilflow-hardening/", "reports/councilflow-finalization/", "reports/gate3-next/")
with zipfile.ZipFile(ARCHIVE) as archive:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise RuntimeError("duplicate archive entries")
    if archive.testzip() is not None:
        raise RuntimeError("archive CRC failure")
    if not required.issubset(names):
        raise RuntimeError(f"required entries absent: {sorted(required - set(names))}")
    if any(not safe_path(name) or name.startswith(forbidden_prefixes) or excluded(name) for name in names):
        raise RuntimeError("unsafe or forbidden archive path")
    for row in manifest:
        data = archive.read(row["path"])
        if len(data) != row["size"] or sha256(data) != row["sha256"]:
            raise RuntimeError(f"source/archive byte mismatch: {row['path']}")

extracted = []
with tempfile.TemporaryDirectory(prefix="councilflow-final-package-") as temporary:
    target = Path(temporary).resolve()
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name in archive.namelist():
            destination = (target / Path(*PurePosixPath(name).parts)).resolve()
            if target not in destination.parents:
                raise RuntimeError(f"extraction path escapes target: {name}")
        archive.extractall(target)
    executable = sys.executable
    checks = [
        [executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [executable, "-m", "unittest", "discover", "-s", "demo/receipt", "-p", "test_receipt_calculator.py", "-v"],
        [executable, "-m", "unittest", "discover", "-s", "demo/structured-flow", "-p", "test_sum_values.py", "-v"],
        [executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_codebase_memory_integration.py", "-v"],
        [executable, ".agents/skills/council-flow/scripts/contracts.py", "message", "docs/CouncilFlow-Full-Plan/examples/job.assign.json", "--root", "."],
        [executable, ".agents/skills/council-flow/scripts/contracts.py", "message", "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", "."],
    ]
    for index, command in enumerate(checks, start=1):
        result = subprocess.run(command, cwd=target, capture_output=True, check=False)
        stem = f"extracted-check-{index}"
        (OUT / f"{stem}.stdout.bin").write_bytes(result.stdout)
        (OUT / f"{stem}.stderr.bin").write_bytes(result.stderr)
        extracted.append(
            {
                "command": executable,
                "arguments": command[1:],
                "working_directory": str(target),
                "exit_code": result.returncode,
                "stdout_sha256_crlf_to_lf_only": sha256(result.stdout.replace(b"\r\n", b"\n")),
                "stderr_sha256_raw": sha256(result.stderr),
                "stdout_path": f"reports/councilflow-e10/release/{stem}.stdout.bin",
                "stderr_path": f"reports/councilflow-e10/release/{stem}.stderr.bin",
            }
        )
        if result.returncode != 0:
            raise RuntimeError(f"extracted check failed: {command}")

verification = {
    "archive": "dist/council-flow.zip",
    "sha256": archive_digest,
    "checksum_file": "dist/council-flow.zip.sha256",
    "entry_count": len(manifest),
    "manifest_path": "reports/councilflow-e10/release/package-manifest.json",
    "manifest_sha256": sha256(manifest_path.read_bytes()),
    "crc": "PASS",
    "safe_paths_and_extraction_containment": "PASS",
    "required_contents": "PASS",
    "forbidden_paths_absent": "PASS",
    "source_byte_mapping": "PASS",
    "checksum_matches": CHECKSUM.read_text(encoding="ascii").strip() == f"{archive_digest}  council-flow.zip",
    "independent_full_suites": "PASS_IN_EXTRACTED_PACKAGE",
    "extracted_checks": extracted,
}
(OUT / "package-verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
print(json.dumps(verification, indent=2))
