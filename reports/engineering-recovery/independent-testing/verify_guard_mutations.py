"""Mutate helper protections in temporary copies; prove new regressions catch them."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HELPER_NAME = ".agents/skills/council-flow/scripts/contracts.py"
PYTHON = str(Path(sys.executable).resolve())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    source = (ROOT / HELPER_NAME).read_bytes()
    required = (HELPER_NAME, "tests/test_contracts.py", "tests/test_original_source.py",
                "tests/fixtures/owner-version-original.txt")
    variants = [
        ("source-comparison-removed", b"                    _compare_authoritative_criteria(plan, expected_criteria)",
         b"                    pass  # isolated independent mutation", b"FAIL: test_actual_fixture_plan_mutations_rejected_despite_rehashed_plan"),
        ("rework-guard-disabled", b"            if earlier_workers and (not predecessor",
         b"            if False and earlier_workers and (not predecessor", b"FAIL: test_direct_failure_repair_requires_rework"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="cf-independent-guard-mutations-") as temporary:
        parent = Path(temporary)
        for name, before, after, assertion in variants:
            assert source.count(before) == 1, f"mutation target mismatch: {name}"
            candidate = parent / name
            candidate.mkdir()
            for relative in required:
                destination = candidate / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
            mutated = source.replace(before, after, 1)
            (candidate / HELPER_NAME).write_bytes(mutated)
            arguments = ["-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_original_source.py", "-v"]
            process = subprocess.run([PYTHON, *arguments], cwd=candidate, capture_output=True, timeout=90)
            (OUT / (name + ".stdout.bin")).write_bytes(process.stdout)
            (OUT / (name + ".stderr.bin")).write_bytes(process.stderr)
            assert process.returncode != 0, f"new regression suite did not catch {name}"
            assert assertion in process.stderr, process.stderr
            assert b"ContractError not raised" in process.stderr, "failure must be the missing protection, not setup"
            assert b"ImportError" not in process.stderr and b"ModuleNotFoundError" not in process.stderr
            assert (ROOT / HELPER_NAME).read_bytes() == source, "live helper mutated"
            results.append({"name": name, "command": PYTHON, "arguments": arguments,
                            "workdir": str(candidate), "base_helper_sha256": sha(source),
                            "mutated_helper_sha256": sha(mutated), "mutation_before": before.decode(),
                            "mutation_after": after.decode(), "exit_code": process.returncode,
                            "stdout_sha256": sha(process.stdout), "stderr_sha256": sha(process.stderr),
                            "assertion_signature": assertion.decode(), "verdict": "REGRESSION_CAUGHT_REMOVED_GUARD"})
    report = {"kind": "Independent maintenance protection mutations; no live source edits or formal Gate 3",
              "input_refs": {name: sha((ROOT / name).read_bytes()) for name in required}, "results": results}
    (OUT / "guard-mutation-results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"guard_mutations": len(results), "regressions_caught": len(results)}))


if __name__ == "__main__":
    main()
