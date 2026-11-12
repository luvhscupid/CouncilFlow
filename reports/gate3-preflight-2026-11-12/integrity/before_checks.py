from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path.cwd().resolve()
CHECKLIST = ROOT / "reports/gate3-next/E1-E10-CHECKLIST.md"
FULL_PLAN = ROOT / "docs/CouncilFlow-Full-Plan"
FROZEN = ROOT / "docs/gate3/CouncilFlow-Gate3-v0.2"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


checklist = CHECKLIST.read_text(encoding="utf-8")
expected_frozen = dict(re.findall(r"`([^`]+)` — SHA-256 `([0-9a-f]{64})`", checklist))
frozen_checks = []
for relative, expected in expected_frozen.items():
    path = ROOT / relative
    actual = sha(path)
    frozen_checks.append({
        "path": relative,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "matches": actual == expected,
    })

manifest = FULL_PLAN / "SHA256SUMS.txt"
plan_checks = []
for line in manifest.read_text(encoding="utf-8").splitlines():
    expected, relative = line.split(maxsplit=1)
    path = FULL_PLAN / relative.strip()
    actual = sha(path)
    plan_checks.append({
        "path": path.relative_to(ROOT).as_posix(),
        "expected_sha256": expected,
        "actual_sha256": actual,
        "matches": actual == expected,
    })

draft = (ROOT / "reports/gate3-next/OWNER-TASK-DRAFT.txt").read_text(encoding="utf-8")
criteria = [line for line in draft.splitlines() if re.match(r"^[12]\. ", line)]
workspace = ROOT / "reports/gate3-next/disposable-workspace"
fixture_files = [
    workspace / "demo/gate3-demo/app.py",
    workspace / "demo/gate3-demo/test_app.py",
]

result = {
    "frozen_sources": frozen_checks,
    "frozen_all_match_checklist": bool(frozen_checks) and all(item["matches"] for item in frozen_checks),
    "full_plan_manifest": manifest.relative_to(ROOT).as_posix(),
    "full_plan_checks": plan_checks,
    "full_plan_count": len(plan_checks),
    "full_plan_all_match": len(plan_checks) == 20 and all(item["matches"] for item in plan_checks),
    "owner_task_draft": {
        "path": "reports/gate3-next/OWNER-TASK-DRAFT.txt",
        "not_owner_approved": "NOT OWNER-APPROVED" in draft,
        "criterion_lines": criteria,
        "exactly_two_criteria": len(criteria) == 2,
        "sha256": sha(ROOT / "reports/gate3-next/OWNER-TASK-DRAFT.txt"),
    },
    "disposable_workspace": {
        "path": "reports/gate3-next/disposable-workspace",
        "app": {"path": fixture_files[0].relative_to(ROOT).as_posix(), "sha256": sha(fixture_files[0])},
        "test": {"path": fixture_files[1].relative_to(ROOT).as_posix(), "sha256": sha(fixture_files[1])},
        "app_and_test_present": all(path.is_file() for path in fixture_files),
    },
}
output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
(ROOT / "reports/gate3-preflight-2026-11-12/integrity/before_checks.json").write_text(output, encoding="utf-8", newline="\n")
print(output, end="")
if not result["frozen_all_match_checklist"] or not result["full_plan_all_match"] or not result["owner_task_draft"]["exactly_two_criteria"] or not result["owner_task_draft"]["not_owner_approved"]:
    raise SystemExit(1)
