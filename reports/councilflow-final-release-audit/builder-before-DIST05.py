"""Build the standalone source bundle from an explicit repository allowlist.

Verification evidence belongs outside the ZIP. This builder checks container and
source bytes; independently executing the extracted tests remains a release step.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = (
    ".agents/skills/council-flow", "demo", "tests",
    "docs/gate3/CouncilFlow-Gate3-v0.2", "docs/CouncilFlow-Full-Plan",
    "reports/demo", "reports/csv-summary",
)
FILES = ("README.md", "RELEASE.md", "docs/gate3/README.md", "tools/build_release.py")
ROLES = {"council-planner", "council-worker", "council-tester", "council-reviewer"}
FORBIDDEN_PARTS = {
    ".git", "__pycache__", ".pytest_cache", ".codex-runtime", ".codebase-memory",
    "runtime", "credentials", "secrets", ".env", ".env.local", "credentials.json", "token.json",
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


def excluded(name: str) -> bool:
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


def build(root: Path = ROOT) -> dict:
    root = root.resolve()
    sources = source_bytes(root)
    manifest = [{"path": name, "size": len(data), "sha256": sha256(data)}
                for name, data in sources.items()]
    destination = root / "dist"
    destination.mkdir(exist_ok=True)
    archive_path = destination / "council-flow.zip"
    temporary = destination / "council-flow.zip.tmp"
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sources.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None or archive.namelist() != list(sources):
            raise ValueError("archive CRC or inventory mismatch")
        for name, data in sources.items():
            if archive.read(name) != data:
                raise ValueError(f"archive/source bytes differ: {name}")
    temporary.replace(archive_path)
    digest = sha256(archive_path.read_bytes())
    (destination / "council-flow.zip.sha256").write_text(
        f"{digest}  council-flow.zip\n", encoding="ascii", newline="\n")
    report = {"archive": "dist/council-flow.zip", "sha256": digest, "entries": len(manifest),
              "files": manifest, "crc": "PASS", "source_bytes": "PASS",
              "tests": "NOT_RUN_BY_BUILDER; independent checkout/extraction verification required",
              "secret_scan": "No tested signatures found; heuristic, not proof of all-secret absence"}
    (destination / "council-flow.manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps({key: result[key] for key in ("archive", "sha256", "entries", "crc", "source_bytes", "tests")}))
