"""Independent maintenance source-lineage controls; not native/Gate 3 proof."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".agents/skills/council-flow/scripts"))
import contracts as c
FIXTURE = ROOT / "tests/fixtures/owner-version-original.txt"

def ref(identity, path, data, kind):
    return {"artifact_id": identity, "path": path, "sha256": hashlib.sha256(data).hexdigest(), "kind": kind}

def run():
    fixture = FIXTURE
    if not fixture.exists():
        fixture = Path(r"E:\Saint\PROJECTS\CouncilFlow-gate3-owner-fixture.txt")
    raw = fixture.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d"
    controls = []
    with tempfile.TemporaryDirectory(prefix="councilflow-review-") as temporary:
        root = Path(temporary)
        (root / "owner.txt").write_bytes(raw)
        source = ref("owner-source", "owner.txt", raw, "owner-original-source")
        captured = c.capture_criteria(source, root, owner_provenance={"owner-source"})
        def context(criteria=None, derivative_source=None, plan_source=None):
            selected = copy.deepcopy(captured["criteria"] if criteria is None else criteria)
            plan = {"plan_id": "P1", "plan_revision": 1, "acceptance": selected,
                    "original_source_ref": source if plan_source is None else plan_source}
            data = json.dumps(plan, ensure_ascii=False).encode("utf-8")
            (root / "plan.json").write_bytes(data)
            plan_ref = ref("plan", "plan.json", data, "plan")
            packet = {"protocol": "council-flow", "version": "1.0", "message_id": "M1", "message_type": "plan.publish",
                      "plan_id": "P1", "plan_revision": 1, "task_id": "T1", "attempt_id": "A1",
                      "sender": {"role": "planner", "instance_id": "planner-1"},
                      "recipient": {"role": "manager", "instance_id": "manager-1"}, "in_reply_to": None,
                      "payload": {"objective": "Independent source-lineage controls", "scope": ["demo/**"],
                                  "acceptance_ids": [entry["id"] for entry in selected], "plan_ref": plan_ref},
                      "evidence_refs": [plan_ref]}
            derivative = {"criteria": selected, "source_ref": source if derivative_source is None else derivative_source}
            data = json.dumps(derivative, ensure_ascii=False).encode("utf-8")
            (root / "derived.json").write_bytes(data)
            return packet, ref("derived", "derived.json", data, "owner-approved-criteria")
        def check(name, expected_error, *, criteria=None, derivative_source=None, plan_source=None, original=None, provenance=None):
            packet, derivative = context(criteria, derivative_source, plan_source)
            try:
                c.validate_sequence([packet], root=root, original_source_ref=source if original is None else original,
                                    authoritative_criteria_ref=derivative, require_criteria_fidelity=True,
                                    owner_provenance={"owner-source"} if provenance is None else provenance)
                code = None
            except c.ContractError as error:
                code = error.code
            assert (code is not None) == expected_error, (name, code)
            controls.append({"name": name, "passed": True, "rejection_code": code})
        check("unchanged original accepted", False)
        changed = copy.deepcopy(captured["criteria"])
        changed[0]["criterion"] = changed[0]["criterion"].replace(chr(96), "")
        check("matching rewritten plan and derivative rejected", True, criteria=changed)
        alias = dict(source, artifact_id="source-alias")
        check("derivative same bytes but substituted source identity rejected", True, derivative_source=alias)
        check("plan substituted source identity rejected", True, plan_source=alias)
        check("matching hash without caller provenance rejected", True, provenance=set())
        derivative_bytes = json.dumps({"criteria": captured["criteria"]}).encode()
        (root / "fake-original.json").write_bytes(derivative_bytes)
        fake = ref("owner-source", "fake-original.json", derivative_bytes, "owner-original-source")
        check("JSON derivative relabelled as original rejected", True, original=fake)
        packet, derivative = context()
        derivative["artifact_id"] = source["artifact_id"]
        try:
            c.validate_sequence([packet], root=root, original_source_ref=source,
                                authoritative_criteria_ref=derivative, require_criteria_fidelity=True,
                                owner_provenance={"owner-source"})
        except c.ContractError as error:
            assert error.code == "artifact_identity", error
            controls.append({"name": "original and derivative artifact-ID collision rejected", "passed": True,
                             "rejection_code": error.code})
        else:
            raise AssertionError("source/derivative artifact identity collision accepted")
        (root / "owner.txt").write_bytes(raw.replace(chr(96).encode(), b""))
        check("stale original pinned digest rejected", True)
    return {"controls": len(controls), "passed": sum(x["passed"] for x in controls), "details": controls,
            "fixture_sha256": hashlib.sha256(raw).hexdigest()}

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
