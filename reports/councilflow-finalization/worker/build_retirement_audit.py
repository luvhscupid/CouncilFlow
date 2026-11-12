from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
SOURCE_ARCHIVE = ROOT.parent / "CouncilFlow-main.zip"
RELEASE_ARCHIVE = ROOT / "dist" / "council-flow.zip"
OUTPUT = ROOT / "reports" / "councilflow-finalization" / "retirement-audit.json"
GENERATED_PREFIXES = ("reports/councilflow-finalization/", "reports/gate3-next/")
TOKEN = "re" + "call"
PATTERN = re.compile(r"(?i)cf[-_]" + TOKEN + r"|cf " + TOKEN)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> str | None:
    if b"\0" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def read_tree():
    scanned = []
    skipped_generated = []
    binary_count = 0
    path_name_matches = []
    for path in ROOT.rglob("*"):
        if path.is_symlink():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if ".git" in PurePosixPath(relative).parts or relative.lower().endswith((".zip", ".pyc", ".pyo")):
            continue
        if any(relative.startswith(prefix) for prefix in GENERATED_PREFIXES):
            skipped_generated.append(relative)
            continue
        if PATTERN.search(relative):
            path_name_matches.append(relative)
        if not path.is_file():
            continue
        data = path.read_bytes()
        text = decode_text(data)
        if text is None:
            binary_count += 1
            continue
        if PATTERN.search(text):
            if relative.startswith(("reports/", "docs/")):
                classification = "historical or supporting evidence retained unchanged"
            else:
                classification = "active project surface requiring review"
            scanned.append({"path": relative, "sha256": sha(data), "classification": classification})
    return scanned, skipped_generated, binary_count, path_name_matches


def scan_zip(path: Path, prefix: str, include_git: bool):
    name_matches = []
    content_matches = []
    text_entries = 0
    binary_entries = 0
    excluded_git = 0
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        for full_name in names:
            relative = full_name[len(prefix):] if full_name.startswith(prefix) else full_name
            if not include_git and ".git" in PurePosixPath(relative).parts:
                excluded_git += 1
                continue
            if PATTERN.search(relative):
                name_matches.append(relative)
            data = archive.read(full_name)
            text = decode_text(data)
            if text is None:
                binary_entries += 1
                continue
            text_entries += 1
            if PATTERN.search(text):
                content_matches.append({"path": relative, "sha256": sha(data)})
    return names, name_matches, content_matches, text_entries, binary_entries, excluded_git


tree_matches, skipped_generated, tree_binary_count, tree_path_matches = read_tree()
source_names, source_name_matches, source_text_matches, source_text_count, source_binary_count, source_git_excluded = scan_zip(
    SOURCE_ARCHIVE, "CouncilFlow-main/", include_git=False
)
release_names, release_name_matches, release_text_matches, release_text_count, release_binary_count, release_git_excluded = scan_zip(
    RELEASE_ARCHIVE, "", include_git=True
)
tracked_scan = subprocess.run(
    ["git", "grep", "-I", "-i", "-n", "-E", r"cf[-_]" + TOKEN + r"|cf " + TOKEN],
    cwd=ROOT,
    capture_output=True,
)
tracked_matches = tracked_scan.stdout.decode("utf-8", errors="replace").splitlines()
tracked_historical_matches = [line for line in tracked_matches if line.split(":", 1)[0].startswith(("reports/", "docs/"))]
tracked_active_matches = [line for line in tracked_matches if line not in tracked_historical_matches]

active_matches = [row for row in tree_matches if row["classification"] == "active project surface requiring review"]
result = {
    "purpose": "Static scan for residual retired standalone component references. Historical evidence is retained; no history rewriting is performed.",
    "scan_pattern_description": "case-insensitive cf-prefixed hyphen/underscore alias and spaced alias; constructed at runtime to avoid self-matching generated evidence",
    "generated_paths_excluded_from_self_scan": GENERATED_PREFIXES,
    "generated_paths_excluded_file_count": len(skipped_generated),
    "working_tree": {
        "root": str(ROOT),
        "git_grep_tracked_match_count": len(tracked_matches),
        "git_grep_historical_line_count": len(tracked_historical_matches),
        "git_grep_historical_matches": tracked_historical_matches,
        "git_grep_active_match_count": len(tracked_active_matches),
        "git_grep_active_matches": tracked_active_matches,
        "text_match_file_count": len(tree_matches),
        "text_matches": tree_matches,
        "active_surface_match_count": len(active_matches),
        "active_path_name_match_count": len(tree_path_matches),
        "binary_files_skipped": tree_binary_count,
        "git_directory_excluded": True,
    },
    "source_archive": {
        "path": str(SOURCE_ARCHIVE),
        "sha256": sha(SOURCE_ARCHIVE.read_bytes()),
        "file_entry_count": len(source_names),
        "utf8_text_entry_count": source_text_count,
        "binary_entry_count": source_binary_count,
        "git_file_entries_excluded": source_git_excluded,
        "entry_name_matches": source_name_matches,
        "historical_text_match_count": len(source_text_matches),
        "text_matches": source_text_matches,
    },
    "installable_release_archive": {
        "path": str(RELEASE_ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha(RELEASE_ARCHIVE.read_bytes()),
        "file_entry_count": len(release_names),
        "utf8_text_entry_count": release_text_count,
        "binary_entry_count": release_binary_count,
        "entry_name_matches": release_name_matches,
        "text_match_count": len(release_text_matches),
        "text_matches": release_text_matches,
        "standalone_component_entries": [name for name in release_names if any(token in name.lower() for token in ("recall",)) and "codebase-memory" not in name.lower()],
    },
    "integrated_context_path": {
        "path": ".agents/skills/council-flow/references/codebase-memory.md",
        "sha256": sha((ROOT / ".agents/skills/council-flow/references/codebase-memory.md").read_bytes()),
        "policy": "exact-root project context/navigation; never verification evidence",
    },
    "limitations": [
        "Git object contents and commit history were not scanned or rewritten; they are not active checkout or installable archive surfaces.",
        "Generated handoff, Gate 3 preparation, and finalization evidence paths are excluded from the content scan to prevent self-referential results.",
        "Binary files were counted but not content-scanned; ZIP entry names and all UTF-8 text entries were scanned.",
        "A static scan detects the configured aliases only and cannot prove that an arbitrary encoding or externally loaded artifact is absent.",
    ],
    "disposition": "PASS for active/installable standalone surface scan only if active_surface_match_count and release text/name match counts are zero; historical text matches remain listed with hashes.",
}
OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "working_tree_text_matches": len(tree_matches),
    "active_matches": len(active_matches),
    "git_grep_matches": len(tracked_matches),
    "source_archive_historical_matches": len(source_text_matches),
    "release_archive_text_matches": len(release_text_matches),
    "release_archive_name_matches": len(release_name_matches),
    "audit_path": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
}, indent=2))
if active_matches or tracked_active_matches or tree_path_matches or release_text_matches or release_name_matches:
    raise SystemExit(1)
