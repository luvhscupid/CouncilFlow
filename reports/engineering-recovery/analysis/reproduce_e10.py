"""Reproduce the historical input-substitution gap; never certify Gate 3."""
from pathlib import Path
import sys
import json
import hashlib
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".agents/skills/council-flow/scripts/contracts.py"
sys.path.insert(0, str(SCRIPT.parent))
import contracts as c

HISTORY = Path(r"E:\Saint\PROJECTS\CouncilFlow-gate3")
FIXTURE = Path(r"E:\Saint\PROJECTS\CouncilFlow-gate3-owner-fixture.txt")
raw = FIXTURE.read_bytes()
history_dir = HISTORY / "reports/councilflow-version"
criteria = c.read_json(history_dir / "owner-criteria.json")
reference = {
    "artifact_id": "reproduction-derived-criteria",
    "path": "reports/councilflow-version/owner-criteria.json",
    "sha256": hashlib.sha256((history_dir / "owner-criteria.json").read_bytes()).hexdigest(),
    "kind": "owner-approved-criteria",
}
messages = [c.read_json(history_dir / "manager-progress-initial.json"),
            c.read_json(history_dir / "plan-publish.json")]
c.validate_sequence(messages, root=HISTORY)
c.validate_sequence(messages, root=HISTORY, authoritative_criteria_ref=reference,
                    require_criteria_fidelity=True)
original = [{"id": match.group(1).decode(), "criterion": match.group(2).decode(),
             "start": match.start(2), "end": match.end(2)}
            for match in re.finditer(rb"(?m)^(AC[0-9]+): ([^\r\n]*)", raw)]
observations = {
    "baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "contracts_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    "original_source": str(FIXTURE),
    "original_source_sha256": hashlib.sha256(raw).hexdigest(),
    "original_source_size": len(raw),
    "criteria_source": str(history_dir / "owner-criteria.json"),
    "criteria_sha256": reference["sha256"],
    "normal_sequence_valid": True,
    "self_consistent_derivative_fidelity_valid": True,
    "original": original,
    "derived": criteria["criteria"],
    "mismatches": [a["id"] for a, b in zip(original, criteria["criteria"])
                   if a["criterion"] != b["criterion"]],
    "meaning": "Baseline accepts actual historical plan and mutually consistent derivative despite disagreement with the original saved Owner fixture. This is reproduction, not Gate 3 certification or proof of approval.",
}
output = Path(__file__).with_name("e10-baseline-reproduction.json")
output.write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(observations, indent=2))
