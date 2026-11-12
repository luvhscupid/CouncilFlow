"""Record disposable Windows junction and Ubuntu extraction observations."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def windows_junctions():
    spec = importlib.util.spec_from_file_location("junction_contracts", ROOT / ".agents/skills/council-flow/scripts/contracts.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    records, commands = [], []
    with tempfile.TemporaryDirectory(prefix="cf-junction-independent-") as directory:
        parent = Path(directory).resolve()
        assert parent.is_relative_to(Path(tempfile.gettempdir()).resolve())
        root, outside = parent / "authorized", parent / "outside"
        root.mkdir()
        outside.mkdir()
        (root / "data").mkdir()
        (root / "data/evidence.txt").write_bytes(b"inside")
        (outside / "evidence.txt").write_bytes(b"outside")
        links = []
        try:
            for name, target in [("inside", root / "data"), ("escape", outside)]:
                link = root / name
                args = ["cmd", "/c", "mklink", "/J", str(link), str(target)]
                process = subprocess.run(args, capture_output=True)
                commands.append({"arguments": args, "exit_code": process.returncode,
                                 "stdout_base64": base64.b64encode(process.stdout).decode(),
                                 "stderr_base64": base64.b64encode(process.stderr).decode()})
                if process.returncode:
                    records.append({"case": name + "-junction", "status": "UNVERIFIED", "reason": "mklink failed"})
                    continue
                links.append(link)
                for stale in ([False, True] if name == "inside" else [False]):
                    data = b"stale" if stale else (target / "evidence.txt").read_bytes()
                    ref = {"artifact_id": name, "path": name + "/evidence.txt", "kind": "evidence",
                           "sha256": hashlib.sha256(data).hexdigest()}
                    try:
                        c.artifact(ref, root)
                        allowed, error = True, None
                    except c.ContractError as exc:
                        allowed, error = False, exc.code
                    expected = name == "inside" and not stale
                    records.append({"case": name + ("-stale" if stale else "-matching-hash"),
                                    "status": "PASS" if allowed == expected else "FAIL", "actual_allowed": allowed,
                                    "expected_allowed": expected, "error": error})
        finally:
            for link in links:
                assert link.parent.resolve() == root.resolve()
                os.rmdir(link)
    return {"commands": commands, "checks": records,
            "limit": "Disposable Windows junction behavior only; not race-free or OS-enforced isolation."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    assert args.label in {"sandbox", "approved"}
    junction = windows_junctions()
    command = [r"C:\Windows\System32\wsl.exe", "-d", "Ubuntu", "--", "python3", "-B",
               "/mnt/e/Saint/PROJECTS/CouncilFlow-main/reports/councilflow-final-release-audit/tester/linux_checks.py"]
    process = subprocess.run(command, capture_output=True)
    (OUT / ("wsl-" + args.label + ".stdout.bin")).write_bytes(process.stdout)
    (OUT / ("wsl-" + args.label + ".stderr.bin")).write_bytes(process.stderr)
    record = {"command": command[0], "arguments": command[1:], "workdir": str(ROOT),
              "exit_code": process.returncode, "stdout_sha256": hashlib.sha256(process.stdout.replace(b"\r\n", b"\n")).hexdigest(),
              "junction": junction}
    if process.returncode == 0:
        linux = json.loads(process.stdout)
        for index, item in enumerate(linux["executions"]):
            stdout, stderr = base64.b64decode(item.pop("stdout_base64")), base64.b64decode(item.pop("stderr_base64"))
            (OUT / f"linux-{index}.stdout.bin").write_bytes(stdout)
            (OUT / f"linux-{index}.stderr.bin").write_bytes(stderr)
            text = stderr.decode("utf-8", errors="replace")
            count = re.search(r"Ran (\d+) tests? in", text)
            skip = re.search(r"OK \(skipped=(\d+)\)", text)
            item["run"] = int(count[1]) if count else None
            item["skipped"] = int(skip[1]) if skip else 0
            item["passed"] = item["run"] - item["skipped"] if item["exit_code"] == 0 else None
        record["linux"] = linux
    (OUT / ("platforms-" + args.label + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wsl_exit": process.returncode, "junction_checks": junction["checks"],
                      "linux_counts": [{k:v for k,v in x.items() if k in {"suite", "run", "passed", "skipped", "exit_code"}} for x in record.get("linux", {}).get("executions", [])]}, indent=2))
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
