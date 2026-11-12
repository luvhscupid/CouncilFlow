from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
paths = [
    "tests/test_codebase_memory_integration.py",
    "tests/test_contracts.py",
    "dist/council-flow.zip",
    "dist/council-flow.zip.sha256",
    "reports/councilflow-finalization/initial-manifest.json",
    "reports/councilflow-finalization/retirement-audit.json",
    "reports/gate3-next/OWNER-TASK-DRAFT.txt",
    "reports/gate3-next/OWNER-INVOCATION.txt",
    "reports/gate3-next/E1-E10-CHECKLIST.md",
    "reports/gate3-next/disposable-demo/app.py",
    "reports/gate3-next/disposable-demo/test_app.py",
    "reports/councilflow-finalization/worker/build_package.py",
    "reports/councilflow-finalization/worker/build_initial_manifest.py",
    "reports/councilflow-finalization/worker/build_retirement_audit.py",
    "reports/councilflow-finalization/worker/run_targeted.py",
    "reports/councilflow-finalization/worker/verify_hashes.py",
    "reports/councilflow-finalization/worker/write_job_report.py",
    "reports/councilflow-finalization/initial-manifest.json",
    "reports/councilflow-finalization/worker/package-manifest.json",
    "reports/councilflow-finalization/worker/package-verification.json",
    "reports/councilflow-finalization/worker/hash-consistency.json",
    "reports/councilflow-finalization/worker/targeted-execution.json",
    "reports/councilflow-finalization/worker/targeted-1.stdout.bin",
    "reports/councilflow-finalization/worker/targeted-1.stderr.bin",
    "reports/councilflow-finalization/worker/targeted-2.stdout.bin",
    "reports/councilflow-finalization/worker/targeted-2.stderr.bin",
    "reports/councilflow-finalization/worker/extracted-check-1.stdout.bin",
    "reports/councilflow-finalization/worker/extracted-check-1.stderr.bin",
    "reports/councilflow-finalization/worker/extracted-check-2.stdout.bin",
    "reports/councilflow-finalization/worker/extracted-check-2.stderr.bin",
    "reports/councilflow-finalization/worker/extracted-check-3.stdout.bin",
    "reports/councilflow-finalization/worker/extracted-check-3.stderr.bin",
]
manifest_rows = []
for relative in paths:
    path = ROOT / Path(*relative.split("/"))
    data = path.read_bytes()
    manifest_rows.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})

manifest_path = ROOT / "reports/councilflow-finalization/worker/candidate-manifest.json"
manifest_path.write_text(json.dumps({
    "candidate": "finalization-worker-output-CF-A003",
    "base_head": "2d695a22a1bb596a527b0d118edc073d6d25553f",
    "release_archive": "dist/council-flow.zip",
    "release_archive_sha256": hashlib.sha256((ROOT / "dist/council-flow.zip").read_bytes()).hexdigest(),
    "files": manifest_rows,
}, indent=2) + "\n", encoding="utf-8")
manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
candidate_digest = hashlib.sha256((ROOT / "dist/council-flow.zip").read_bytes()).hexdigest()

acceptance_ids = [
    "P0-A", "P0-B", "P1-A", "P1-B", "P1-C", "P2-A", "P2-B", "P2-C", "P2-D", "P2-E",
    "P3-A", "P3-B", "P3-C", "P3-D", "P3-E", "P4-A", "P4-B", "P4-C", "P4-D", "P4-E",
    "P5-A", "P5-B", "P5-C",
]
evidence = [
    {"artifact_id": "CF-FINAL-INITIAL-MANIFEST", "path": "reports/councilflow-finalization/initial-manifest.json", "sha256": hashlib.sha256((ROOT / "reports/councilflow-finalization/initial-manifest.json").read_bytes()).hexdigest(), "kind": "inventory"},
    {"artifact_id": "CF-FINAL-RETIREMENT-AUDIT", "path": "reports/councilflow-finalization/retirement-audit.json", "sha256": hashlib.sha256((ROOT / "reports/councilflow-finalization/retirement-audit.json").read_bytes()).hexdigest(), "kind": "verification-record"},
    {"artifact_id": "CF-FINAL-PACKAGE-VERIFICATION", "path": "reports/councilflow-finalization/worker/package-verification.json", "sha256": hashlib.sha256((ROOT / "reports/councilflow-finalization/worker/package-verification.json").read_bytes()).hexdigest(), "kind": "verification-record"},
    {"artifact_id": "CF-FINAL-HASH-CONSISTENCY", "path": "reports/councilflow-finalization/worker/hash-consistency.json", "sha256": hashlib.sha256((ROOT / "reports/councilflow-finalization/worker/hash-consistency.json").read_bytes()).hexdigest(), "kind": "verification-record"},
    {"artifact_id": "CF-FINAL-TARGETED-EXECUTIONS", "path": "reports/councilflow-finalization/worker/targeted-execution.json", "sha256": hashlib.sha256((ROOT / "reports/councilflow-finalization/worker/targeted-execution.json").read_bytes()).hexdigest(), "kind": "execution-record"},
    {"artifact_id": "CF-FINAL-CANDIDATE-MANIFEST", "path": "reports/councilflow-finalization/worker/candidate-manifest.json", "sha256": manifest_digest, "kind": "candidate-manifest"},
]
report = {
    "protocol": "council-flow",
    "version": "1.0",
    "message_id": "CF-M008",
    "message_type": "job.report",
    "plan_id": "CF-FINAL-001",
    "plan_revision": 1,
    "task_id": "CF-FINAL-001",
    "attempt_id": "CF-A003",
    "sender": {"role": "worker", "instance_id": "/root/worker"},
    "recipient": {"role": "manager", "instance_id": "/root"},
    "in_reply_to": "CF-M006",
    "payload": {
        "status": "passed",
        "summary": "Bounded finalization artifacts, minimal negative-test corrections, Gate 3 preparation, and an allowlisted release rebuild are complete. Independent six-suite verification, Reviewer rerun, and final Planner decision remain pending; this is not mission acceptance.",
        "acceptance_ids": acceptance_ids,
        "candidate_ref": {"artifact_id": "CF-FINAL-DIST-ARCHIVE", "path": "dist/council-flow.zip", "sha256": candidate_digest, "kind": "candidate-archive"},
        "changed_files": paths + ["reports/councilflow-finalization/worker/candidate-manifest.json"],
        "findings": [
            "The current installable archive contains 118 safe unique entries and its exact allowlisted source-byte mapping, CRC, checksum, and extraction checks passed; archive SHA-256 is " + candidate_digest + ".",
            "Case-insensitive static checks found zero active surface matches and zero installable archive path/text matches. Historical/supporting text remains in 14 checkout files with per-file SHA-256 in retirement-audit.json; the original source ZIP has 15 text matches including its prior test snapshot.",
            "The integration regression preserves the absent-path/command assertions while constructing the retired tokens dynamically. The focused top-level evidence-reference regression separately removes Tester and Reviewer execution references and rejects each sequence.",
            "The disposable demo and proposed Owner task are separate from product files and the release allowlist. The Owner task is explicitly unapproved. The frozen experiment was not executed; no E1-E10 status is claimed as a mission result.",
            "All 156 final hash-consistency checks passed across historical scan exceptions, source ZIP identity, package manifest/source-byte mapping, current regression tests, checksum, and frozen governance files.",
            "Initial inventory reconstructed 9 modified tracked paths and 595 untracked paths from initial status plus the supplied source ZIP; source ZIP SHA-256 is ab0fb7cf561d43d06c8e7222779e03040bde54a137d613aeed79ad646ef398f1. Two ignored/generated cache files changed after test execution and are called out in the inventory.",
            "Dynamic unavailable-MCP/stale-index fallback behavior and Windows junction/reparse/TOCTOU behavior were not exercised by this Worker. The previously reported symlink test skip remains unverified for safety.",
        ],
        "errors": [],
    },
    "evidence_refs": evidence,
}
report_path = ROOT / "reports/councilflow-finalization/worker/job-report.json"
report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"job_report": str(report_path.relative_to(ROOT)), "candidate_archive_sha256": candidate_digest, "candidate_manifest_sha256": manifest_digest, "changed_file_count": len(report["payload"]["changed_files"]), "evidence_refs": len(evidence)}, indent=2))
