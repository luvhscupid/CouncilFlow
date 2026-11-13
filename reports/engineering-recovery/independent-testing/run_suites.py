"""Execute six suites on a digest-bound candidate and retain raw evidence."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PYTHON = str(Path(sys.executable).resolve())
SUITES = ("tests", "demo/receipt", "demo/csv-summary", "demo/structured-flow",
          "reports/demo/verification", "reports/csv-summary/verification")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def as_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def snapshot():
    spec = importlib.util.spec_from_file_location("independent_release_inventory", ROOT / "tools/build_release.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    files = builder.source_bytes(ROOT)
    for path in (ROOT / ".github").rglob("*"):
        if path.is_file():
            files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in (".gitattributes", ".gitignore"):
        files[name] = (ROOT / name).read_bytes()
    inventory = {name: {"sha256": sha(raw), "size": len(raw)} for name, raw in sorted(files.items())}
    return {"files": inventory, "candidate_sha256": sha(as_bytes(inventory))}


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    initial = snapshot()
    (OUT / "candidate-before.json").write_bytes(as_bytes(initial))
    records = []
    for index, suite in enumerate(SUITES):
        arguments = ["-B", "-m", "unittest", "discover", "-s", suite, "-v"]
        try:
            process = subprocess.run([PYTHON, *arguments], cwd=ROOT, capture_output=True, timeout=240)
            exit_code, stdout, stderr = process.returncode, process.stdout, process.stderr
            timed_out = False
        except subprocess.TimeoutExpired as error:
            exit_code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
            timed_out = True
        (OUT / f"suite-{index}.stdout.bin").write_bytes(stdout)
        (OUT / f"suite-{index}.stderr.bin").write_bytes(stderr)
        text = stderr.decode("utf-8", "replace")
        ran_match = re.search(r"Ran (\d+) tests?", text)
        summary = text.splitlines()[-1] if text.splitlines() else "NO_OUTPUT"
        details = {key: int(value) for key, value in re.findall(r"(failures|errors|skipped)=(\d+)", summary)}
        ran = int(ran_match.group(1)) if ran_match else None
        counts = {"ran": ran, "failures": details.get("failures", 0),
                  "errors": details.get("errors", 0), "skipped": details.get("skipped", 0)}
        counts["passed"] = None if ran is None else ran - sum(counts[key] for key in ("failures", "errors", "skipped"))
        record = {"suite": suite, "command": PYTHON, "arguments": arguments,
                  "workdir": str(ROOT), "candidate_sha256": initial["candidate_sha256"],
                  "exit_code": exit_code, "timed_out": timed_out, "counts": counts,
                  "stdout_sha256": sha(stdout),
                  "normalized_stdout_sha256": sha(stdout.replace(b"\r\n", b"\n")),
                  "stderr_sha256": sha(stderr), "summary": summary,
                  "stdout_artifact": f"suite-{index}.stdout.bin", "stderr_artifact": f"suite-{index}.stderr.bin"}
        records.append(record)
        print(json.dumps({"suite": suite, "exit_code": exit_code, **counts}), flush=True)
    final = snapshot()
    (OUT / "candidate-after.json").write_bytes(as_bytes(final))
    result = {"kind": "Independent Windows engineering execution, not formal Gate 3",
              "python": PYTHON, "python_version": sys.version, "platform": platform.platform(),
              "candidate_sha256": initial["candidate_sha256"], "candidate_unchanged": final == initial,
              "records": records}
    (OUT / "suite-results.json").write_bytes(as_bytes(result))
    if final != initial:
        raise AssertionError("source candidate changed during independent verification")
    raise SystemExit(any(record["exit_code"] != 0 for record in records))


if __name__ == "__main__":
    main()
