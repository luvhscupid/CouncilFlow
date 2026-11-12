from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path.cwd().resolve()
OUT = ROOT / "reports" / "councilflow-finalization" / "tester"
ARCHIVE = ROOT / "dist" / "council-flow.zip"
EXPECTED_ARCHIVE_SHA256 = "9e569fd99e23f334927a3771fcf145172b116f93a0912008f49d0e62db13a482"
EXPECTED_MANIFEST_SHA256 = "6834a9995928afa058c12c5aee1da2dcdbc25afbf15f69e6076bdfc6b4c82992"
OUT.mkdir(parents=True, exist_ok=True)
EXECUTABLE = sys.executable
SPECS = [
    ("tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("demo-receipt", ["-m", "unittest", "discover", "-s", "demo/receipt", "-v"]),
    ("demo-csv-summary", ["-m", "unittest", "discover", "-s", "demo/csv-summary", "-v"]),
    ("demo-structured-flow", ["-m", "unittest", "discover", "-s", "demo/structured-flow", "-v"]),
    ("reports-demo-verification", ["-m", "unittest", "discover", "-s", "reports/demo/verification", "-v"]),
    ("reports-csv-verification", ["-m", "unittest", "discover", "-s", "reports/csv-summary/verification", "-v"]),
]


def sha(data: bytes) -> str:
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


def run(name: str, args: list[str], cwd: Path, *, tag: str, criterion: str, inputs: list[dict]) -> dict:
    completed = subprocess.run([EXECUTABLE, *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stdout_path = OUT / f"{tag}.stdout.bin"
    stderr_path = OUT / f"{tag}.stderr.bin"
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    stderr_text = completed.stderr.decode("utf-8", errors="replace")
    ran_match = re.search(r"Ran (\d+) tests?", stderr_text)
    skipped_match = re.search(r"OK \(skipped=(\d+)\)", stderr_text)
    if ran_match:
        summary = f"Ran {ran_match.group(1)} tests; " + (skipped_match.group(0) if skipped_match else "OK" if completed.returncode == 0 else "FAILED")
    else:
        summary = (completed.stdout + completed.stderr).decode("utf-8", errors="replace").strip()[-500:]
    return {
        "name": name,
        "command": EXECUTABLE,
        "arguments": args,
        "working_directory": str(cwd),
        "candidate_ref": {"artifact_id": "CF-FINAL-DIST-ARCHIVE", "path": "dist/council-flow.zip", "sha256": EXPECTED_ARCHIVE_SHA256, "kind": "candidate-archive"},
        "input_refs": inputs,
        "criterion_id": criterion,
        "exit_code": completed.returncode,
        "stdout_sha256_crlf_to_lf_only": sha(completed.stdout.replace(b"\r\n", b"\n")),
        "stderr_sha256_raw": sha(completed.stderr),
        "summary": summary,
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
        "stdout_sha256_raw": sha(completed.stdout),
        "skipped": int(skipped_match.group(1)) if skipped_match else 0,
        "test_count": int(ran_match.group(1)) if ran_match else None,
    }


def artifact(path: str, kind: str) -> dict:
    data = (ROOT / path).read_bytes()
    return {"artifact_id": path.replace("/", "-").replace(".", "-"), "path": path, "sha256": sha(data), "kind": kind}


def assert_plan_fidelity() -> dict:
    plan = json.loads((ROOT / "reports/councilflow-hardening/planner-correction-p004/plan.json").read_text(encoding="utf-8"))
    frozen = (ROOT / "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md").read_text(encoding="utf-8")
    erratum = (ROOT / "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md").read_text(encoding="utf-8")
    expected: dict[str, str] = {}
    for number in range(1, 11):
        label = f"E{number} —"
        source = erratum if number == 4 else frozen
        start = source.index(("## " if number == 4 else "### ") + label)
        end = len(source)
        next_markers = [source.find("\n### E", start + 1), source.find("\n## Token-usage data", start + 1)]
        next_markers = [pos for pos in next_markers if pos >= 0]
        if next_markers:
            end = min(next_markers)
        section = source[start:end]
        heading_prefix = "## " if number == 4 else "### "
        expected[f"E{number}"] = section[len(heading_prefix):].strip("\n")
    planned = {item["id"]: item["criterion"] for item in plan["acceptance"] if item["id"].startswith("E")}
    results = {key: planned.get(key) == value for key, value in expected.items()}
    record = {"source_plan": "reports/councilflow-hardening/planner-correction-p004/plan.json", "frozen_source": "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md", "C3_source_for_E4": "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md", "criteria": results, "all_exact": all(results.values()), "classification": "Static byte/text fidelity only; no Gate 3 observation."}
    (OUT / "criteria-fidelity.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def verify_root(tree: Path, label: str) -> dict:
    manifest_path = tree / "docs/CouncilFlow-Full-Plan/SHA256SUMS.txt"
    checksum_results = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        actual = sha((tree / "docs/CouncilFlow-Full-Plan" / name).read_bytes())
        checksum_results.append({"path": name, "expected": expected, "actual": actual, "passed": expected == actual})
    examples = []
    for name in ("job.assign.json", "job.report.json"):
        args = [".agents/skills/council-flow/scripts/contracts.py", "message", f"docs/CouncilFlow-Full-Plan/examples/{name}", "--root", "."]
        examples.append(run(f"{label}-example-{name}", args, tree, tag=f"{label}-example-{name}", criterion="P3-B", inputs=[artifact(f"docs/CouncilFlow-Full-Plan/examples/{name}", "input")]))
    return {"root": str(tree), "manifest_entry_count": len(checksum_results), "all_manifest_checksums_valid": all(x["passed"] for x in checksum_results), "checksums": checksum_results, "examples": examples}


archive_data = ARCHIVE.read_bytes()
if sha(archive_data) != EXPECTED_ARCHIVE_SHA256:
    raise SystemExit("candidate archive hash changed since Manager assignment")
manifest_file = ROOT / "reports/councilflow-finalization/worker/package-manifest.json"
if sha(manifest_file.read_bytes()) != EXPECTED_MANIFEST_SHA256:
    raise SystemExit("package manifest hash changed since Manager assignment")
manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
with zipfile.ZipFile(ARCHIVE) as archive:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise SystemExit("duplicate archive paths")
    if archive.testzip() is not None:
        raise SystemExit("CRC failure")
    if not all(safe_path(name) for name in names):
        raise SystemExit("unsafe archive path")
    if len(names) != len(manifest):
        raise SystemExit("archive/manifest entry-count mismatch")
    source_mapping = []
    for entry in manifest:
        data = archive.read(entry["path"])
        current = (ROOT / entry["path"]).read_bytes()
        source_mapping.append({"path": entry["path"], "manifest_sha256": entry["sha256"], "archive_sha256": sha(data), "source_sha256": sha(current), "all_equal": sha(data) == entry["sha256"] == sha(current)})
    required = {
        ".agents/skills/council-flow/SKILL.md",
        ".agents/skills/council-flow/references/codebase-memory.md",
        ".agents/skills/council-flow/scripts/contracts.py",
        ".agents/skills/council-flow/policies/roles.yaml",
        "tests/test_contracts.py",
        "tests/test_codebase_memory_integration.py",
        "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
        "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
        "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
    }
    forbidden_prefixes = (".git/", "reports/councilflow-finalization/", "reports/gate3-next/", "reports/councilflow-hardening/")
    forbidden_paths = [name for name in names if name.startswith(forbidden_prefixes) or any(x in name.lower() for x in (".pyc", "credentials", "token.json"))]
    archive_scan = {"entry_count": len(names), "safe_paths": all(safe_path(name) for name in names), "unique_paths": len(names) == len(set(names)), "crc": "PASS", "required_entries_present": sorted(required - set(names)) == [], "forbidden_entries": forbidden_paths, "source_mapping_all_equal": all(row["all_equal"] for row in source_mapping), "source_mapping": source_mapping}

suite_records = []
source_inputs = [artifact("reports/councilflow-finalization/worker/candidate-manifest.json", "candidate-manifest")]
for name, args in SPECS:
    suite_records.append(run(name, args, ROOT, tag=f"source-{name}", criterion="P3-A", inputs=source_inputs))

with tempfile.TemporaryDirectory(prefix="councilflow-independent-test-") as temp_dir:
    extracted = Path(temp_dir).resolve()
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name in archive.namelist():
            destination = (extracted / Path(*PurePosixPath(name).parts)).resolve()
            if extracted not in destination.parents:
                raise SystemExit(f"extraction path escapes temp root: {name}")
        archive.extractall(extracted)
    extract_suite_records = []
    for name, args in SPECS:
        extract_suite_records.append(run(name, args, extracted, tag=f"extracted-{name}", criterion="P3-C", inputs=[{"artifact_id":"CF-FINAL-DIST-ARCHIVE","path":"dist/council-flow.zip","sha256":EXPECTED_ARCHIVE_SHA256,"kind":"candidate-archive"}]))
    extracted_checks = verify_root(extracted, "extracted")

    # Mutate only an isolated temp copy of the genuine example and its real fixture.
    negative_root = extracted / "negative-control"
    example_rel = Path("docs/CouncilFlow-Full-Plan/examples")
    (negative_root / example_rel).mkdir(parents=True)
    (negative_root / ".agents/skills/council-flow/scripts").mkdir(parents=True)
    shutil.copy2(extracted / example_rel / "job.report.json", negative_root / example_rel / "job.report.json")
    shutil.copy2(extracted / example_rel / "synthetic-candidate.txt", negative_root / example_rel / "synthetic-candidate.txt")
    shutil.copy2(extracted / ".agents/skills/council-flow/scripts/contracts.py", negative_root / ".agents/skills/council-flow/scripts/contracts.py")
    candidate_file = negative_root / example_rel / "synthetic-candidate.txt"
    candidate_file.write_bytes(candidate_file.read_bytes() + b"tamper\n")
    stale_args = [".agents/skills/council-flow/scripts/contracts.py", "message", "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", "."]
    stale_result = run("stale-hash-negative-control", stale_args, negative_root, tag="stale-hash-negative-control", criterion="P3-B", inputs=[{"artifact_id":"isolated-tampered-fixture","path":"docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt","sha256":sha(candidate_file.read_bytes()),"kind":"negative-control-input"}])
    stale_result["expected_nonzero"] = True
    stale_result["passed_expected_rejection"] = stale_result["exit_code"] != 0

source_checks = verify_root(ROOT, "source")
protected = []
protected_paths = [
    "docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md",
    "docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md",
]
for path in protected_paths:
    current = (ROOT / path).read_bytes()
    baseline = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    protected.append({"path": path, "sha256": sha(current), "matches_HEAD": current == baseline})
criteria = assert_plan_fidelity()

# Verify Codebase Memory remains available as the exact-root navigation path and not release evidence.
context_path = ROOT / ".agents/skills/council-flow/references/codebase-memory.md"
context_text = context_path.read_text(encoding="utf-8")
codebase_policy = {
    "path": ".agents/skills/council-flow/references/codebase-memory.md",
    "sha256": sha(context_path.read_bytes()),
    "exact_root_binding_present": "equals the authorized repository root exactly" in context_text,
    "navigation_not_verification_present": "not correctness proof or permission authority" in context_text,
    "direct_fallback_present": "continue ordinary CouncilFlow" in context_text,
}

all_runs = suite_records + extract_suite_records
summary = {
    "protocol": "council-flow-test-evidence-1.0",
    "candidate_archive_sha256": EXPECTED_ARCHIVE_SHA256,
    "actual_python_executable": EXECUTABLE,
    "suite_command_count": len(all_runs),
    "suite_runs": all_runs,
    "source_checks": source_checks,
    "extracted_checks": extracted_checks,
    "archive_checks": archive_scan,
    "source_byte_mapping_all_equal": all(row["all_equal"] for row in source_mapping),
    "protected_sources_match_HEAD": all(row["matches_HEAD"] for row in protected),
    "protected_sources": protected,
    "criteria_fidelity": criteria,
    "Codebase_Memory_policy": codebase_policy,
    "stale_hash_negative_control": stale_result,
    "total_tests": sum(row["test_count"] or 0 for row in all_runs),
    "total_skipped": sum(row["skipped"] for row in all_runs),
    "all_suite_exits_zero": all(row["exit_code"] == 0 for row in all_runs),
}
(OUT / "execution.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"executable": EXECUTABLE, "suites": len(all_runs), "test_count": summary["total_tests"], "skipped": summary["total_skipped"], "all_suite_exits_zero": summary["all_suite_exits_zero"], "archive_checks": {k:v for k,v in archive_scan.items() if k!="source_mapping"}, "source_examples": source_checks["examples"], "extracted_examples": extracted_checks["examples"], "stale_hash_rejected": stale_result["passed_expected_rejection"], "criteria_all_exact": criteria["all_exact"], "protected_match_HEAD": summary["protected_sources_match_HEAD"]}, indent=2, ensure_ascii=False))
