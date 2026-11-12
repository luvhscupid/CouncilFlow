from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path.cwd().resolve()
ARCHIVE = ROOT / "dist" / "council-flow.zip"
CHECKSUM = ROOT / "dist" / "council-flow.zip.sha256"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe(name: str) -> bool:
    if "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and bool(path.parts) and all(
        part not in ("", ".", "..") for part in path.parts
    ) and not (len(path.parts[0]) > 1 and path.parts[0][1] == ":")


def excluded(name: str) -> bool:
    parts = [part.lower() for part in name.split("/")]
    return (
        any(part in {
            ".git", "__pycache__", ".pytest_cache", ".codex-runtime",
            ".codebase-memory", "runtime", "credentials", "secrets",
        } for part in parts)
        or any(part.endswith((".pyc", ".pyo", ".tmp", ".temp")) for part in parts)
        or any(part in {".env", ".env.local", "credentials.json", "token.json"} for part in parts)
        or "councilflow-hardening" in parts
    )


def walk(directory: str, entries: set[str]) -> None:
    base = ROOT / directory
    if not base.is_dir():
        raise RuntimeError(f"missing allowlisted directory: {directory}")
    for path in base.rglob("*"):
        if path.is_dir():
            continue
        if path.is_symlink():
            raise RuntimeError(f"symlink inside allowlisted directory: {path}")
        name = path.relative_to(ROOT).as_posix()
        if not excluded(name):
            entries.add(name)


entries = {"README.md", "RELEASE.md"}
for directory in (
    ".agents/skills/council-flow", "demo", "tests",
    "docs/gate3/CouncilFlow-Gate3-v0.2", "docs/CouncilFlow-Full-Plan",
    "reports/demo", "reports/csv-summary",
):
    walk(directory, entries)
entries.update({
    "docs/gate3/README.md", "reports/final.md",
    "reports/requirements-traceability.md", "reports/gate3b-results.md",
})
agents = sorted((ROOT / ".codex/agents").glob("council-*.toml"))
if len(agents) != 4:
    raise RuntimeError(f"expected four CouncilFlow TOML files, found {len(agents)}")
entries.update(path.relative_to(ROOT).as_posix() for path in agents)
for name in entries:
    if not safe(name) or excluded(name):
        raise RuntimeError(f"unsafe or excluded allowlisted path: {name}")

rows = []
for name in sorted(entries):
    content = (ROOT / Path(*name.split("/"))).read_bytes()
    rows.append({"path": name, "sha256": sha(content), "size": len(content)})

with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for row in rows:
        info = zipfile.ZipInfo(row["path"], date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, (ROOT / Path(*row["path"].split("/"))).read_bytes())

archive_bytes = ARCHIVE.read_bytes()
archive_sha = sha(archive_bytes)
CHECKSUM.write_text(f"{archive_sha}  council-flow.zip\n", encoding="ascii", newline="\n")
required = {
    ".agents/skills/council-flow/SKILL.md",
    ".agents/skills/council-flow/scripts/contracts.py",
    ".agents/skills/council-flow/policies/roles.yaml",
    "README.md", "RELEASE.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
    "docs/CouncilFlow-Full-Plan/README.md", "tests/test_contracts.py",
    "demo/receipt/receipt_calculator.py",
}
with zipfile.ZipFile(ARCHIVE) as archive:
    names = archive.namelist()
    crc_error = archive.testzip()
    if len(names) != len(set(names)) or crc_error is not None:
        raise RuntimeError(f"duplicate paths or CRC failure: {crc_error}")
    if not required.issubset(names):
        raise RuntimeError(f"required entries missing: {sorted(required - set(names))}")
    for name in names:
        if not safe(name) or excluded(name) or name.startswith(("reports/runtime/", "reports/councilflow-hardening/")) or name == "dist/council-flow.zip":
            raise RuntimeError(f"forbidden archive entry: {name}")
    for row in rows:
        content = archive.read(row["path"])
        if len(content) != row["size"] or sha(content) != row["sha256"]:
            raise RuntimeError(f"archive/source mismatch: {row['path']}")

print(json.dumps({
    "archive": "dist/council-flow.zip",
    "sha256": archive_sha,
    "checksum_matches": CHECKSUM.read_text(encoding="ascii").strip() == f"{archive_sha}  council-flow.zip",
    "entries": len(entries),
    "crc": "PASS",
    "safe_paths": "PASS",
    "required_entries": "PASS",
    "forbidden_entries_absent": "PASS",
    "all_entries_match_source": True,
    "entry_manifest": rows,
}, indent=2, ensure_ascii=False))
