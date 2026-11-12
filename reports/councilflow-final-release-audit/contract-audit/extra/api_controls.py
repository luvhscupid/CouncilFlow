"""Additional bounded synthetic API controls, using pinned baseline by default."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "3879c3d97efb6dfb5256445bf21748a95d0d2eab"
PRODUCTION = ".agents/skills/council-flow/scripts/contracts.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    source = ((ROOT / PRODUCTION).read_bytes() if args.current else
              subprocess.check_output(["git", "show", BASELINE + ":" + PRODUCTION], cwd=ROOT))
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        module = root / "contracts.py"
        module.write_bytes(source)
        spec = importlib.util.spec_from_file_location("challenged_contracts", module)
        c = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(c)

        def run(name, expected, operation):
            try:
                operation()
                actual, error = True, None
            except c.ContractError as exc:
                actual, error = False, exc.code
            except Exception as exc:
                actual, error = "UNEXPECTED_EXCEPTION", type(exc).__name__
            results.append({"case": name, "expected_valid": expected, "actual_valid": actual,
                            "satisfied": actual == expected, "error": error})

        content = b'{"criteria":[{"id":"AC1","criterion":"Preserve exact text."}]}'
        (root / "criteria.json").write_bytes(content)
        trusted = {"artifact_id": "\ud800", "path": "criteria.json",
                   "sha256": hashlib.sha256(content).hexdigest(), "kind": "owner-approved-criteria"}
        run("authoritative_reference_surrogate_identity", False,
            lambda: c.validate_sequence([], root=root, authoritative_criteria_ref=trusted,
                                        require_criteria_fidelity=True))
        trusted["artifact_id"] = "criteria"
        run("valid_authoritative_reference_prefix", True,
            lambda: c.validate_sequence([], root=root, authoritative_criteria_ref=trusted,
                                        require_criteria_fidelity=True))
        candidate = {"artifact_id": "candidate", "path": "candidate.json", "sha256": "0" * 64, "kind": "synthetic"}
        execution = dict(candidate, artifact_id="execution", path="execution.txt")
        command = {"command_id": "C1", "command": "C:/synthetic/python.exe", "arguments": ["--version"],
                   "workdir": "C:/synthetic", "candidate_ref": candidate, "input_refs": [], "exit_code": 0,
                   "stdout_sha256": "a" * 64, "acceptance_id": "AC1", "evidence_ref": execution}
        tester = {"protocol": "council-flow", "version": "1.0", "message_id": "T1", "message_type": "job.report",
                  "plan_id": "P1", "plan_revision": 1, "task_id": "task", "attempt_id": "A1",
                  "sender": {"role": "tester", "instance_id": "tester"},
                  "recipient": {"role": "manager", "instance_id": "manager"}, "in_reply_to": "ASSIGN",
                  "payload": {"status": "passed", "summary": "Synthetic only", "acceptance_ids": ["AC1"],
                              "candidate_ref": candidate, "findings": [], "errors": [],
                              "oracle_ref": dict(candidate, artifact_id="oracle", path="oracle.json"),
                              "checks": [{"name": "synthetic", "status": "passed", "evidence_ref": execution}],
                              "deterministic_commands": [command]}, "evidence_refs": [execution]}
        run("valid_closed_tester_message", True, lambda: c.validate_message(tester))
        changed = copy.deepcopy(tester)
        changed["payload"]["deterministic_commands"][0]["exit_code"] = True
        run("boolean_exit_code_rejected", False, lambda: c.validate_message(changed))
        changed_payload = copy.deepcopy(tester)
        changed_payload["payload"]["unknown"] = "x"
        run("unknown_payload_field_rejected", False, lambda: c.validate_message(changed_payload))
        changed_command = copy.deepcopy(tester)
        changed_command["payload"]["deterministic_commands"][0]["unknown"] = "x"
        run("unknown_nested_command_field_rejected", False, lambda: c.validate_message(changed_command))
    summary = {"source": "current" if args.current else BASELINE, "source_sha256": hashlib.sha256(source).hexdigest(),
               "kind": "synthetic-API-controls", "cases": len(results),
               "passed": sum(x["satisfied"] for x in results), "failed": sum(not x["satisfied"] for x in results),
               "skipped": 0, "results": results,
               "limits": "Prefix validation is not completion evidence. No authentic Owner fixture or host provenance established."}
    print(json.dumps(summary, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
