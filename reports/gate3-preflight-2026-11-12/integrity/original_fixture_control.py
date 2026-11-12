from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
import zipfile


ARCHIVE = Path(sys.argv[1]).resolve()
EVIDENCE = Path(sys.argv[2]).resolve()
ROOT = Path(tempfile.mkdtemp(prefix="councilflow-original-fixture-"))
with zipfile.ZipFile(ARCHIVE) as archive:
    archive.extractall(ROOT)
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts


with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
    parent = Path(directory)
    authorized = parent / "authorized"
    authorized.mkdir()
    outside = parent / "outside.txt"
    outside.write_text("outside root", encoding="utf-8")
    link = authorized / "escape.txt"
    link.symlink_to(outside)
    item = {
        "artifact_id": "original-fixture-control",
        "path": link.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
        "kind": "test-fixture",
    }
    returned = contracts.artifact(item, ROOT)
    record = {
        "old_fixture_geometry_recreated": True,
        "link_path": item["path"],
        "authorized_subdirectory": str(authorized),
        "target": str(outside),
        "validator_root": str(ROOT),
        "target_within_validator_root": outside.resolve().is_relative_to(ROOT.resolve()),
        "digest_matches_target": item["sha256"] == hashlib.sha256(outside.read_bytes()).hexdigest(),
        "validator_result": "accepted",
        "would_old_assertRaises_fail": returned == item,
        "interpretation": "The old fixture escaped its authorized subdirectory but not ROOT, so artifact() correctly accepted it and the old expected rejection would fail on a symlink-capable platform.",
    }
output = EVIDENCE / "original-fixture-control.json"
output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(record, indent=2, ensure_ascii=False))
