"""Independent black-box oracle for the frozen A/B model-policy validator task."""
from __future__ import annotations
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

candidate_path = Path(sys.argv[1]).resolve()
fixture_path = Path(__file__).with_name("fixtures.json")
spec = importlib.util.spec_from_file_location("candidate_model_policy", candidate_path)
if spec is None or spec.loader is None:
    raise SystemExit("candidate module cannot be loaded")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fixtures = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
now = datetime.fromisoformat(fixtures["now_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
base_identity = fixtures["valid_identity"]
base_policy = fixtures["valid_policy"]
base_request = fixtures["valid_request"]

def set_path(root, dotted, value):
    names = dotted.split(".")
    node = root
    for name in names[:-1]:
        node = node[name]
    node[names[-1]] = value

for case in fixtures["cases"]:
    identity = json.loads(json.dumps(base_identity))
    policy = json.loads(json.dumps(base_policy))
    request = json.loads(json.dumps(base_request))
    mutation = case["mutation"]
    if isinstance(mutation, dict):
        for key, value in mutation.items():
            root_name, *rest = key.split(".")
            root = {"identity": identity, "policy": policy, "request": request}[root_name]
            set_path(root, ".".join(rest), value)
    result = module.authorize(identity, policy, request, now)
    if type(result) is not dict or set(result) != {"decision", "reason_code"}:
        raise AssertionError(f"{case['id']}: result must contain exactly decision/reason_code")
    actual = [result["decision"], result["reason_code"]]
    if actual != case["expected"]:
        raise AssertionError(f"{case['id']}: expected {case['expected']!r}, got {actual!r}")
    print(f"PASS {case['id']}")
print(f"PASS all {len(fixtures['cases'])} model-policy fixtures")
