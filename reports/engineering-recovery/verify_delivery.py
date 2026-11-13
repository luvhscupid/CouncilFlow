"""Windows maintenance verification; never a formal Gate 3 experiment.

Run after committing product and distribution files. All mutations are bounded
to this report directory or tempfile-owned clones/extractions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "delivery-verification"
SUITES = ("tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification")
PROTECTED = ("docs/CouncilFlow-Full-Plan/examples/job.report.json",
             "docs/CouncilFlow-Full-Plan/examples/synthetic-candidate.txt")
GIT = shutil.which("git")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(label, args, cwd, records, timeout=240):
    result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout)
    stdout, stderr = f"{label}.stdout.bin", f"{label}.stderr.bin"
    (OUT / stdout).write_bytes(result.stdout)
    (OUT / stderr).write_bytes(result.stderr)
    record = {"label": label, "command": args[0], "arguments": args[1:],
              "workdir": str(cwd), "exit_code": result.returncode,
              "stdout": stdout, "stderr": stderr,
              "stdout_sha256": digest(result.stdout),
              "stdout_crlf_to_lf_sha256": digest(result.stdout.replace(b"\r\n", b"\n")),
              "stderr_sha256": digest(result.stderr)}
    text = result.stderr.decode("utf-8", "replace")
    count = re.search(r"Ran (\d+) tests?", text)
    if count:
        record["tests_run"] = int(count.group(1))
        skips = re.search(r"skipped=(\d+)", text)
        record["skipped"] = int(skips.group(1)) if skips else 0
        record["result"] = text.splitlines()[-1]
    records.append(record)
    print(json.dumps(record), flush=True)
    if result.returncode:
        raise AssertionError(f"{label}: exit {result.returncode}; inspect {stderr}")
    return result.stdout


def suites(path, prefix, records):
    for index, suite in enumerate(SUITES):
        run(f"{prefix}-suite-{index}",
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", suite, "-v"],
            path, records)


def frozen(path):
    count = 0
    for relative in ("docs/CouncilFlow-Full-Plan", "docs/gate3/CouncilFlow-Gate3-v0.2"):
        folder = path / relative
        for line in (folder / "SHA256SUMS.txt").read_text("utf-8").splitlines():
            if not line.strip():
                continue
            expected, name = line.split(None, 1)
            target = folder / name.lstrip(" *")
            assert digest(target.read_bytes()) == expected, str(target)
            count += 1
    return count


def main():
    OUT.mkdir(exist_ok=True)
    records = []
    head = subprocess.check_output([GIT, "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    report = {"kind": "direct engineering verification, not Gate 3",
              "head": head, "platform": platform.platform(), "python": sys.executable,
              "records": records}
    try:
        original = (ROOT / "dist/council-flow.zip").read_bytes()
        archive_sha = digest(original)
        assert (ROOT / "dist/council-flow.zip.sha256").read_text("ascii").split()[0] == archive_sha
        spec = importlib.util.spec_from_file_location("verified_builder", ROOT / "tools/build_release.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        source = builder.source_bytes(ROOT)
        manifest = json.loads((ROOT / "dist/council-flow.manifest.json").read_bytes())
        assert manifest["sha256"] == archive_sha
        assert manifest["files"] == [{"path": name, "size": len(data), "sha256": digest(data)}
                                     for name, data in source.items()]
        with zipfile.ZipFile(ROOT / "dist/council-flow.zip") as archive:
            assert archive.testzip() is None
            assert archive.namelist() == list(source)
            for name, data in source.items():
                assert archive.read(name) == data, name
        report.update(archive_sha256=archive_sha, entries=len(source),
                      frozen_checksum_entries=frozen(ROOT), source_byte_parity="PASS")
        with tempfile.TemporaryDirectory(prefix="councilflow-delivery-") as temporary:
            parent = Path(temporary)
            checkout = parent / "checkout"
            run("fresh-clone", [GIT, "-c", "core.autocrlf=true", "clone", "--no-hardlinks",
                                "--branch", "codex/councilflow-e10-recovery", str(ROOT), str(checkout)],
                parent, records)
            assert subprocess.check_output([GIT, "rev-parse", "HEAD"], cwd=checkout).decode().strip() == head
            for name in PROTECTED:
                blob = subprocess.check_output([GIT, "show", f"HEAD:{name}"], cwd=checkout)
                assert blob == (checkout / name).read_bytes()
                assert b"\r\n" in blob
            assert frozen(checkout) == report["frozen_checksum_entries"]
            suites(checkout, "checkout", records)
            for iteration in range(2):
                run(f"checkout-build-{iteration}", [sys.executable, "-B", "tools/build_release.py"],
                    checkout, records)
                assert (checkout / "dist/council-flow.zip").read_bytes() == original
                assert (checkout / "dist/council-flow.manifest.json").read_bytes() == (ROOT / "dist/council-flow.manifest.json").read_bytes()
                assert (checkout / "dist/council-flow.zip.sha256").read_bytes() == (ROOT / "dist/council-flow.zip.sha256").read_bytes()
            status = subprocess.check_output([GIT, "status", "--porcelain"], cwd=checkout)
            assert not status, status
            extraction = parent / "extracted"
            with zipfile.ZipFile(ROOT / "dist/council-flow.zip") as archive:
                archive.extractall(extraction)
            suites(extraction, "extracted", records)
            assert frozen(extraction) == report["frozen_checksum_entries"]
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="FAIL", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (OUT / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
