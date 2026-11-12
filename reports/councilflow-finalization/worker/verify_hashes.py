from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
audit = json.loads((ROOT / "reports/councilflow-finalization/retirement-audit.json").read_text(encoding="utf-8"))
package = json.loads((ROOT / "reports/councilflow-finalization/worker/package-verification.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "reports/councilflow-finalization/worker/package-manifest.json").read_text(encoding="utf-8"))
initial = json.loads((ROOT / "reports/councilflow-finalization/initial-manifest.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


checks = []
for row in audit["working_tree"]["text_matches"]:
    actual = sha((ROOT / Path(*row["path"].split("/"))).read_bytes())
    checks.append({"check": "working_tree_exception", "path": row["path"], "expected": row["sha256"], "actual": actual, "passed": actual == row["sha256"]})

source_zip = ROOT.parent / "CouncilFlow-main.zip"
with zipfile.ZipFile(source_zip) as archive:
    for row in audit["source_archive"]["text_matches"]:
        data = archive.read("CouncilFlow-main/" + row["path"])
        actual = sha(data)
        checks.append({"check": "source_archive_exception", "path": row["path"], "expected": row["sha256"], "actual": actual, "passed": actual == row["sha256"]})

release_zip = ROOT / "dist/council-flow.zip"
release_sha = sha(release_zip.read_bytes())
checks.append({"check": "release_archive_digest", "path": "dist/council-flow.zip", "expected": package["sha256"], "actual": release_sha, "passed": release_sha == package["sha256"]})
checks.append({"check": "sibling_checksum", "path": "dist/council-flow.zip.sha256", "expected": f"{release_sha}  council-flow.zip", "actual": (ROOT / "dist/council-flow.zip.sha256").read_text(encoding="ascii").strip(), "passed": (ROOT / "dist/council-flow.zip.sha256").read_text(encoding="ascii").strip() == f"{release_sha}  council-flow.zip"})
with zipfile.ZipFile(release_zip) as archive:
    names = set(archive.namelist())
    for row in manifest:
        data = archive.read(row["path"])
        actual = sha(data)
        checks.append({"check": "release_source_byte_mapping", "path": row["path"], "expected": row["sha256"], "actual": actual, "passed": actual == row["sha256"] and row["path"] in names})
    for path in ("tests/test_codebase_memory_integration.py", "tests/test_contracts.py"):
        data = archive.read(path)
        actual = sha(data)
        worktree = sha((ROOT / Path(*path.split("/"))).read_bytes())
        checks.append({"check": "current_regressions_in_release", "path": path, "expected": worktree, "actual": actual, "passed": actual == worktree})
        if path.endswith("test_codebase_memory_integration.py"):
            checks.append({"check": "neutral_test_label_in_release", "path": path, "expected": True, "actual": "test_retired_standalone_paths_are_absent" in data.decode("utf-8"), "passed": b"test_custom_recall_system_is_removed" not in data})
        if path.endswith("test_contracts.py"):
            checks.append({"check": "top_level_reference_regression_in_release", "path": path, "expected": True, "actual": b"test_tester_command_and_reviewer_rerun_artifacts_must_be_top_level_refs" in data, "passed": b"test_tester_command_and_reviewer_rerun_artifacts_must_be_top_level_refs" in data})

for protected in (
    "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
):
    worktree_hash = sha((ROOT / Path(*protected.split("/"))).read_bytes())
    with zipfile.ZipFile(release_zip) as archive:
        archive_hash = sha(archive.read(protected))
    checks.append({"check": "frozen_governance_preserved_and_packaged", "path": protected, "expected": worktree_hash, "actual": archive_hash, "passed": worktree_hash == archive_hash})

result = {
    "source_archive_sha256": sha(source_zip.read_bytes()),
    "expected_source_archive_sha256": initial["source_archive_sha256"],
    "package_sha256": release_sha,
    "package_entry_count": len(manifest),
    "checks_total": len(checks),
    "checks_passed": sum(check["passed"] for check in checks),
    "checks_failed": [check for check in checks if not check["passed"]],
    "checks": checks,
}
output = ROOT / "reports/councilflow-finalization/worker/hash-consistency.json"
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in result.items() if key != "checks"}, indent=2))
if result["checks_failed"] or result["source_archive_sha256"] != result["expected_source_archive_sha256"]:
    raise SystemExit(1)
