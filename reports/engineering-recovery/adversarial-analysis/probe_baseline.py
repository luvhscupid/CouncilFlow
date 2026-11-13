"""Maintenance probes, not native CouncilFlow or Gate 3 execution evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def execute(label, arguments, workdir):
    command = [sys.executable, *arguments]
    result = subprocess.run(command, cwd=workdir, capture_output=True, timeout=30)
    for stream in ("stdout", "stderr"):
        (OUTPUT / (label + "." + stream + ".bin")).write_bytes(getattr(result, stream))
    return {"command": sys.executable, "arguments": arguments,
            "workdir": str(workdir), "exit_code": result.returncode,
            "stdout_sha256": digest(result.stdout.replace(b"\r\n", b"\n")),
            "stderr_sha256": digest(result.stderr),
            "stdout_file": label + ".stdout.bin", "stderr_file": label + ".stderr.bin"}


def main():
    sys.path.insert(0, str(ROOT / "tests"))
    import test_contracts as t
    data = t.sequence()[:5]
    data[-1]["payload"]["status"] = "failed"
    repair = t.assignment("REPAIR", "worker", "M5", t.ref(), instance="worker-1")
    try:
        t.c.validate_sequence(data + [repair])
        recovery = {"result": "ACCEPTED", "defect": "Failed Tester can route repair directly to same Worker/same attempt without rework decision"}
    except t.c.ContractError as exc:
        recovery = {"result": "REJECTED", "error": str(exc)}
    result = {"kind": "direct-maintenance-baseline-probes", "not_gate3": True,
              "contracts_sha256": digest((ROOT / ".agents/skills/council-flow/scripts/contracts.py").read_bytes()),
              "recovery_bypass": recovery}
    with tempfile.TemporaryDirectory(prefix="councilflow-oracle-probe-") as temp:
        candidate = Path(temp)
        app = (ROOT / "demo/receipt/receipt_calculator.py").read_bytes()
        mutated = app.replace(b"return self.quantity * self.unit_price", b"return self.quantity + self.unit_price")
        assert mutated != app, "behavioral mutation must land"
        (candidate / "receipt_calculator.py").write_bytes(mutated)
        weakened = b"import unittest\nclass Weakened(unittest.TestCase):\n def test_false_confidence(self): self.assertTrue(True)\n"
        (candidate / "test_receipt_calculator.py").write_bytes(weakened)
        result["oracle_inputs"] = {"original_app_sha256": digest(app), "mutated_app_sha256": digest(mutated),
                                    "weakened_test_sha256": digest(weakened)}
        result["worker_weakened_suite"] = execute("worker-weakened-suite", ["-B", "-m", "unittest", "discover", "-s", "."], candidate)
        original_tests = (ROOT / "demo/receipt/test_receipt_calculator.py").read_bytes()
        (candidate / "test_receipt_calculator.py").write_bytes(original_tests)
        result["oracle_inputs"]["original_tests_sha256"] = digest(original_tests)
        result["independent_pristine_suite"] = execute("independent-pristine-suite", ["-B", "-m", "unittest", "discover", "-s", "."], candidate)
        assert result["worker_weakened_suite"]["exit_code"] == 0
        assert result["independent_pristine_suite"]["exit_code"] != 0
        stderr = (OUTPUT / "independent-pristine-suite.stderr.bin").read_bytes()
        assert b"FAIL:" in stderr and b"AssertionError" in stderr
        assert b"ImportError" not in stderr and b"SyntaxError" not in stderr
    names = [
        "test_rework_requires_failure_and_fresh_worker_attempt",
        "test_planner_failure_rework_completes_through_fresh_independent_checks",
        "test_passed_tester_cannot_hide_failed_or_unverified_checks",
        "test_tester_strategy_is_assigned_not_self_approved",
        "test_acceptance_cannot_hide_known_failed_candidate_report",
        "test_passing_final_check_requires_manager_evidence_acceptance",
        "test_unmet_planner_check_cannot_be_bypassed_in_same_attempt",
        "test_known_failed_reviewer_cannot_be_hidden_from_acceptance",
        "test_stdout_hash_mismatch_fails_reviewer_acceptance",
        "test_exit_code_mismatch_fails_reviewer_acceptance",
    ]
    result["existing_controls"] = execute("existing-controls", ["-B", "-m", "unittest", *["test_contracts.JSONContractTests." + name for name in names]], ROOT / "tests")
    (OUTPUT / "baseline-probe.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"recovery_bypass": recovery, "weakened_oracle_exit": result["worker_weakened_suite"]["exit_code"], "pristine_oracle_exit": result["independent_pristine_suite"]["exit_code"], "existing_controls_exit": result["existing_controls"]["exit_code"]}))


if __name__ == "__main__":
    main()
