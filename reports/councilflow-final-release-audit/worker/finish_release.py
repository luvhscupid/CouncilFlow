"""Worker developer checks and immutable candidate inventory; not independent approval."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "final"
OUT.mkdir(exist_ok=False)
SUITES = ["tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(name, arguments, cwd=ROOT, executable=sys.executable):
    result = subprocess.run([executable, *arguments], cwd=cwd, capture_output=True)
    (OUT / (name + ".stdout.bin")).write_bytes(result.stdout)
    (OUT / (name + ".stderr.bin")).write_bytes(result.stderr)
    stderr = result.stderr.decode("utf-8", errors="replace")
    total = re.search(r"Ran (\d+) tests?", stderr)
    skipped = re.search(r"skipped=(\d+)", stderr)
    record = {"name": name, "command": executable, "arguments": arguments, "cwd": str(cwd),
              "exit_code": result.returncode,
              "stdout_sha256": digest(result.stdout.replace(b"\r\n", b"\n")),
              "stderr_sha256_raw": digest(result.stderr),
              "tests_run": int(total[1]) if total else None,
              "skipped": int(skipped[1]) if skipped else 0}
    records.append(record)
    (OUT / "final-executions.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"developer check failed: {name}; preserved raw outputs")


records = []
run("build", ["tools/build_release.py"])
for index, suite in enumerate(SUITES):
    run(f"checkout-{index}", ["-m", "unittest", "discover", "-s", suite, "-v"])
for name, arguments in [
    ("CA01-06", ["reports/councilflow-final-release-audit/contract-audit/negative_controls.py"]),
    ("CA07-current", ["reports/councilflow-final-release-audit/contract-audit/extra/challenge.py", "--current"]),
    ("CA08-current", ["reports/councilflow-final-release-audit/contract-audit/extra/api_controls.py", "--current"]),
    ("examples", [".agents/skills/council-flow/scripts/contracts.py", "message",
                  "docs/CouncilFlow-Full-Plan/examples/job.assign.json",
                  "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", "."]),
    ("policy", [".agents/skills/council-flow/scripts/contracts.py", "policy",
                ".agents/skills/council-flow/policies/roles.yaml"]),
]:
    run(name, arguments)
run("diff-check", ["-c", "core.whitespace=cr-at-eol", "diff", "--check", "--",
                   ".agents", "tests", "demo/receipt", "demo/structured-flow", "README.md", "RELEASE.md", "tools"],
    executable="git")

package = json.loads((ROOT / "dist/council-flow.manifest.json").read_text(encoding="utf-8"))
archive = ROOT / "dist/council-flow.zip"
assert digest(archive.read_bytes()) == package["sha256"]
assert (ROOT / "dist/council-flow.zip.sha256").read_text().strip() == package["sha256"] + "  council-flow.zip"
temporary_parent = Path(tempfile.gettempdir()).resolve()
extraction = Path(tempfile.mkdtemp(prefix="councilflow-worker-final-")).resolve()
assert extraction.is_relative_to(temporary_parent)
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    assert len(zipped.namelist()) == len(set(zipped.namelist())) == package["entries"]
    for row in package["files"]:
        name = row["path"]
        pure = PurePosixPath(name)
        assert not pure.is_absolute() and not PureWindowsPath(name).drive and "\\" not in name
        assert all(part not in {"", ".", ".."} for part in name.split("/"))
        assert (extraction / name).resolve().is_relative_to(extraction)
        data = zipped.read(name)
        assert data == (ROOT / name).read_bytes()
        assert len(data) == row["size"] and digest(data) == row["sha256"]
    zipped.extractall(extraction)
for row in package["files"]:
    assert digest((extraction / row["path"]).read_bytes()) == row["sha256"]
for index, suite in enumerate(SUITES):
    run(f"extraction-{index}", ["-m", "unittest", "discover", "-s", suite, "-v"], cwd=extraction)
run("extracted-examples", [".agents/skills/council-flow/scripts/contracts.py", "message",
                          "docs/CouncilFlow-Full-Plan/examples/job.assign.json",
                          "docs/CouncilFlow-Full-Plan/examples/job.report.json", "--root", "."], cwd=extraction)
baseline = json.loads((ROOT / "reports/councilflow-final-release-audit/baseline.json").read_text(encoding="utf-8"))
assert all(digest((ROOT / name).read_bytes()) == value for name, value in baseline["frozen"].items())
assert all(digest((ROOT / row["path"]).read_bytes()) == row["sha256"] for row in package["files"])
verification = {"archive": package["archive"], "sha256": package["sha256"], "entry_count": package["entries"],
                "crc": "PASS", "source_byte_mapping": "PASS", "extracted_byte_mapping": "PASS",
                "safe_names": "PASS", "frozen_hashes": baseline["frozen"],
                "extraction": str(extraction), "extraction_retained": True,
                "developer_only": True, "independent_verification": "Manager must assign fresh Tester and Reviewer"}
(OUT / "package-verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
candidate = {"candidate_id": "FRA-A01-cumulative", "baseline_head": baseline["head"],
             "baseline_manifest_sha256": digest((ROOT / "reports/councilflow-final-release-audit/baseline.json").read_bytes()),
             "files": package["files"], "archive": {"path": package["archive"], "sha256": package["sha256"], "entries": package["entries"]},
             "package_inventory": {"path": "dist/council-flow.manifest.json", "sha256": digest((ROOT / "dist/council-flow.manifest.json").read_bytes())},
             "checksum_file": {"path": "dist/council-flow.zip.sha256", "sha256": digest((ROOT / "dist/council-flow.zip.sha256").read_bytes())},
             "scope": "All allowlisted active skill/config/source/docs/tests/helper and necessary shipped examples; current audit evidence excluded to avoid self-reference.",
             "frozen": baseline["frozen"]}
(OUT / "candidate-manifest.json").write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"candidate": "reports/councilflow-final-release-audit/worker/final/candidate-manifest.json",
                  "sha256": digest((OUT / "candidate-manifest.json").read_bytes()),
                  "archive_sha256": package["sha256"], "entries": package["entries"],
                  "checks": len(records), "extraction": str(extraction)}))
