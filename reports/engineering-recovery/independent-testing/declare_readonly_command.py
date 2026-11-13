"""Record a read-only deterministic source-fidelity command for independent rerun."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PYTHON = str(Path(sys.executable).resolve())
CODE = r'''import hashlib, pathlib, sys
root = pathlib.Path.cwd()
sys.path.insert(0, str(root / ".agents/skills/council-flow/scripts"))
import contracts
relative = "tests/fixtures/owner-version-original.txt"
raw = (root / relative).read_bytes()
expected_hash = "e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d"
assert hashlib.sha256(raw).hexdigest() == expected_hash
reference = {"artifact_id": "read-only-original-fixture", "path": relative, "sha256": expected_hash, "kind": "owner-original-source"}
captured = contracts.capture_criteria(reference, root, owner_provenance={"read-only-original-fixture"})
expected = [
    {"id": "AC1", "criterion": "When invoked with `--version`, print exactly `1.0.0` followed by a newline."},
    {"id": "AC2", "criterion": "The `--version` invocation exits with status code 0."},
    {"id": "AC3", "criterion": "All existing receipt-calculator tests continue to pass."},
]
assert captured["criteria"] == expected
assert captured["source_ref"] == reference
sys.stdout.buffer.write(b"ORIGINAL_CRITERIA_FIDELITY_OK\n")
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    inputs = (".agents/skills/council-flow/scripts/contracts.py", "tests/fixtures/owner-version-original.txt")
    hashes = {name: sha((ROOT / name).read_bytes()) for name in inputs}
    arguments = ["-B", "-c", CODE]
    process = subprocess.run([PYTHON, *arguments], cwd=ROOT, capture_output=True, timeout=30)
    assert process.returncode == 0, process.stderr
    assert process.stdout == b"ORIGINAL_CRITERIA_FIDELITY_OK\n"
    assert hashes == {name: sha((ROOT / name).read_bytes()) for name in inputs}
    (OUT / "readonly-command.stdout.bin").write_bytes(process.stdout)
    (OUT / "readonly-command.stderr.bin").write_bytes(process.stderr)
    manifest = json.loads((OUT / "candidate-before.json").read_text(encoding="utf-8"))
    declaration = {"kind": "Independent maintenance deterministic command, not formal E8/Gate 3 evidence",
        "command_id": "INDEPENDENT-ORIGINAL-SOURCE", "command": PYTHON, "arguments": arguments,
        "workdir": str(ROOT), "candidate_sha256": manifest["candidate_sha256"],
        "input_refs": [{"path": name, "sha256": digest} for name, digest in hashes.items()],
        "executable_sha256": sha(Path(PYTHON).read_bytes()), "exit_code": process.returncode,
        "stdout_sha256": sha(process.stdout.replace(b"\r\n", b"\n")),
        "normalization": "raw_stdout.replace(b'\\r\\n', b'\\n') only",
        "stdout_artifact": "reports/engineering-recovery/independent-testing/readonly-command.stdout.bin",
        "stderr_artifact": "reports/engineering-recovery/independent-testing/readonly-command.stderr.bin"}
    (OUT / "readonly-command-declaration.json").write_text(json.dumps(declaration, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"exit_code": declaration["exit_code"], "stdout_sha256": declaration["stdout_sha256"],
                      "candidate_sha256": declaration["candidate_sha256"]}))


if __name__ == "__main__":
    main()
