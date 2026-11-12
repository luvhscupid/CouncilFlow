"""Execute valid production mutants against causally relevant existing regressions."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "reports/councilflow-final-release-audit/worker/final/candidate-manifest.json").read_bytes())
CONTRACT = ".agents/skills/council-flow/scripts/contracts.py"


def one(source, old, new):
    assert source.count(old) == 1, (old[:100], source.count(old))
    return source.replace(old, new, 1)


def main():
    cases = [
        ("CA01", CONTRACT, 'fail("failed_planner_check", "attempt_id", "an unmet original Planner check requires preserved rework and a fresh attempt")', "pass", "test_contracts.PolicyAndDiagnosticTests.test_unmet_planner_check_cannot_be_bypassed_in_same_attempt", "tests"),
        ("CA02", CONTRACT, 'if r["message_type"] == "job.report" and r["sender"]["role"] in {"tester", "reviewer"}', 'if r["message_type"] == "job.report" and r["sender"]["role"] == "tester"', "test_contracts.PolicyAndDiagnosticTests.test_known_failed_reviewer_cannot_be_hidden_from_acceptance", "tests"),
        ("CA03", CONTRACT, 'for role_reports in (testers, reviewers):', 'for role_reports in (testers + reviewers,):', "test_contracts.PolicyAndDiagnosticTests.test_tester_and_reviewer_must_each_cover_all_accepted_criteria", "tests"),
        ("CA04", CONTRACT, 'if p["status"] == "passed" and tc["status"] != "MATCH":', 'if (tc["status"] == "MATCH") != (p["status"] == "passed"):', "test_contracts.PolicyAndDiagnosticTests.test_matching_rerun_can_truthfully_report_substantive_review_failure", "tests"),
        ("CA05", CONTRACT, 'fail("plan_origin", "sender/recipient", "final check requires the original Planner and Manager actors")', "pass", "test_contracts.PolicyAndDiagnosticTests.test_final_check_uses_original_planner_and_manager_actors", "tests"),
        ("CA06", CONTRACT, 'if p != original["payload"] or any(m[actor] != original[actor] for actor in ("sender", "recipient")):', 'if p["plan_ref"] != original["payload"]["plan_ref"] or p["acceptance_ids"] != original["payload"]["acceptance_ids"]:', "test_contracts.PolicyAndDiagnosticTests.test_republication_preserves_full_payload_and_original_actors", "tests"),
        ("CA07", CONTRACT, ' or PureWindowsPath(path).drive', '', "test_contracts.PolicyAndDiagnosticTests.test_windows_drive_paths_are_never_repository_relative", "tests"),
        ("CA08", CONTRACT, 'def artifact(value, root=None, field="evidence_ref"):\n    _tree(value)\n', 'def artifact(value, root=None, field="evidence_ref"):\n', "test_contracts.JSONContractTests.test_authoritative_reference_api_rejects_unencodable_identity", "tests"),
        ("E10", CONTRACT, 'if actual != expected:', 'if False:', "test_contracts.JSONContractTests.test_exact_fidelity_rejects_spacing_newlines_case_and_unicode_changes", "tests"),
        ("DIST02", "demo/structured-flow/sum_values.py", '    try:\n        total = str(sum(args.values))\n    except ValueError:\n        parser.error("sum exceeds supported Python integer output bounds")\n    print(total)', '    print(sum(args.values))', "test_sum_values.SumValuesTests.test_large_valid_operands_handle_output_conversion_bound", "demo/structured-flow"),
        ("DIST03", "demo/receipt/receipt_calculator.py", None, None, "test_receipt_calculator.ArithmeticTests.test_restrictive_ambient_exponent_context_does_not_change_exact_arithmetic", "demo/receipt"),
        ("DIST05", "tools/build_release.py", None, None, "test_release.ReleaseOutputTests.test_existing_output_hardlinks_do_not_modify_outside_inodes", "tests"),
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="cf-independent-mutations-") as directory:
        temporary = Path(directory).resolve()
        assert temporary.is_relative_to(Path(tempfile.gettempdir()).resolve())
        for identity, relative, old, new, test, testdir in cases:
            root = temporary / identity
            root.mkdir()
            for item in MANIFEST["files"]:
                path = root / item["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / item["path"]).read_bytes())
            original = (root / relative).read_text(encoding="utf-8")
            if identity == "DIST03":
                guard = '            context.Emax, context.Emin, context.clamp = MAX_EMAX, MIN_EMIN, 0\n'
                assert original.count(guard) == 1
                mutated = original.replace(guard, "", 1)
                guard2 = '        context.Emax, context.Emin, context.clamp = MAX_EMAX, MIN_EMIN, 0\n'
                assert mutated.count(guard2) == 1
                mutated = mutated.replace(guard2, "", 1)
            elif identity == "DIST05":
                start = original.index("def atomic_write(")
                end = original.index("\n\ndef build(", start)
                mutated = original[:start] + 'def atomic_write(path: Path, data: bytes) -> None:\n    path.write_bytes(data)\n' + original[end:]
            else:
                mutated = one(original, old, new)
            ast.parse(mutated)
            compile(mutated, relative, "exec")
            (root / relative).write_text(mutated, encoding="utf-8", newline="\n")
            env = dict(os.environ, PYTHONPATH=str(root / testdir), PYTHONDONTWRITEBYTECODE="1")
            args = ["-B", "-m", "unittest", test, "-v"]
            process = subprocess.run([sys.executable, *args], cwd=root, env=env, capture_output=True)
            (OUT / ("mutation-" + identity + ".stdout.bin")).write_bytes(process.stdout)
            (OUT / ("mutation-" + identity + ".stderr.bin")).write_bytes(process.stderr)
            text = process.stderr.decode("utf-8", errors="replace")
            invalid = "ImportError" in text or "SyntaxError" in text or "ModuleNotFoundError" in text
            skipped = "OK (skipped=" in text
            result = {"id": identity, "source": relative, "test": test, "command": sys.executable,
                      "arguments": args, "workdir": str(root), "environment": {"PYTHONPATH": str(root / testdir), "PYTHONDONTWRITEBYTECODE": "1"},
                      "original_sha256": hashlib.sha256(original.encode()).hexdigest(), "mutant_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
                      "mutation_old": old, "mutation_new": new,
                      "valid_compiled": True, "exit_code": process.returncode,
                      "stdout_sha256": hashlib.sha256(process.stdout.replace(b"\r\n", b"\n")).hexdigest(),
                      "status": "INVALID" if invalid else "SKIPPED" if skipped else "KILLED" if process.returncode else "SURVIVED",
                      "stdout_path": (OUT / ("mutation-" + identity + ".stdout.bin")).relative_to(ROOT).as_posix(),
                      "stderr_path": (OUT / ("mutation-" + identity + ".stderr.bin")).relative_to(ROOT).as_posix()}
            results.append(result)
            if identity in {"DIST03", "DIST05"}:
                result["mutation_definition"] = "Remove both internal Decimal exponent/clamp assignments" if identity == "DIST03" else "Replace atomic_write body with path.write_bytes(data)"
    report = {"kind": "isolated production mutation checks", "results": results,
              "totals": {s:sum(x["status"] == s for x in results) for s in ["KILLED", "SURVIVED", "INVALID", "SKIPPED"]},
              "limits": "Killed means this designated regression detected this valid mutant, not universal test adequacy."}
    (OUT / "mutation-results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": report["totals"], "cases": [{"id":x["id"], "status":x["status"]} for x in results]}, indent=2))
    return 0 if all(x["status"] == "KILLED" for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
