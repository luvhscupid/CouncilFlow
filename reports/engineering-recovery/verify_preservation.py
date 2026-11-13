"""Compare protected and original bytes to the pre-edit maintenance capture."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).resolve().parent


def main():
    baseline = json.loads((EVIDENCE / "baseline.json").read_bytes())
    failures, checked = [], {}
    for key in ("owner_checkout", "gate3_checkout"):
        source = baseline[key]
        root = Path(source["root"])
        for relative, expected in source["files"].items():
            path = root / relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
                failures.append(f"{key}: bytes changed or missing: {relative}")
        status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z"], cwd=root).decode()
        if status != source["status"]:
            failures.append(f"{key}: original Git status changed")
        checked[key] = len(source["files"])
    protected = 0
    for relative, expected in baseline["baseline"]["files"].items():
        if relative.startswith(("docs/", "reports/")) or relative == ".gitattributes":
            path = ROOT / relative
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
                failures.append(f"maintenance checkout protected bytes changed: {relative}")
            protected += 1
    fixture = baseline["external_owner_fixture"]
    if hashlib.sha256(Path(fixture["path"]).read_bytes()).hexdigest() != fixture["sha256"]:
        failures.append("external original Owner fixture changed")
    if subprocess.check_output(["git", "rev-parse", "refs/heads/main"], cwd=ROOT).decode().strip() != baseline["baseline"]["head"]:
        failures.append("local main changed")
    plan = json.loads((EVIDENCE / "engineering-plan.json").read_bytes())
    tags = subprocess.check_output(["git", "show-ref", "--tags"], cwd=ROOT).decode().splitlines()
    if tags != plan["initial_tags"]:
        failures.append("release tags changed")
    result = {"status": "FAIL" if failures else "PASS", "checked_original_files": checked,
              "protected_baseline_files": protected, "external_fixture_sha256": fixture["sha256"],
              "main_unchanged": "local main changed" not in failures, "tags_unchanged": tags == plan["initial_tags"],
              "failures": failures}
    (EVIDENCE / "preservation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
