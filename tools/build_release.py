"""Build the standalone source bundle from an explicit repository allowlist.

Verification evidence belongs outside the ZIP. This builder checks container and
source bytes; independently executing the extracted tests remains a release step.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = (
    ".agents/skills/council-flow", "demo", "tests",
    "docs/gate3/CouncilFlow-Gate3-v0.2", "docs/CouncilFlow-Full-Plan",
    "reports/demo", "reports/csv-summary", "docs/technical", "docs/research",
)
FILES = (
    "README.md", "RELEASE.md", "docs/gate3/README.md", "tools/build_release.py",
    "AGENTS.md", "docs/gate3/current-implementation-gaps.md", "docs/gate3/import-record.json",
    "reports/README.md",
    "reports/councilflow-hardening/README.md",
    "reports/councilflow-final-release-audit/README.md",
    "reports/engineering-recovery/README.md",
    "reports/councilflow-finalization/README.md",
    "reports/package-check-verified/README.md",
    "reports/integration-gate3-efficiency/README.md",
    "reports/restoration/README.md",
    "reports/reliability-repair/README.md",
    "reports/gate3-next/README.md",
    "reports/gate3-preflight-2026-11-12/README.md",
    "reports/councilflow-e10/README.md",
    "reports/documentation-release-sync/gate3-run-01.md",
    "reports/documentation-release-sync/claude-calc-001.md",
    ".agents/skills/council-flow/scripts/efficiency.py",
    ".agents/skills/council-flow/scripts/efficiency/recorder.py",
    ".agents/skills/council-flow/scripts/efficiency/digest.py",
    ".agents/skills/council-flow/scripts/efficiency/codex_adapter.py",
    ".agents/skills/council-flow/scripts/efficiency/claude_adapter.py",
    ".agents/skills/council-flow/scripts/efficiency/record.schema.json",
    ".agents/skills/council-flow/references/efficiency.md",
    "demo/gate3-demo/app.py", "demo/gate3-demo/test_app.py",
    "demo/gate3-demo/inputs/amount.csv", "demo/gate3-demo/inputs/nonnumeric.csv",
    "tests/test_efficiency_install.py",
)
# Efficiency lives inside the complete skill; maintained tests/synthetic fixtures
# and Gate 3 demo live under tests/ and demo/. Never allow experiments wholesale.
ROLES = {"council-planner", "council-worker", "council-tester", "council-reviewer"}
FORBIDDEN_PARTS = {
    ".git", "__pycache__", ".pytest_cache", ".codex-runtime", ".codebase-memory",
    "runtime", ".local-runs", "credentials", "secrets", ".env", ".env.local", "credentials.json", "token.json",
}
SECRET = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
                    rb"(?:ghp_|github_pat_|sk-proj-|sk-live-|xox[baprs]-)[A-Za-z0-9_-]{16,}|"
                    rb"AKIA[A-Z0-9]{16}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> bool:
    return (bool(name) and "\\" not in name and not PurePosixPath(name).is_absolute()
            and not PureWindowsPath(name).drive
            and all(part not in {"", ".", ".."} for part in name.split("/")))


# Claude Code plugin tests need plugins/ and its builder, which are not in this package.
HOST_ONLY = {"tests/test_claude_plugin.py"}


def excluded(name: str) -> bool:
    if name in HOST_ONLY:
        return True
    parts = {part.lower() for part in name.split("/")}
    return bool(parts & FORBIDDEN_PARTS) or name.lower().endswith((".pyc", ".pyo", ".tmp", ".temp"))


def is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def source_bytes(root: Path) -> dict[str, bytes]:
    """Read each allowed regular file once; reject links rather than traverse them."""
    root = root.resolve()
    names = set(FILES)
    for relative in DIRECTORIES:
        directory = root / relative
        if not directory.is_dir() or is_link(directory):
            raise ValueError(f"missing or linked allowlisted directory: {relative}")
        for current, directories, files in os.walk(directory, followlinks=False):
            for name in list(directories):
                path = Path(current) / name
                if excluded(path.relative_to(root).as_posix()):
                    directories.remove(name)
                elif is_link(path):
                    raise ValueError(f"linked directory in allowlist: {path.relative_to(root)}")
            names.update((Path(current) / name).relative_to(root).as_posix() for name in files)
    roles = sorted((root / ".codex/agents").glob("council-*.toml"))
    if {path.stem for path in roles} != ROLES:
        raise ValueError("the four native CouncilFlow roles are required")
    names.update(path.relative_to(root).as_posix() for path in roles)
    result = {}
    for name in sorted(names):
        if excluded(name):
            continue
        path = root / name
        if not safe_name(name) or not path.resolve().is_relative_to(root) or is_link(path) or not path.is_file():
            raise ValueError(f"unsafe or missing source: {name}")
        data = path.read_bytes()
        if SECRET.search(data):
            raise ValueError(f"credential-pattern match in source: {name}")
        result[name] = data
    return result


def atomic_write(path: Path, data: bytes) -> None:
    """Replace an output entry without truncating any existing linked inode.

    The output directory is validated by build(). This is best-effort local
    filesystem validation, not protection from a concurrent directory swap.
    """
    descriptor, temporary_name = tempfile.mkstemp(prefix=".council-flow-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build(root: Path = ROOT) -> dict:
    root = root.resolve()
    sources = source_bytes(root)
    manifest = [{"path": name, "size": len(data), "sha256": sha256(data)}
                for name, data in sources.items()]
    destination = root / "dist"
    if destination.is_symlink() or (destination.exists() and (is_link(destination) or not destination.is_dir())):
        raise ValueError("release output directory must be an ordinary directory inside the repository")
    destination.mkdir(exist_ok=True)
    if is_link(destination) or not destination.resolve().is_relative_to(root):
        raise ValueError("release output directory leaves the repository")
    archive_path = destination / "council-flow.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sources.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Stable Unix-origin ZIP metadata on Windows and POSIX.
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as archive:
        if archive.testzip() is not None or archive.namelist() != list(sources):
            raise ValueError("archive CRC or inventory mismatch")
        for name, data in sources.items():
            if archive.read(name) != data:
                raise ValueError(f"archive/source bytes differ: {name}")
    archive_bytes = buffer.getvalue()
    atomic_write(archive_path, archive_bytes)
    digest = sha256(archive_bytes)
    atomic_write(destination / "council-flow.zip.sha256", f"{digest}  council-flow.zip\n".encode("ascii"))
    report = {"archive": "dist/council-flow.zip", "sha256": digest, "entries": len(manifest),
              "files": manifest, "crc": "PASS", "source_bytes": "PASS",
              "tests": "NOT_RUN_BY_BUILDER; independent checkout/extraction verification required",
              "secret_scan": "No tested signatures found; heuristic, not proof of all-secret absence"}
    atomic_write(destination / "council-flow.manifest.json",
                 (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps({key: result[key] for key in ("archive", "sha256", "entries", "crc", "source_bytes", "tests")}))
