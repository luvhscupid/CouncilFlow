"""Sync and package the Claude Code plugin from the canonical Codex skill.

The shared runtime (references/, policies/, scripts/) is copied byte-for-byte
from .agents/skills/council-flow into plugins/councilflow/skills/run/ so the
plugin is self-contained after installation. `--check` fails on drift.
Output: dist/councilflow-claude-plugin.zip (+ .sha256), deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / ".agents/skills/council-flow"
PLUGIN = ROOT / "plugins/councilflow"
TARGET = PLUGIN / "skills/run"
SHARED = ("references", "policies", "scripts")
SKIP = {"__pycache__"}
SKIP_SUFFIX = (".pyc", ".pyo")
FORBIDDEN = {".git", ".councilflow", ".env", "credentials.json", "token.json"}


def shared_files(base: Path) -> dict[str, bytes]:
    out = {}
    for part in SHARED:
        for path in sorted((base / part).rglob("*")):
            rel = path.relative_to(base).as_posix()
            if path.is_symlink():
                raise ValueError(f"link not allowed: {rel}")
            if (not path.is_file() or SKIP & set(path.parts) or path.suffix in SKIP_SUFFIX):
                continue
            out[rel] = path.read_bytes()
    return out


def drift() -> list[str]:
    canon, copy = shared_files(CANON), shared_files(TARGET) if TARGET.is_dir() else {}
    return sorted([f"missing: {n}" for n in canon.keys() - copy.keys()]
                  + [f"extra: {n}" for n in copy.keys() - canon.keys()]
                  + [f"differs: {n}" for n in canon.keys() & copy.keys() if canon[n] != copy[n]])


def sync() -> None:
    for name, data in shared_files(CANON).items():
        dest = TARGET / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
    for name in shared_files(TARGET):
        if not (CANON / name).is_file():
            (TARGET / name).unlink()


def package_files() -> dict[str, bytes]:
    out = {}
    for path in sorted(PLUGIN.rglob("*"), key=lambda path: path.relative_to(PLUGIN).as_posix()):
        if path.is_symlink():
            raise ValueError(f"link not allowed: {path}")
        rel = path.relative_to(PLUGIN).as_posix()
        if (not path.is_file() or SKIP & set(path.parts) or path.suffix in SKIP_SUFFIX
                or FORBIDDEN & set(path.parts)):
            continue
        out[rel] = path.read_bytes()
    return out


def build(output: Path | None = None) -> dict:
    problems = drift()
    if problems:
        raise ValueError("plugin runtime drifted from canonical skill; run sync: " + "; ".join(problems))
    files = package_files()
    archive = Path(output) if output is not None else ROOT / "dist/councilflow-claude-plugin.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="ascii", newline="\n")
    return {"archive": archive.as_posix(), "sha256": digest, "entries": len(files)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("sync", "check", "build"))
    parser.add_argument("--output", type=Path, help="write archive and sidecar to this path")
    args = parser.parse_args()
    cmd = args.command
    try:
        if cmd == "sync":
            sync()
        if cmd in ("sync", "check") and drift():
            print("\n".join(drift())); sys.exit(1)
        if cmd == "build":
            print(json.dumps(build(args.output)))
    except ValueError as exc:
        print(exc); sys.exit(1)
