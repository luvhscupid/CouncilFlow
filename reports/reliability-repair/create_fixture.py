"""Create honest local execution evidence for the bounded sequence regression.

The role identities in this fixture are synthetic contract data. Subprocess
outputs and hashes are real local observations; this is not native agent proof.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "reliability-repair" / "fresh-verification-final"
ACCEPTANCE = ["AC1"]
PLAN_ID = "RELIABILITY-PLAN-1"
TASK_ID = "RELIABILITY-TASK-1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_bytes(relative: str, content: bytes) -> dict:
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"artifact_id": relative.replace("/", "-"),
            "path": path.relative_to(ROOT).as_posix(), "sha256": sha(content), "kind": "evidence"}


def write_json(relative: str, value: object, *, identity: str | None = None, kind="evidence") -> dict:
    content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"artifact_id": identity or relative.replace("/", "-"),
            "path": path.relative_to(ROOT).as_posix(), "sha256": sha(content), "kind": kind}


def envelope(mid, message_type, sender, recipient, attempt, reply, payload, evidence_refs):
    return {"protocol": "council-flow", "version": "1.0", "message_id": mid,
            "message_type": message_type, "plan_id": PLAN_ID, "plan_revision": 1,
            "task_id": TASK_ID, "attempt_id": attempt,
            "sender": {"role": sender[0], "instance_id": sender[1]},
            "recipient": {"role": recipient[0], "instance_id": recipient[1]},
            "in_reply_to": reply, "payload": payload, "evidence_refs": evidence_refs}


def save_message(message):
    return write_json(f"messages/{message['message_id']}.json", message,
                      identity=message["message_id"], kind="message")


def run_command(candidate_path: str, label: str):
    argv = ["-B", candidate_path, "--version"]
    result = subprocess.run([sys.executable, *argv], cwd=ROOT, capture_output=True, check=False)
    raw_out, raw_err = result.stdout, result.stderr
    stdout_ref = write_bytes(f"execution/{label}.stdout.bin", raw_out)
    stderr_ref = write_bytes(f"execution/{label}.stderr.bin", raw_err)
    exit_ref = write_bytes(f"execution/{label}.exit.txt", f"{result.returncode}\n".encode("ascii"))
    normalized_hash = sha(raw_out.replace(b"\r\n", b"\n"))
    execution_ref = write_json(f"execution/{label}.json", {
        "executable": sys.executable, "arguments": argv, "working_directory": str(ROOT),
        "stdout_ref": stdout_ref, "stderr_ref": stderr_ref, "exit_ref": exit_ref,
        "exit_code": result.returncode, "normalized_stdout_sha256": normalized_hash,
    }, identity=f"{label}-execution", kind="execution-evidence")
    return {"stdout": raw_out, "stderr": raw_err, "exit_code": result.returncode,
            "stdout_ref": stdout_ref, "stderr_ref": stderr_ref, "exit_ref": exit_ref,
            "execution_ref": execution_ref, "stdout_sha256": normalized_hash,
            "command": sys.executable, "arguments": argv,
            "workdir": str(ROOT)}


def run():
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing evidence: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    messages = []
    plan = {"plan_id": PLAN_ID, "plan_revision": 1,
            "acceptance": [{"id": "AC1", "criterion":
                "--version stdout bytes are exactly b'1.0.0\\n' and exit is 0."}]}
    plan_ref = write_json("plan.json", plan, identity="plan-original", kind="plan")
    oracle_ref = write_json("verification-strategy.json", {
        "strategy_id": "exact-version-bytes", "command": "run --version and preserve raw stdout/exit"},
        identity="manager-oracle", kind="verification-strategy")
    plan_publish = envelope("M01", "plan.publish", ("planner", "planner-1"),
        ("manager", "manager-1"), "A1", None,
        {"objective": "Check exact version output and preserve original acceptance.",
         "scope": ["reports/reliability-repair/fresh-verification/**"],
         "acceptance_ids": ACCEPTANCE, "plan_ref": plan_ref}, [plan_ref])
    messages.append(plan_publish); save_message(plan_publish)

    candidate_paths = [
        "reports/reliability-repair/fresh-verification/candidates/candidate-attempt1.py",
        "reports/reliability-repair/fresh-verification/candidates/candidate-attempt2.py",
    ]
    source_variants = [b"import sys\nsys.stdout.buffer.write(b'1.0.0\\r\\n')\n",
                       b"import sys\nsys.stdout.buffer.write(b'1.0.0\\n')\n"]
    candidate_refs = []
    for path, content in zip(candidate_paths, source_variants):
        artifact = write_bytes(path.removeprefix("reports/reliability-repair/fresh-verification/"), content)
        candidate_refs.append({**artifact, "artifact_id": Path(path).stem, "kind": "candidate"})

    def dispatch_and_check(index, attempt, worker_id, tester_id, reviewer_id, candidate_ref,
                           input_ref=None, dispatch_reply=None):
        suffix = f"A{index}"
        worker_payload = {"objective": "Implement the exact AC1 command behavior.",
            "scope": [candidate_paths[index - 1]], "acceptance_ids": ACCEPTANCE,
            "instructions": ["Preserve the frozen plan and candidate snapshots."]}
        if input_ref is not None:
            worker_payload["candidate_ref"] = input_ref
        assignment = envelope(f"M{suffix}-WORK-ASSIGN", "job.assign",
            ("manager", "manager-1"), ("worker", worker_id), attempt,
            "M01" if index == 1 else dispatch_reply, worker_payload,
            [plan_ref] + ([input_ref] if input_ref else []))
        messages.append(assignment); assignment_ref = save_message(assignment)
        worker_evidence = write_json(f"evidence/{suffix}-worker.json", {
            "candidate_ref": candidate_ref, "input_candidate_ref": input_ref,
            "snapshot_sha256": candidate_ref["sha256"]}, identity=f"{suffix}-worker-evidence", kind="worker-evidence")
        worker_payload_report = {"status": "passed", "summary": "Candidate snapshot recorded.",
            "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_ref,
            "findings": [], "errors": [],
            "changed_files": [candidate_paths[index - 1].removeprefix("reports/reliability-repair/fresh-verification/")]}
        if input_ref is not None:
            worker_payload_report["input_candidate_ref"] = input_ref
        worker_report = envelope(f"M{suffix}-WORK-REPORT", "job.report",
            ("worker", worker_id), ("manager", "manager-1"), attempt,
            assignment["message_id"], worker_payload_report,
            [candidate_ref, worker_evidence, assignment_ref, plan_ref])
        messages.append(worker_report); worker_report_ref = save_message(worker_report)

        tester_assignment = envelope(f"M{suffix}-TEST-ASSIGN", "job.assign",
            ("manager", "manager-1"), ("tester", tester_id), attempt,
            worker_report["message_id"], {"objective": "Independently execute the approved exact-output check.",
            "scope": [candidate_paths[index - 1]], "acceptance_ids": ACCEPTANCE,
            "instructions": ["Record raw stdout and exit evidence."],
            "candidate_ref": candidate_ref, "oracle_ref": oracle_ref},
            [candidate_ref, oracle_ref, worker_report_ref])
        messages.append(tester_assignment); tester_assignment_ref = save_message(tester_assignment)
        tester_run = run_command(candidate_paths[index - 1], f"{suffix.lower()}-tester")
        # Attempt one deliberately records the known false-positive interpretation
        # that Planner must catch; the real stdout file records the unmet bytes.
        tester_check = {"name": "AC1 result as reported by the initial checker",
            "status": "passed", "evidence_ref": tester_run["stdout_ref"]}
        tester_report_payload = {"status": "passed", "summary":
            "Local command execution completed; raw output is preserved for Planner review.",
            "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_ref,
            "findings": [], "errors": [], "oracle_ref": oracle_ref,
            "checks": [tester_check],
            "deterministic_commands": [{"command_id": "VERSION", "command": tester_run["command"],
                "arguments": tester_run["arguments"], "workdir": tester_run["workdir"],
                "candidate_ref": candidate_ref, "input_refs": [plan_ref, tester_assignment_ref],
                "exit_code": tester_run["exit_code"], "stdout_sha256": tester_run["stdout_sha256"],
                "acceptance_id": "AC1", "evidence_ref": tester_run["execution_ref"]}]}
        tester_report = envelope(f"M{suffix}-TEST-REPORT", "job.report",
            ("tester", tester_id), ("manager", "manager-1"), attempt,
            tester_assignment["message_id"], tester_report_payload,
            [candidate_ref, oracle_ref, tester_assignment_ref, tester_run["stdout_ref"],
             tester_run["stderr_ref"], tester_run["exit_ref"], tester_run["execution_ref"]])
        messages.append(tester_report); tester_report_ref = save_message(tester_report)

        reviewer_assignment = envelope(f"M{suffix}-REVIEW-ASSIGN", "job.assign",
            ("manager", "manager-1"), ("reviewer", reviewer_id), attempt,
            tester_report["message_id"], {"objective": "Compare the original plan, candidate and Tester evidence.",
            "scope": [candidate_paths[index - 1]], "acceptance_ids": ACCEPTANCE,
            "instructions": ["Rerun the exact Tester-declared executable and arguments."],
            "candidate_ref": candidate_ref}, [candidate_ref, tester_report_ref, plan_ref])
        messages.append(reviewer_assignment); reviewer_assignment_ref = save_message(reviewer_assignment)
        reviewer_run = run_command(candidate_paths[index - 1], f"{suffix.lower()}-reviewer")
        rerun_status = "MATCH" if (reviewer_run["exit_code"] == tester_run["exit_code"] and
                                    reviewer_run["stdout_sha256"] == tester_run["stdout_sha256"]) else "MISMATCH"
        tester_message_ref = {**tester_report_ref, "artifact_id": tester_report["message_id"]}
        reviewer_report_payload = {"status": "passed" if rerun_status == "MATCH" else "failed",
            "summary": "Independent local rerun comparison; no native Reviewer session is claimed.",
            "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_ref,
            "findings": ["Compared exact executable, arguments, working directory, candidate, inputs, exit and normalized stdout hash."],
            "errors": [], "comparison": {"plan_ref": plan_ref,
                "tester_report_ref": tester_message_ref, "candidate_ref": candidate_ref,
                "findings": ["Tester report file matches the exact earlier Tester message."],
                "discrepancies": [], "independent_rerun": {
                    "status": rerun_status, "command_id": "VERSION", "command": reviewer_run["command"],
                    "arguments": reviewer_run["arguments"], "workdir": reviewer_run["workdir"],
                    "candidate_ref": candidate_ref, "input_refs": [plan_ref, tester_assignment_ref],
                    "exit_code": reviewer_run["exit_code"], "stdout_sha256": reviewer_run["stdout_sha256"],
                    "acceptance_id": "AC1", "evidence_ref": reviewer_run["execution_ref"],
                    "tester_evidence_ref": tester_run["execution_ref"],
                    "tester_exit_code": tester_run["exit_code"],
                    "tester_stdout_sha256": tester_run["stdout_sha256"]}}}
        reviewer_report = envelope(f"M{suffix}-REVIEW-REPORT", "job.report",
            ("reviewer", reviewer_id), ("manager", "manager-1"), attempt,
            reviewer_assignment["message_id"], reviewer_report_payload,
            [candidate_ref, plan_ref, tester_message_ref, reviewer_assignment_ref,
             reviewer_run["stdout_ref"], reviewer_run["stderr_ref"], reviewer_run["exit_ref"],
             reviewer_run["execution_ref"]])
        messages.append(reviewer_report); reviewer_report_ref = save_message(reviewer_report)
        return {"worker": worker_report, "tester": tester_report, "reviewer": reviewer_report,
                "tester_run": tester_run, "reviewer_run": reviewer_run,
                "message_refs": [worker_report_ref, tester_report_ref, reviewer_report_ref]}

    first = dispatch_and_check(1, "A1", "worker-1", "tester-1", "reviewer-1", candidate_refs[0])
    accept1 = envelope("M08-ACCEPT", "task.decision", ("manager", "manager-1"),
        ("planner", "planner-1"), "A1", first["reviewer"]["message_id"],
        {"disposition": "accept", "reason": "Initial Tester and Reviewer records reported PASS.",
         "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_refs[0],
         "report_ids": [first[role]["message_id"] for role in ("worker", "tester", "reviewer")]},
        [candidate_refs[0], *first["message_refs"]])
    messages.append(accept1); accept1_ref = save_message(accept1)
    progress1 = envelope("M09-PROGRESS", "plan.progress", ("manager", "manager-1"),
        ("planner", "planner-1"), "A1", accept1["message_id"],
        {"status": "ready-for-original-check", "objective": "Verify exact frozen output bytes.",
         "scope": [candidate_paths[0]], "acceptance_ids": ACCEPTANCE,
         "verified_progress": ["Initial Tester/Reviewer comparator records saved."],
         "next_action": "Check exact AC1 bytes against the original plan.", "candidate_ref": candidate_refs[0]},
        [accept1_ref, candidate_refs[0]])
    messages.append(progress1); progress1_ref = save_message(progress1)
    failed_check_ref = first["tester_run"]["stdout_ref"]
    plan_check1 = envelope("M10-PLANNER-FAIL", "plan.check", ("planner", "planner-1"),
        ("manager", "manager-1"), "A1", progress1["message_id"],
        {"status": "blocked", "summary": "AC1 fails: initial stdout contains CRLF, not the frozen LF bytes.",
         "acceptance_ids": ACCEPTANCE, "plan_ref": plan_ref,
         "results": [{"acceptance_id": "AC1", "status": "failed", "evidence_refs":
            [failed_check_ref, first["tester_run"]["exit_ref"], first["reviewer_run"]["execution_ref"]]}]},
        [plan_ref, progress1_ref, candidate_refs[0], failed_check_ref,
         first["tester_run"]["exit_ref"], first["reviewer_run"]["execution_ref"]])
    messages.append(plan_check1); plan_check1_ref = save_message(plan_check1)
    rework = envelope("M11-REWORK", "task.decision", ("manager", "manager-1"),
        ("planner", "planner-1"), "A1", plan_check1["message_id"],
        {"disposition": "rework", "reason": "Planner's original AC1 failure is confirmed by raw stdout evidence.",
         "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_refs[0],
         "report_ids": [first[role]["message_id"] for role in ("worker", "tester", "reviewer")],
         "failed_acceptance_ids": ["AC1"]},
        [plan_check1_ref, candidate_refs[0], failed_check_ref])
    messages.append(rework); rework_ref = save_message(rework)

    second = dispatch_and_check(2, "A2", "worker-2", "tester-2", "reviewer-2",
                                candidate_refs[1], candidate_refs[0], rework["message_id"])
    accept2 = envelope("M18-ACCEPT", "task.decision", ("manager", "manager-1"),
        ("planner", "planner-1"), "A2", second["reviewer"]["message_id"],
        {"disposition": "accept", "reason": "Fresh attempt's exact output and independent rerun match AC1.",
         "acceptance_ids": ACCEPTANCE, "candidate_ref": candidate_refs[1],
         "report_ids": [second[role]["message_id"] for role in ("worker", "tester", "reviewer")]},
        [candidate_refs[1], rework_ref, *second["message_refs"]])
    messages.append(accept2); accept2_ref = save_message(accept2)
    progress2 = envelope("M19-PROGRESS", "plan.progress", ("manager", "manager-1"),
        ("planner", "planner-1"), "A2", accept2["message_id"],
        {"status": "ready-for-original-check", "objective": "Verify unchanged frozen AC1.",
         "scope": [candidate_paths[1]], "acceptance_ids": ACCEPTANCE,
         "verified_progress": ["Fresh Tester check and Reviewer rerun match."],
         "next_action": "Perform the final original-plan check.", "candidate_ref": candidate_refs[1]},
        [accept2_ref, candidate_refs[1]])
    messages.append(progress2); progress2_ref = save_message(progress2)
    plan_check2 = envelope("M20-PLANNER-PASS", "plan.check", ("planner", "planner-1"),
        ("manager", "manager-1"), "A2", progress2["message_id"],
        {"status": "passed", "summary": "AC1 exact LF output and zero exit are supported by fresh raw evidence.",
         "acceptance_ids": ACCEPTANCE, "plan_ref": plan_ref,
         "results": [{"acceptance_id": "AC1", "status": "passed", "evidence_refs":
            [second["tester_run"]["stdout_ref"], second["tester_run"]["exit_ref"],
             second["reviewer_run"]["execution_ref"]]}]},
        [plan_ref, progress2_ref, candidate_refs[1], second["tester_run"]["stdout_ref"],
         second["tester_run"]["exit_ref"], second["reviewer_run"]["execution_ref"]])
    messages.append(plan_check2); save_message(plan_check2)

    packet = ("\n".join(json.dumps(m, ensure_ascii=False, separators=(",", ":")) for m in messages) + "\n").encode("utf-8")
    write_bytes("ordered-messages.jsonl", packet)
    sequence_path = OUT / "sequence-files.txt"
    sequence_path.write_text("\n".join(str((OUT / "messages" / f"{m['message_id']}.json").relative_to(ROOT)) for m in messages) + "\n", encoding="utf-8")
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "council-flow" / "scripts"))
    import contracts
    contracts.validate_sequence(messages, root=ROOT)
    (OUT / "sequence-validation.json").write_text(json.dumps({
        "valid": True, "message_count": len(messages), "attempts": ["A1", "A2"],
        "planner_failed_criterion": "AC1", "manager_rework_reply": "M10-PLANNER-FAIL",
        "fresh_worker_instance": "worker-2", "final_planner_status": "passed",
        "fixture_identities": "synthetic; not native agent observations",
    }, indent=2) + "\n", encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(run())
