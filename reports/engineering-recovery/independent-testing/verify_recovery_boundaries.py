"""Real bounded process failures plus synthetic contract recovery checks.

The harness's bounded loop is test code. CouncilFlow native-agent retry/crash
accounting remains instruction-only and is not established by these controls.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PYTHON = str(Path(sys.executable).resolve())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    sys.path.insert(0, str(ROOT / "tests"))
    import test_contracts as f
    c = f.c
    contracts = []

    def rejected(name, data):
        try:
            c.validate_sequence(data)
        except c.ContractError as error:
            contracts.append({"name": name, "verdict": "REJECTED", "code": error.code, "field": error.field})
        else:
            raise AssertionError(f"contract recovery attack accepted: {name}")

    failed = f.sequence()[:5]
    failed[-1]["payload"]["status"] = "failed"
    direct = f.assignment("DIRECT", "worker", "M5", f.ref(), instance="worker-1")
    rejected("failed-tester-cannot-direct-dispatch-same-worker", failed + [direct])
    decision = f.message("REWORK", "task.decision", "manager", "planner",
        {"disposition": "rework", "reason": "Retained failing verification; scoped repair.",
         "acceptance_ids": f.AC, "candidate_ref": f.ref(), "report_ids": ["M5"],
         "failed_acceptance_ids": ["AC1", "AC2"]}, "M5")
    fresh = f.assignment("FRESH", "worker", "REWORK", f.ref(), "A2", "independent-fresh-worker")
    c.validate_sequence(failed + [decision, fresh])
    contracts.append({"name": "failed-tester-explicit-rework-fresh-worker-and-attempt", "verdict": "ACCEPTED_UNCHANGED_CRITERIA"})
    reused_worker = copy.deepcopy(fresh)
    reused_worker["recipient"]["instance_id"] = "worker-1"
    rejected("rework-cannot-reuse-worker", failed + [decision, reused_worker])
    reused_attempt = copy.deepcopy(fresh)
    reused_attempt["attempt_id"] = "A1"
    rejected("rework-cannot-reuse-attempt", failed + [decision, reused_attempt])
    mismatch = f.sequence()
    rerun = mismatch[6]["payload"]["comparison"]["independent_rerun"]
    rerun["stdout_sha256"] = "b" * 64
    rerun["status"] = "MISMATCH"
    mismatch[6]["payload"]["status"] = "failed"
    rejected("reviewer-mismatch-cannot-reach-acceptance", mismatch)
    unmet = f.sequence()
    unmet[-1]["payload"]["results"][0]["status"] = "failed"
    rejected("mandatory-final-criterion-cannot-be-unmet-and-passed", unmet)
    # Execute the existing full Planner failure/rework/fresh verification regression
    # separately. Its messages are synthetic; this is not native agent observation.
    arguments = ["-B", "-m", "unittest", "test_contracts.JSONContractTests.test_planner_failure_rework_completes_through_fresh_independent_checks", "-v"]
    full = subprocess.run([PYTHON, *arguments], cwd=ROOT / "tests", capture_output=True, timeout=30)
    (OUT / "planner-full-recovery.stdout.bin").write_bytes(full.stdout)
    (OUT / "planner-full-recovery.stderr.bin").write_bytes(full.stderr)
    assert full.returncode == 0, full.stderr
    contracts.append({"name": "failed-planner-full-rework-retains-all-failed-criteria-and-evidence", "verdict": "PASSED_SYNTHETIC_TRANSITION_REGRESSION",
                      "command": PYTHON, "arguments": arguments, "workdir": str(ROOT / "tests"), "exit_code": full.returncode,
                      "stdout_sha256": sha(full.stdout), "stderr_sha256": sha(full.stderr)})

    process_records = []
    interrupted_args = ["-B", "-c", "import time; print('STARTED', flush=True); time.sleep(5)"]
    try:
        subprocess.run([PYTHON, *interrupted_args], cwd=ROOT, capture_output=True, timeout=0.3)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b"", error.stderr or b""
        (OUT / "infrastructure-timeout.stdout.bin").write_bytes(stdout)
        (OUT / "infrastructure-timeout.stderr.bin").write_bytes(stderr)
        process_records.append({"name": "actual-child-process-timeout", "command": PYTHON, "arguments": interrupted_args,
            "workdir": str(ROOT), "timeout_seconds": 0.3, "exit_code": None, "status": "blocked", "error": "TimeoutExpired",
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr), "success_claimed": False})
    else:
        raise AssertionError("timeout negative control unexpectedly completed")
    failure_args = ["-B", "-c", "import sys; sys.stdout.buffer.write(b'INFRA_FAILURE\\n'); raise SystemExit(73)"]
    bound = 3
    for index in range(bound):
        process = subprocess.run([PYTHON, *failure_args], cwd=ROOT, capture_output=True, timeout=5)
        (OUT / f"unproductive-failure-{index}.stdout.bin").write_bytes(process.stdout)
        (OUT / f"unproductive-failure-{index}.stderr.bin").write_bytes(process.stderr)
        assert process.returncode == 73 and process.stdout == b"INFRA_FAILURE\n"
        process_records.append({"name": "actual-repeated-process-failure", "attempt": index + 1,
            "command": PYTHON, "arguments": failure_args, "workdir": str(ROOT), "exit_code": process.returncode,
            "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr), "status": "failed", "success_claimed": False})
    assert len([record for record in process_records if record["name"] == "actual-repeated-process-failure"]) == bound
    report = {"kind": "Independent maintenance recovery controls; process failures actual, role transitions synthetic",
        "helper_sha256": sha((ROOT / ".agents/skills/council-flow/scripts/contracts.py").read_bytes()),
        "contract_controls": contracts, "process_controls": process_records,
        "repeated_failure_final": {"status": "blocked", "reason": "identical unproductive failure reached declared test bound", "attempts": bound},
        "limitations": ["Bound is enforced by this test harness, not a CouncilFlow supervisor.",
                        "Actual native-agent crash recovery and effective host retry accounting were not exercised."]}
    (OUT / "recovery-boundary-results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"contract_recovery_controls": len(contracts), "actual_process_timeout": 1,
                      "actual_repeated_failures": bound, "final_status": "blocked-as-expected"}))


if __name__ == "__main__":
    main()
