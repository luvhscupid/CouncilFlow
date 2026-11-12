"""Independent Windows checkout/extraction checks; no final source/archive edits."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "reports/councilflow-final-release-audit/worker/final/candidate-manifest.json"
EXPECTED = "9e5ae1a046221deb96a345815ef9ac72746f023ccd01bdaf34984ea224c4a113"
MANIFEST = json.loads(MANIFEST_PATH.read_bytes())
SUITES = ["tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification"]
EXECUTIONS = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(label, arguments, cwd=ROOT):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.run([sys.executable, "-B", *arguments], cwd=cwd, capture_output=True, env=env)
    stdout_path, stderr_path = OUT / (label + ".stdout.bin"), OUT / (label + ".stderr.bin")
    stdout_path.write_bytes(process.stdout)
    stderr_path.write_bytes(process.stderr)
    record = {"label": label, "command": sys.executable, "arguments": ["-B", *arguments],
              "workdir": str(cwd), "exit_code": process.returncode,
              "stdout_sha256": digest(process.stdout.replace(b"\r\n", b"\n")),
              "raw_stdout_sha256": digest(process.stdout), "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
              "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
              "candidate_manifest_sha256": EXPECTED}
    text = process.stderr.decode("utf-8", errors="replace")
    count = re.search(r"Ran (\d+) tests? in", text)
    if count:
        skipped = re.search(r"OK \(skipped=(\d+)\)", text)
        failures = re.search(r"FAILED \(([^)]+)\)", text)
        record["run"] = int(count[1])
        record["skipped"] = int(skipped[1]) if skipped else 0
        record["result"] = "passed" if process.returncode == 0 else "failed"
        record["failure_summary"] = failures[1] if failures else None
        record["passed"] = record["run"] - record["skipped"] if process.returncode == 0 else None
    EXECUTIONS.append(record)
    return record


def verify_source(root):
    for entry in MANIFEST["files"]:
        data = (root / entry["path"]).read_bytes()
        assert len(data) == entry["size"] and digest(data) == entry["sha256"], entry["path"]


def main():
    assert digest(MANIFEST_PATH.read_bytes()) == EXPECTED
    verify_source(ROOT)
    archive_path = ROOT / MANIFEST["archive"]["path"]
    archive_bytes = archive_path.read_bytes()
    assert digest(archive_bytes) == MANIFEST["archive"]["sha256"]
    baseline = json.loads((ROOT / "reports/councilflow-final-release-audit/baseline.json").read_bytes())
    assert all(digest((ROOT / p).read_bytes()) == h for p, h in baseline["frozen"].items())
    before = {p: digest((ROOT / p).read_bytes()) for p in baseline["frozen"]}
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        expected_names = [entry["path"] for entry in MANIFEST["files"]]
        assert names == expected_names
        assert len(names) == len(set(names)) == len({n.casefold() for n in names}) == 117
        assert archive.testzip() is None
        for info in archive.infolist():
            name = info.filename
            assert not PurePosixPath(name).is_absolute() and not PureWindowsPath(name).drive
            assert "\\" not in name and all(p not in {"", ".", ".."} for p in name.split("/"))
            assert not stat.S_ISLNK(info.external_attr >> 16)
            assert not any(p.lower() in {".git", "__pycache__", ".pytest_cache", ".env", ".codex-runtime", "runtime"} for p in name.split("/"))
            assert not name.startswith(("dist/", "reports/councilflow-final-release-audit/"))
            assert archive.read(name) == (ROOT / name).read_bytes()
        with tempfile.TemporaryDirectory(prefix="cf-tester-extract-") as directory:
            extracted = Path(directory).resolve()
            assert extracted.is_relative_to(Path(tempfile.gettempdir()).resolve())
            archive.extractall(extracted)
            verify_source(extracted)
            for index, suite in enumerate(SUITES):
                run("extraction-" + str(index), ["-m", "unittest", "discover", "-s", suite, "-v"], extracted)
            run("extraction-policy", [".agents/skills/council-flow/scripts/contracts.py", "policy", ".agents/skills/council-flow/policies/roles.yaml"], extracted)
    for index, suite in enumerate(SUITES):
        run("checkout-" + str(index), ["-m", "unittest", "discover", "-s", suite, "-v"])
    for label, script, arguments in [
        ("CA01-06", "contract-audit/negative_controls.py", []),
        ("adversarial", "contract-audit/extra/challenge.py", ["--current"]),
        ("api", "contract-audit/extra/api_controls.py", ["--current"]),
    ]:
        run(label, ["reports/councilflow-final-release-audit/" + script, *arguments])
    run("policy", [".agents/skills/council-flow/scripts/contracts.py", "policy", ".agents/skills/council-flow/policies/roles.yaml"])
    run("deterministic-1", ["reports/councilflow-final-release-audit/tester/deterministic.py"])
    run("deterministic-2", ["reports/councilflow-final-release-audit/tester/deterministic.py"])
    assert EXECUTIONS[-1]["stdout_sha256"] == EXECUTIONS[-2]["stdout_sha256"]
    verify_source(ROOT)
    assert digest(archive_path.read_bytes()) == MANIFEST["archive"]["sha256"]
    assert all(digest((ROOT / p).read_bytes()) == h for p, h in before.items())
    (OUT / "windows-executions.json").write_text(json.dumps(EXECUTIONS, indent=2) + "\n", encoding="utf-8")
    package = {"archive_sha256": digest(archive_bytes), "entries": 117, "crc": "PASS",
               "safe_names_unique_casefold": "PASS", "source_and_extracted_bytes": "PASS", "frozen": before,
               "source_hashes_unchanged_after": True, "current_evidence_excluded": True,
               "limits": "Source bytes/container checks do not prove host identity, Owner approval or OS isolation."}
    (OUT / "package-checks.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"executions": [{k:v for k,v in x.items() if k in {"label", "run", "passed", "skipped", "exit_code", "stdout_sha256"}} for x in EXECUTIONS],
                      "all_exit_zero": all(x["exit_code"] == 0 for x in EXECUTIONS)}, indent=2))
    return 0 if all(x["exit_code"] == 0 for x in EXECUTIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
