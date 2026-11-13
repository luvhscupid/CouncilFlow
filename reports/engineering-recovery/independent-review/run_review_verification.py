"""Independent direct engineering review executions; no formal native-role claim."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TESTER = ROOT / "reports/engineering-recovery/independent-testing"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def serial(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

def snapshot():
    spec = importlib.util.spec_from_file_location("review_release_inventory", ROOT / "tools/build_release.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    files = builder.source_bytes(ROOT)
    for path in (ROOT / ".github").rglob("*"):
        if path.is_file():
            files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in (".gitattributes", ".gitignore"):
        files[name] = (ROOT / name).read_bytes()
    inventory = {name: {"sha256": digest(raw), "size": len(raw)} for name, raw in sorted(files.items())}
    return {"files": inventory, "candidate_sha256": digest(serial(inventory))}

def execute(command, arguments, workdir, name):
    process = subprocess.run([command, *arguments], cwd=workdir, capture_output=True, timeout=60)
    (OUT / (name + ".stdout.bin")).write_bytes(process.stdout)
    (OUT / (name + ".stderr.bin")).write_bytes(process.stderr)
    return {"command": command, "arguments": arguments, "workdir": workdir,
            "exit_code": process.returncode, "stdout_sha256": digest(process.stdout),
            "normalized_stdout_sha256": digest(process.stdout.replace(b"\r\n", b"\n")),
            "stderr_sha256": digest(process.stderr),
            "stdout_artifact": (OUT / (name + ".stdout.bin")).relative_to(ROOT).as_posix(),
            "stderr_artifact": (OUT / (name + ".stderr.bin")).relative_to(ROOT).as_posix()}

def main():
    declaration_path = TESTER / "readonly-command-declaration.json"
    declaration_raw = declaration_path.read_bytes()
    declaration = json.loads(declaration_raw)
    before = snapshot()
    assert before == json.loads((TESTER / "candidate-after.json").read_bytes()), "review candidate differs from tested source"
    assert before["candidate_sha256"] == declaration["candidate_sha256"]
    (OUT / "candidate-before.json").write_bytes(serial(before))
    assert Path(declaration["command"]).is_absolute()
    assert digest(Path(declaration["command"]).read_bytes()) == declaration["executable_sha256"]
    for item in declaration["input_refs"]:
        assert digest((ROOT / item["path"]).read_bytes()) == item["sha256"], item
    tester_stdout = (ROOT / declaration["stdout_artifact"]).read_bytes()
    assert digest(tester_stdout.replace(b"\r\n", b"\n")) == declaration["stdout_sha256"]
    rerun = execute(declaration["command"], declaration["arguments"], declaration["workdir"], "readonly-rerun")
    match = (rerun["exit_code"] == declaration["exit_code"] and
             rerun["normalized_stdout_sha256"] == declaration["stdout_sha256"])
    assert match, "independent rerun differs from actual Tester record"
    controls = execute(declaration["command"], ["-B", "reports/engineering-recovery/independent-review/review_source_controls.py"], str(ROOT), "source-controls")
    assert controls["exit_code"] == 0, controls
    source_results = json.loads((ROOT / controls["stdout_artifact"]).read_bytes())
    assert source_results["passed"] == source_results["controls"] == 8
    after = snapshot()
    (OUT / "candidate-after.json").write_bytes(serial(after))
    assert before == after, "review execution changed product inputs"
    record = {"kind": "Independent direct engineering review; not formal Gate 3/E8 certification",
              "status": "passed", "candidate_sha256": before["candidate_sha256"], "candidate_unchanged": before == after,
              "tester_declaration_path": declaration_path.relative_to(ROOT).as_posix(),
              "tester_declaration_sha256": digest(declaration_raw),
              "tester_input_refs": declaration["input_refs"], "executable_sha256": declaration["executable_sha256"],
              "tester_exit_code": declaration["exit_code"], "tester_stdout_sha256": declaration["stdout_sha256"],
              "normalization": "raw_stdout.replace(b'\\r\\n', b'\\n') only",
              "independent_rerun": rerun, "comparison": "MATCH" if match else "MISMATCH",
              "source_controls_execution": controls, "source_controls": source_results,
              "open_findings": [],
              "limitations": ["Caller supplies observed original-input provenance; hashes do not authenticate the Owner or seal storage.",
                              "Source parsing deliberately supports unambiguous ACn text only; unsupported inputs fail closed.",
                              "Oracle preservation, handoff completeness and retry accounting remain instruction policies rather than an OS-enforced runtime.",
                              "Distinct maintenance sessions do not establish formal Gate 3 E1/E2/E4, effective custom-agent TOML loading, model diversity or independent model weights."]}
    (OUT / "review-result.json").write_bytes(serial(record))
    print(json.dumps({"status": record["status"], "candidate_sha256": record["candidate_sha256"],
                      "comparison": record["comparison"], "source_controls": source_results["passed"],
                      "exit_code": rerun["exit_code"], "normalized_stdout_sha256": rerun["normalized_stdout_sha256"],
                      "candidate_unchanged": record["candidate_unchanged"]}, sort_keys=True))

if __name__ == "__main__":
    main()
