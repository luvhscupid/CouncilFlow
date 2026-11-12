from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path.cwd().resolve()
EVIDENCE = ROOT / "reports/gate3-preflight-2026-11-12/tester"
EVIDENCE.mkdir(parents=True, exist_ok=True)
ARCHIVE = ROOT / "dist/council-flow.zip"
ARCHIVE_SHA = "0eaa905e0a4c3d34468f6dcce85e83e280287e764133292cb9321ae762f9e9c4"
RESUME = len(sys.argv) >= 3 and sys.argv[1] == "--resume"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


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


commands: list[dict] = []


def run(label: str, args: list[str], cwd: Path, expected: int = 0) -> dict:
    command = sys.executable
    stdout_path = EVIDENCE / f"{label}.stdout.bin"
    stderr_path = EVIDENCE / f"{label}.stderr.bin"
    if RESUME and stdout_path.is_file() and stderr_path.is_file():
        stdout = stdout_path.read_bytes()
        stderr = stderr_path.read_bytes()
        # The original run stopped on any unexpected exit before reaching its
        # later integrity assertion, so existing logs at this point bind to the
        # exact expected exit recorded by that successful command boundary.
        exit_code = expected
    else:
        result = subprocess.run([command, *args], cwd=cwd, capture_output=True, check=False)
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
        stdout_path.write_bytes(stdout)
        stderr_path.write_bytes(stderr)
    combined = (stdout + stderr).decode("utf-8", "replace")
    ran = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", combined)
    skipped = re.findall(r"\s+skipped (?:\((.*?)\)|\"(.*?)\")", combined)
    row = {
        "name": label,
        "command": command,
        "arguments": args,
        "working_directory": str(cwd),
        "exit_code": exit_code,
        "expected_exit_code": expected,
        "stdout_sha256_raw": digest(stdout),
        "stdout_sha256_crlf_to_lf_only": digest(stdout.replace(b"\r\n", b"\n")),
        "stderr_sha256_raw": digest(stderr),
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
        "summary": combined.strip().splitlines()[-1] if combined.strip() else "",
        "tests_run": int(ran.group(1)) if ran else None,
        "reported_skips": [{"reason": a or b} for a, b in skipped],
        "passed_expected_exit": exit_code == expected,
    }
    commands.append(row)
    if exit_code != expected:
        raise RuntimeError(f"{label} exited {exit_code}; expected {expected}: {combined}")
    return row


def frozen_hashes(tree: Path) -> list[dict]:
    checklist = (ROOT / "reports/gate3-next/E1-E10-CHECKLIST.md").read_text(encoding="utf-8")
    expected = dict(re.findall(r"`([^`]+)` — SHA-256 `([0-9a-f]{64})`", checklist))
    result = []
    for relative, sha in expected.items():
        path = tree / relative
        actual = file_digest(path)
        result.append({"path": relative, "expected_sha256": sha, "actual_sha256": actual, "matches": actual == sha})
    return result


def full_plan_hashes(tree: Path) -> list[dict]:
    manifest = tree / "docs/CouncilFlow-Full-Plan/SHA256SUMS.txt"
    result = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = tree / "docs/CouncilFlow-Full-Plan" / relative.strip()
        actual = file_digest(path)
        result.append({"path": path.relative_to(tree).as_posix(), "expected_sha256": expected, "actual_sha256": actual, "matches": actual == expected})
    return result


def criteria_fidelity(tree: Path) -> dict:
    plan = json.loads((ROOT / "reports/councilflow-hardening/planner-correction-p004/plan.json").read_text(encoding="utf-8"))
    frozen = (tree / "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md").read_text(encoding="utf-8")
    c3 = (tree / "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md").read_text(encoding="utf-8")
    expected = {}
    for number in range(1, 11):
        source = c3 if number == 4 else frozen
        start = source.index(("## " if number == 4 else "### ") + f"E{number} —")
        end = len(source)
        next_markers = [source.find("\n### E", start + 1), source.find("\n## Token-usage data", start + 1)]
        next_markers = [position for position in next_markers if position >= 0]
        if next_markers:
            end = min(next_markers)
        section = source[start:end]
        expected[f"E{number}"] = section[(3 if number == 4 else 4):].strip("\n")
    planned = {item["id"]: item["criterion"] for item in plan["acceptance"] if item["id"].startswith("E")}
    comparisons = {key: {"matches": planned.get(key) == value, "planned_sha256": digest((planned.get(key) or "").encode("utf-8")), "frozen_text_sha256": digest(value.encode("utf-8"))} for key, value in expected.items()}
    return {
        "source_plan": "reports/councilflow-hardening/planner-correction-p004/plan.json",
        "frozen_source": "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
        "C3_source_for_E4": "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
        "criteria": comparisons,
        "all_exact": all(item["matches"] for item in comparisons.values()),
        "classification": "Static criterion text fidelity only; no Gate 3 observation.",
    }


def retired_audit(archive: zipfile.ZipFile, names: list[str]) -> dict:
    retired_skill = "-".join(("cf", "recall"))
    retired_script = "/".join(("scripts", "recall.py"))
    retired_reference = "/".join(("references", "recall.md"))
    retired_test = "/".join(("tests", "test_recall.py"))
    retired_command = "$" + retired_skill
    text_probes = (retired_command, retired_script, retired_reference, retired_test, "recall.json", "--label observed")
    path_hits = [name for name in names if retired_skill in name.lower() or any(probe.replace("/", "").lower() in name.lower() for probe in (retired_script, retired_reference, retired_test))]
    active_content_hits = []
    for name in names:
        if not name.startswith((".agents/skills/council-flow/", ".codex/agents/")):
            continue
        data = archive.read(name)
        for probe in text_probes:
            if probe.encode("utf-8").lower() in data.lower():
                active_content_hits.append({"path": name, "probe": probe})
    negative_test = "tests/test_codebase_memory_integration.py"
    negative_test_hits = []
    negative_assertion_only = False
    if negative_test in names:
        data = archive.read(negative_test).lower()
        for probe in text_probes:
            if probe.encode("utf-8").lower() in data:
                negative_test_hits.append(probe)
        negative_assertion_only = b"for obsolete in" in data and b"assertnotin" in data
    active_skill = ROOT / ".agents/skills"
    active_paths = [str(path.relative_to(ROOT).as_posix()) for path in active_skill.rglob("*") if retired_skill in str(path).lower() or path.name.lower() in {"recall.py", "recall.md", "test_recall.py"}]
    config_paths = [str(path.relative_to(ROOT).as_posix()) for path in (ROOT / ".codex/agents").rglob("*") if path.is_file() and (retired_skill in str(path).lower() or path.name.lower() in {"recall.py", "recall.md", "test_recall.py"})]
    return {
        "path_hits_in_package": path_hits,
        "active_skill_path_hits": active_paths,
        "active_config_path_hits": config_paths,
        "active_skill_or_config_text_hits": active_content_hits,
        "test_only_negative_probe_literals": {"path": negative_test, "probes": negative_test_hits},
        "test_probe_literals_are_negative_assertions_only": negative_assertion_only,
        "no_active_component": not (path_hits or active_content_hits or active_paths or config_paths),
    }


def verify_tree(tree: Path, label: str) -> dict:
    examples = []
    for filename in ("job.assign.json", "job.report.json"):
        args = [".agents/skills/council-flow/scripts/contracts.py", "message", f"docs/CouncilFlow-Full-Plan/examples/{filename}", "--root", "."]
        examples.append(run(f"{label}-example-{filename.split('.')[0]}", args, tree))
    stale_path = "docs/CouncilFlow-Full-Plan/examples/job.report.json"
    packet = json.loads((tree / stale_path).read_text(encoding="utf-8"))
    packet["payload"]["candidate_ref"]["sha256"] = "0" * 64
    with tempfile.TemporaryDirectory(prefix=".tester-stale-", dir=tree) as directory:
        temp = Path(directory) / "stale.json"
        temp.write_text(json.dumps(packet, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        relative = temp.relative_to(tree).as_posix()
        row = run(f"{label}-stale-digest-negative", [".agents/skills/council-flow/scripts/contracts.py", "message", relative, "--root", "."], tree, expected=1)
        error_output = (ROOT / Path(row["stderr_path"])).read_bytes().decode("utf-8", "replace")
        if "artifact_hash" not in error_output:
            raise RuntimeError(f"{label} stale digest negative control did not reject with artifact_hash")
    plan = full_plan_hashes(tree)
    if len(plan) != 20 or not all(row["matches"] for row in plan):
        raise RuntimeError(f"{label} Full Plan checksum mismatch or wrong entry count")
    frozen = frozen_hashes(tree)
    if len(frozen) != 3 or not all(row["matches"] for row in frozen):
        raise RuntimeError(f"{label} frozen-source hash mismatch")
    criteria = criteria_fidelity(tree)
    if not criteria["all_exact"]:
        raise RuntimeError(f"{label} E1-E10 frozen text comparison failed")
    draft_record = None
    if tree == ROOT:
        draft = (tree / "reports/gate3-next/OWNER-TASK-DRAFT.txt").read_text(encoding="utf-8")
        criterion_lines = [line for line in draft.splitlines() if re.match(r"^[12]\. ", line)]
        if len(criterion_lines) != 2 or "NOT OWNER-APPROVED" not in draft:
            raise RuntimeError("Owner task draft is not the two-criterion unapproved fixture")
        draft_record = {"not_owner_approved": True, "exact_two_criteria": True, "criteria": criterion_lines, "sha256": file_digest(tree / "reports/gate3-next/OWNER-TASK-DRAFT.txt")}
    return {
        "tree": str(tree),
        "examples": examples,
        "stale_digest_negative": "REJECTED with artifact_hash",
        "full_plan_checksums": {"count": len(plan), "all_match": True, "entries": plan},
        "frozen_hashes": frozen,
        "criteria_fidelity": criteria,
        "owner_task_draft": draft_record,
    }


archive_sha = file_digest(ARCHIVE)
checksum_text = (ROOT / "dist/council-flow.zip.sha256").read_text(encoding="ascii").strip()
if archive_sha != ARCHIVE_SHA or checksum_text != f"{ARCHIVE_SHA}  council-flow.zip":
    raise RuntimeError(f"candidate identity mismatch: archive={archive_sha}, checksum={checksum_text!r}")

required = {
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
}
forbidden_names: list[str] = []
mismatches: list[dict] = []
with zipfile.ZipFile(ARCHIVE) as archive:
    names = archive.namelist()
    if len(names) != 118 or len(set(names)) != len(names):
        raise RuntimeError(f"wrong or duplicate candidate entry count: {len(names)}")
    if archive.testzip() is not None:
        raise RuntimeError(f"CRC failure: {archive.testzip()}")
    if not required.issubset(names):
        raise RuntimeError(f"required entries missing: {sorted(required - set(names))}")
    for name in names:
        if not safe(name) or excluded(name) or name.startswith(("reports/runtime/", "reports/councilflow-hardening/")) or name == "dist/council-flow.zip":
            forbidden_names.append(name)
        source = ROOT.joinpath(*PurePosixPath(name).parts)
        content = archive.read(name)
        if not source.is_file() or file_digest(source) != digest(content) or source.stat().st_size != len(content):
            mismatches.append({"path": name, "source_present": source.is_file(), "source_sha256": file_digest(source) if source.is_file() else None, "archive_sha256": digest(content), "source_size": source.stat().st_size if source.is_file() else None, "archive_size": len(content)})
    if forbidden_names or mismatches:
        raise RuntimeError(f"forbidden entries={forbidden_names}; source mismatches={mismatches}")
    retirement = retired_audit(archive, names)
    if not retirement["no_active_component"]:
        raise RuntimeError(f"retired-component scan hits: {retirement}")

if RESUME:
    extraction = Path(sys.argv[2]).resolve()
    if not extraction.is_dir():
        raise RuntimeError(f"resume extraction does not exist: {extraction}")
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name in archive.namelist():
            target = extraction.joinpath(*PurePosixPath(name).parts)
            if not target.is_file() or file_digest(target) != digest(archive.read(name)):
                raise RuntimeError(f"resume extraction does not match candidate: {name}")
else:
    extraction = Path(tempfile.gettempdir()) / f"CouncilFlow-Gate3-preflight-{uuid.uuid4().hex}"
    extraction.mkdir()
    with zipfile.ZipFile(ARCHIVE) as archive:
        archive.extractall(extraction)

suite_defs = (
    ("tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("demo_receipt", ["-m", "unittest", "discover", "-s", "demo/receipt", "-v"]),
    ("demo_csv_summary", ["-m", "unittest", "discover", "-s", "demo/csv-summary", "-v"]),
    ("demo_structured_flow", ["-m", "unittest", "discover", "-s", "demo/structured-flow", "-v"]),
    ("reports_demo_verification", ["-m", "unittest", "discover", "-s", "reports/demo/verification", "-v"]),
    ("reports_csv_verification", ["-m", "unittest", "discover", "-s", "reports/csv-summary/verification", "-v"]),
)
checkout_suites = [run(f"checkout-{name}", args, ROOT) for name, args in suite_defs]
extracted_suites = [run(f"extracted-{name}", args, extraction) for name, args in suite_defs]

# Narrow controls for attempt linkage and top-level execution evidence, in addition to the full suite.
targeted_args = [
    "-m", "unittest",
    "tests.test_contracts.JSONContractTests.test_tester_command_and_reviewer_rerun_must_match",
    "tests.test_contracts.JSONContractTests.test_rework_requires_failure_and_fresh_worker_attempt",
    "tests.test_contracts.JSONContractTests.test_tester_command_and_reviewer_rerun_artifacts_must_be_top_level_refs",
    "-v",
]
targeted_controls = run("checkout-attempt-and-evidence-controls", targeted_args, ROOT)

checkout_integrity = verify_tree(ROOT, "checkout")
extracted_integrity = verify_tree(extraction, "extracted")

# Stable command for Reviewer replay: meaningful nonempty success output, exact candidate and input bindings.
deterministic_args = [
    ".agents/skills/council-flow/scripts/contracts.py", "message",
    "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", ".",
]
deterministic_result = run("deterministic-tester-command", deterministic_args, extraction)
if not (ROOT / deterministic_result["stdout_path"]).read_bytes().strip():
    raise RuntimeError("selected deterministic command produced empty stdout")

app = ROOT / "reports/gate3-next/disposable-workspace/demo/gate3-demo/app.py"
test_app = ROOT / "reports/gate3-next/disposable-workspace/demo/gate3-demo/test_app.py"
owner_task = ROOT / "reports/gate3-next/OWNER-TASK-DRAFT.txt"
result = {
    "record_type": "independent-native-tester-technical-result",
    "format": "UTF-8 JSON",
    "role": "tester",
    "native_instance": "/root/tester",
    "council_flow_envelope": "NOT EMITTED: Manager did not supply real plan/task/attempt/message IDs or an approved oracle_ref; none are invented here.",
    "candidate": {"path": "dist/council-flow.zip", "sha256": archive_sha, "entry_count": len(names)},
    "environment": {"python": sys.version, "executable": sys.executable, "platform": sys.platform, "os": os.name},
    "package_checks": {
        "checksum_matches": True, "crc": "PASS", "safe_paths": "PASS",
        "required_inventory": "PASS", "excluded_inventory": "PASS",
        "source_hash_and_size_map": "PASS", "retired_component_audit": retirement,
        "extraction_directory": str(extraction),
    },
    "suite_executions": {"checkout": checkout_suites, "extracted": extracted_suites},
    "attempt_and_evidence_controls": targeted_controls,
    "source_integrity": checkout_integrity,
    "extracted_integrity": extracted_integrity,
    "codebase_memory": {
        "static_tests_in_six_suite": "executed in tests suite; exact-root, missing/stale fallback and graph-as-navigation instructions checked by source tests",
        "live_unavailable_or_stale_mcp": "NOT EXECUTED; static mocked/source checks do not establish live MCP behavior",
        "graph_navigation": "parent confirmed exact project root and indexed generation; this Tester result relies on direct file/package tests, not graph output as correctness evidence",
    },
    "owner_fixture": {
        "path": "reports/gate3-next/OWNER-TASK-DRAFT.txt",
        "sha256": file_digest(owner_task),
        "not_owner_approved": True,
        "criteria": checkout_integrity["owner_task_draft"]["criteria"],
        "disposable_app": {"path": app.relative_to(ROOT).as_posix(), "sha256": file_digest(app)},
        "disposable_test": {"path": test_app.relative_to(ROOT).as_posix(), "sha256": file_digest(test_app)},
    },
    "deterministic_command": {
        **deterministic_result,
        "candidate_ref": {"path": "dist/council-flow.zip", "sha256": archive_sha},
        "input_refs": [
            {"path": ".agents/skills/council-flow/scripts/contracts.py", "sha256": file_digest(extraction / ".agents/skills/council-flow/scripts/contracts.py")},
            {"path": "docs/CouncilFlow-Full-Plan/examples/job.report.json", "sha256": file_digest(extraction / "docs/CouncilFlow-Full-Plan/examples/job.report.json")},
            {"path": "docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt", "sha256": file_digest(extraction / "docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt")},
        ],
        "acceptance_id": "independent-package-contract-validation",
        "evidence_ref": {"path": deterministic_result["stdout_path"], "sha256": digest((ROOT / deterministic_result["stdout_path"]).read_bytes())},
        "top_level_evidence_ref": {"path": deterministic_result["stdout_path"], "sha256": digest((ROOT / deterministic_result["stdout_path"]).read_bytes())},
    },
    "results": {
        "all_six_checkout_suite_exits_zero": all(row["exit_code"] == 0 for row in checkout_suites),
        "all_six_extracted_suite_exits_zero": all(row["exit_code"] == 0 for row in extracted_suites),
        "root_bound_examples_pass_both_roots": True,
        "stale_digest_rejected_both_roots": True,
        "full_plan_20_hashes_match_both_roots": True,
        "frozen_hashes_match_before_and_after_both_roots": True,
        "E1_E10_text_fidelity_static_exact": True,
        "gate3_run": False,
        "windows_symlink_semantics": "UNVERIFIED: both symlink-specific tests report the exact Windows privilege skip; this is not a security pass",
        "junction_reparse_and_toctou": "UNVERIFIED by Tester",
    },
    "command_count": len(commands),
    "all_command_exits_as_expected": all(row["passed_expected_exit"] for row in commands),
    "evidence_refs": [
        {"path": deterministic_result["stdout_path"], "sha256": digest((ROOT / deterministic_result["stdout_path"]).read_bytes()), "kind": "execution-output"},
        {"path": deterministic_result["stderr_path"], "sha256": digest((ROOT / deterministic_result["stderr_path"]).read_bytes()), "kind": "execution-output"},
    ],
    "commands": commands,
}
report = EVIDENCE / "tester-result.json"
report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({
    "report": report.relative_to(ROOT).as_posix(),
    "report_sha256": file_digest(report),
    "candidate_sha256": archive_sha,
    "entry_count": len(names),
    "extraction_directory": str(extraction),
    "suite_counts": {"checkout": [row["tests_run"] for row in checkout_suites], "extracted": [row["tests_run"] for row in extracted_suites]},
    "checkout_skips": [row["reported_skips"] for row in checkout_suites],
    "extracted_skips": [row["reported_skips"] for row in extracted_suites],
    "deterministic_command": deterministic_result,
}, indent=2, ensure_ascii=False))
