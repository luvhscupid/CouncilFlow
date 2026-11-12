from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "evidence-manifest.json"
rows = []
for path in sorted(item for item in ROOT.rglob("*") if item.is_file() and item != MANIFEST):
    data = path.read_bytes()
    rows.append({
        "path": path.relative_to(ROOT).as_posix(),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
record = {
    "scope": "reports/gate3-preflight-2026-11-12",
    "file_count_excluding_this_manifest": len(rows),
    "files": rows,
}
MANIFEST.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"manifest": str(MANIFEST), "file_count": len(rows), "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}, indent=2))
