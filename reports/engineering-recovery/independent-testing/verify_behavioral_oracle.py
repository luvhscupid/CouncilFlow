"""Independent maintenance negative controls; never native-role/Gate 3 proof."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = "ba1aee06ce0c97add1029b7c3ef323b6de1cb9ce"
PYTHON = str(Path(sys.executable).resolve())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run(name, arguments, workdir, timeout=30):
    command = [PYTHON, *arguments]
    process = subprocess.run(command, cwd=workdir, capture_output=True, timeout=timeout)
    (OUT / (name + ".stdout.bin")).write_bytes(process.stdout)
    (OUT / (name + ".stderr.bin")).write_bytes(process.stderr)
    return {"name": name, "command": PYTHON, "arguments": arguments,
            "workdir": str(workdir), "exit_code": process.returncode,
            "stdout_sha256": digest(process.stdout),
            "normalized_stdout_sha256": digest(process.stdout.replace(b"\r\n", b"\n")),
            "stderr_sha256": digest(process.stderr)}, process


def original(name):
    return subprocess.run(["git", "show", BASELINE + ":" + name], cwd=ROOT,
                          capture_output=True, check=True).stdout


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    source = original("demo/receipt/receipt_calculator.py")
    oracle = original("demo/receipt/test_receipt_calculator.py")
    weakened = b"import unittest\nclass WeakTests(unittest.TestCase):\n def test_success(self): self.assertTrue(True)\n"
    mutations = [
        ("wrong-version", b'sys.stdout.buffer.write(b"1.0.0\\n")',
         b'sys.stdout.buffer.write(b"9.9.9\\n")', b"FAIL: test_version"),
        ("wrong-arithmetic", b"return self.quantity * self.unit_price",
         b"return self.quantity + self.unit_price", b"FAIL: test_owner_sample"),
    ]
    result = {"kind": "Independent maintenance behavioral mutation controls, not Gate 3 or host-role proof",
              "baseline": BASELINE, "source_sha256": digest(source),
              "preserved_oracle_sha256": digest(oracle), "controls": []}
    with tempfile.TemporaryDirectory(prefix="cf-independent-oracle-") as temporary:
        parent = Path(temporary)
        for name, before, after, assertion in mutations:
            candidate = parent / name
            candidate.mkdir()
            assert source.count(before) == 1, "mutation target must match exactly once"
            mutated = source.replace(before, after, 1)
            (candidate / "receipt_calculator.py").write_bytes(mutated)
            (candidate / "test_candidate.py").write_bytes(weakened)
            (candidate / "test_preserved.py").write_bytes(oracle)
            own_record, own = run(name + "-weak-tests",
                                  ["-B", "-m", "unittest", "discover", "-s", ".", "-p", "test_candidate.py", "-v"], candidate)
            independent_record, independent = run(name + "-preserved-oracle",
                                  ["-B", "-m", "unittest", "discover", "-s", ".", "-p", "test_preserved.py", "-v"], candidate)
            assert own.returncode == 0, own.stderr
            assert independent.returncode != 0, "preserved oracle failed to catch behavioral defect"
            assert assertion in independent.stderr, independent.stderr
            assert b"ImportError" not in independent.stderr and b"ModuleNotFoundError" not in independent.stderr
            assert (candidate / "test_preserved.py").read_bytes() == oracle
            assert (candidate / "receipt_calculator.py").read_bytes() == mutated
            result["controls"].append({"name": name, "mutation_before": before.decode(), "mutation_after": after.decode(),
                "candidate_source_sha256": digest(mutated), "preserved_oracle_sha256": digest(oracle),
                "weakened_tests": own_record, "independent_tests": independent_record,
                "assertion_signature": assertion.decode(), "verdict": "BEHAVIORAL_DEFECT_CAUGHT"})
        # Rerun an exact executable/arguments/workdir against one unchanged good app.
        stable = parent / "rerun"
        stable.mkdir()
        (stable / "receipt_calculator.py").write_bytes(source)
        tester_record, tester = run("deterministic-tester", ["-B", "receipt_calculator.py", "--version"], stable)
        reviewer_record, reviewer = run("deterministic-reviewer", ["-B", "receipt_calculator.py", "--version"], stable)
        assert tester.stdout == reviewer.stdout == b"1.0.0\n"
        assert tester.returncode == reviewer.returncode == 0
        assert tester_record["normalized_stdout_sha256"] == reviewer_record["normalized_stdout_sha256"]
        # A known corrupted prior hash is retained as test input, never authentic Tester evidence.
        tampered = dict(tester_record, normalized_stdout_sha256="0" * 64)
        assert tampered["normalized_stdout_sha256"] != reviewer_record["normalized_stdout_sha256"]
        result["deterministic_rerun"] = {"candidate_source_sha256": digest(source),
            "tester": tester_record, "reviewer": reviewer_record, "unchanged_candidate_match": True,
            "synthetic_tampered_record": tampered, "tampered_record_detected": True,
            "normalization": "raw_stdout.replace(b'\\r\\n', b'\\n') only; no trimming"}
    (OUT / "behavioral-oracle-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"controls": len(result["controls"]), "behavioral_defects_caught": len(result["controls"]),
                      "exact_rerun_match": True, "tampered_record_detected": True}))


if __name__ == "__main__":
    main()
