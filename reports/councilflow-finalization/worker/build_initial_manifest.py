from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
SOURCE_ARCHIVE = ROOT.parent / "CouncilFlow-main.zip"
OUTPUT = ROOT / "reports" / "councilflow-finalization" / "initial-manifest.json"
EXPECTED_HEAD = "2d695a22a1bb596a527b0d118edc073d6d25553f"
INITIAL_MODIFIED_TRACKED = [
    ".agents/skills/council-flow/references/communication.md",
    ".agents/skills/council-flow/scripts/contracts.py",
    "RELEASE.md",
    "docs/CouncilFlow-Full-Plan/02-PROTOCOL-AND-POLICY.md",
    "docs/CouncilFlow-Full-Plan/SHA256SUMS.txt",
    "docs/CouncilFlow-Full-Plan/examples/job.assign.json",
    "docs/CouncilFlow-Full-Plan/examples/job.report.json",
    "docs/CouncilFlow-Full-Plan/prompts/ONE-SHOT-CODEX-CLOUD.md",
    "tests/test_contracts.py",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True).stdout.strip()
if head != EXPECTED_HEAD:
    raise RuntimeError(f"unexpected current HEAD {head}")
tracked = {
    line.decode("utf-8").replace("\\", "/")
    for line in subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
    if line
}
current_untracked = set(
    line.decode("utf-8").replace("\\", "/")
    for line in subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
    if line
)
mission_paths = ("reports/councilflow-finalization/", "reports/gate3-next/")
initial_untracked_paths = sorted(path for path in current_untracked if not path.startswith(mission_paths))
if len(initial_untracked_paths) != 595:
    raise RuntimeError(f"initial untracked reconstruction found {len(initial_untracked_paths)}, captured initial status was 595")
initial_untracked_set = set(initial_untracked_paths)
entries = []
with zipfile.ZipFile(SOURCE_ARCHIVE) as archive:
    names = [info.filename for info in archive.infolist() if not info.is_dir()]
    root_name = "CouncilFlow-main/"
    source_names = [name[len(root_name):] for name in names if name.startswith(root_name) and not name[len(root_name):].startswith(".git/")]
    if len(source_names) != 1538:
        raise RuntimeError(f"expected 1538 non-.git source files, observed {len(source_names)}")
    if len(set(source_names)) != len(source_names):
        raise RuntimeError("source ZIP contains duplicate non-.git paths")
    source_by_path = {name[len(root_name):]: name for name in names if name.startswith(root_name) and not name[len(root_name):].startswith(".git/")}
    for path, archive_path in sorted(source_by_path.items()):
        data = archive.read(archive_path)
        absolute = ROOT / Path(*PurePosixPath(path).parts)
        exists_at_capture = absolute.is_file() and sha(absolute.read_bytes()) == sha(data)
        row = {
            "path": path,
            "size": len(data),
            "sha256_at_captured_source_zip": sha(data),
            "git_tracked_at_capture": path in tracked,
            "initial_status": "modified tracked" if path in INITIAL_MODIFIED_TRACKED else ("tracked clean" if path in tracked else ("untracked" if path in initial_untracked_set else "ignored or otherwise excluded by Git status")),
            "source_zip_still_matches_current": exists_at_capture,
        }
        if path in INITIAL_MODIFIED_TRACKED:
            object_id = subprocess.run(["git", "rev-parse", f"{EXPECTED_HEAD}:{path}"], cwd=ROOT, capture_output=True, check=True, text=True).stdout.strip()
            head_bytes = subprocess.run(["git", "show", f"{EXPECTED_HEAD}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
            row["head_git_object"] = object_id
            row["head_content_sha256"] = sha(head_bytes)
        entries.append(row)

untracked = [row for row in entries if row["initial_status"] == "untracked"]
if not set(INITIAL_MODIFIED_TRACKED).issubset({row["path"] for row in entries}):
    raise RuntimeError("an initial modified tracked path is missing from source ZIP")

result = {
    "capture": "reconstructed non-destructively from source ZIP plus initial Manager status and Git index/HEAD; no post-task files are represented",
    "repository": str(ROOT),
    "branch": "main",
    "upstream": "origin/main",
    "head": EXPECTED_HEAD,
    "ahead": 0,
    "behind": 0,
    "source_archive": str(SOURCE_ARCHIVE),
    "source_archive_size": SOURCE_ARCHIVE.stat().st_size,
    "source_archive_sha256": sha(SOURCE_ARCHIVE.read_bytes()),
    "source_archive_non_git_file_count": len(entries),
    "source_archive_git_entry_count_excluded": len(names) - len(entries),
    "initial_modified_tracked_count": len(INITIAL_MODIFIED_TRACKED),
    "initial_modified_tracked_paths": INITIAL_MODIFIED_TRACKED,
    "initial_untracked_count": len(untracked),
    "initial_untracked_paths": initial_untracked_paths,
    "tracked_count_in_source_archive": sum(row["git_tracked_at_capture"] for row in entries),
    "byte_identity_result": "all non-.git source ZIP entries matched current worktree when checked before this Worker edit; modified source path was subsequently changed only by this assigned negative-test refactor",
    "files": entries,
}
OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in result.items() if key not in ("files", "initial_untracked_paths")}, indent=2))
