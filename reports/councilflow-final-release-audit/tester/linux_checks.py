"""Executed by Ubuntu Python; extract exact final archive on native /tmp."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
import tempfile
import zipfile

WINDOWS_ROOT = Path("/mnt/e/Saint/PROJECTS/CouncilFlow-main")
EXPECTED_ARCHIVE = "8a37c6c6b8727cd78070635c86451ff8f6516caa3b584553afb8d2b9e294dc5f"
MANIFEST = json.loads((WINDOWS_ROOT / "reports/councilflow-final-release-audit/worker/final/candidate-manifest.json").read_bytes())
SUITES = ["tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification"]


def main():
    archive_path = WINDOWS_ROOT / "dist/council-flow.zip"
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == EXPECTED_ARCHIVE
    records = []
    with tempfile.TemporaryDirectory(prefix="cf-linux-final-", dir="/tmp") as directory:
        root = Path(directory).resolve()
        assert root.is_relative_to(Path("/tmp").resolve()) and not root.is_relative_to(Path("/mnt"))
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None and len(archive.infolist()) == 117
            for name in archive.namelist():
                assert not PurePosixPath(name).is_absolute() and not PureWindowsPath(name).drive
                assert "\\" not in name and all(p not in {"", ".", ".."} for p in name.split("/"))
            archive.extractall(root)
        for item in MANIFEST["files"]:
            data = (root / item["path"]).read_bytes()
            assert len(data) == item["size"] and hashlib.sha256(data).hexdigest() == item["sha256"]
        for suite in SUITES:
            args = ["-B", "-m", "unittest", "discover", "-s", suite, "-v"]
            process = subprocess.run([sys.executable, *args], cwd=root, capture_output=True,
                                     env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            records.append({"suite": suite, "command": sys.executable, "arguments": args,
                            "workdir": str(root), "exit_code": process.returncode,
                            "stdout_sha256": hashlib.sha256(process.stdout.replace(b"\r\n", b"\n")).hexdigest(),
                            "stdout_base64": base64.b64encode(process.stdout).decode("ascii"),
                            "stderr_base64": base64.b64encode(process.stderr).decode("ascii")})
        spec = importlib.util.spec_from_file_location("linux_contracts", root / ".agents/skills/council-flow/scripts/contracts.py")
        contracts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contracts)
        parent = root / "disposable-path-controls"
        parent.mkdir()
        authorized, outside = parent / "authorized", parent / "outside"
        authorized.mkdir()
        outside.mkdir()
        target = authorized / "actual.txt"
        target.write_bytes(b"inside evidence")
        (outside / "outside.txt").write_bytes(b"outside evidence")
        (authorized / "inside-link.txt").symlink_to(target)
        (authorized / "outside-link.txt").symlink_to(outside / "outside.txt")
        checks = []
        for name, path, data, expected in [
            ("inside-symlink-correct-hash", "inside-link.txt", target.read_bytes(), True),
            ("inside-symlink-stale-hash", "inside-link.txt", b"stale", False),
            ("outside-symlink-correct-hash", "outside-link.txt", (outside / "outside.txt").read_bytes(), False),
        ]:
            reference = {"artifact_id": name, "path": path, "sha256": hashlib.sha256(data).hexdigest(), "kind": "evidence"}
            try:
                contracts.artifact(reference, authorized)
                actual, error = True, None
            except contracts.ContractError as exc:
                actual, error = False, exc.code
            checks.append({"case": name, "expected_allowed": expected, "actual_allowed": actual, "error": error, "passed": actual == expected})
        report = {"platform": sys.platform, "python": sys.version, "executable": sys.executable,
                  "archive_sha256": EXPECTED_ARCHIVE, "extracted_entries_verified": 117,
                  "native_filesystem_root": str(root), "executions": records, "symlink_checks": checks,
                  "limits": "Native Linux /tmp tests, not Windows junction/OS isolation proof."}
    print(json.dumps(report, sort_keys=True))
    return 0 if all(x["exit_code"] == 0 for x in records) and all(x["passed"] for x in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
