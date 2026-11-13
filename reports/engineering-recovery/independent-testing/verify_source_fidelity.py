"""Independently specified source attacks against actual helper/API/CLI.

Packets here are synthetic contract inputs. They are not native role execution,
Owner approval evidence, or a formal Gate 3 experiment.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
HELPER = ROOT / ".agents/skills/council-flow/scripts/contracts.py"
ORIGINAL = Path(r"E:\Saint\PROJECTS\CouncilFlow-gate3-owner-fixture.txt")
ORIGINAL_SHA = "e0ec215cf548c73f98063b22127e99fccd4b4f80afae3a805beb38bb58e0d79d"
PYTHON = str(Path(sys.executable).resolve())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_ref(root, relative, value, identity, kind):
    raw = value if isinstance(value, bytes) else json_bytes(value)
    (root / relative).write_bytes(raw)
    return {"artifact_id": identity, "path": relative, "sha256": sha(raw), "kind": kind}


def publication(root, criteria, original_ref):
    plan = {"plan_id": "INDEPENDENT-P1", "plan_revision": 1,
            "original_source_ref": original_ref, "acceptance": criteria,
            "metadata": {"purpose": "independent maintenance negative control"}}
    plan_ref = write_ref(root, "plan.json", plan, "independent-plan", "plan")
    return {"protocol": "council-flow", "version": "1.0", "message_id": "INDEPENDENT-M1",
            "message_type": "plan.publish", "plan_id": "INDEPENDENT-P1", "plan_revision": 1,
            "task_id": "INDEPENDENT-T1", "attempt_id": "INDEPENDENT-A1",
            "sender": {"role": "planner", "instance_id": "synthetic-planner"},
            "recipient": {"role": "manager", "instance_id": "synthetic-manager"},
            "in_reply_to": None, "payload": {"objective": "Preserve saved Owner criteria.",
                "scope": ["demo/receipt/**"], "acceptance_ids": [c["id"] for c in criteria], "plan_ref": plan_ref},
            "evidence_refs": [plan_ref, original_ref]}


def main():
    spec = importlib.util.spec_from_file_location("independently_loaded_contracts", HELPER)
    contracts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contracts)
    raw = ORIGINAL.read_bytes()
    assert sha(raw) == ORIGINAL_SHA, "actual saved fixture changed; never substitute a generated fixture"
    # This is an independent expected-value extraction for the known single-line fixture.
    expected = [{"id": match.group(1), "criterion": match.group(2)}
                for match in re.finditer(r"(?m)^(AC[1-9][0-9]*): ([^\r\n]*)", raw.decode("utf-8"))]
    assert len(expected) == 3 and "`--version`" in expected[0]["criterion"]
    results = []
    with tempfile.TemporaryDirectory(prefix="cf-independent-source-") as temporary:
        root = Path(temporary)
        source_ref = write_ref(root, "original-owner-source.txt", raw, "observed-original", "owner-original-source")
        kwargs = {"root": root, "owner_provenance": {source_ref["artifact_id"]},
                  "original_source_ref": source_ref, "require_criteria_fidelity": True}

        def check(name, packet, passed=False, options=None):
            opts = dict(kwargs)
            if options:
                opts.update(options)
            try:
                contracts.validate_sequence([packet], **opts)
            except contracts.ContractError as error:
                if passed:
                    raise AssertionError(f"unchanged control {name} rejected: {error}") from error
                results.append({"name": name, "verdict": "REJECTED", "code": error.code, "field": error.field})
            else:
                if not passed:
                    raise AssertionError(f"independent source attack ACCEPTED: {name}")
                results.append({"name": name, "verdict": "ACCEPTED_UNCHANGED"})

        captured = contracts.capture_criteria(source_ref, root, owner_provenance=kwargs["owner_provenance"])
        assert captured["criteria"] == expected and captured["source_ref"] == source_ref
        packet = publication(root, expected, source_ref)
        check("unchanged-original", packet, passed=True)
        source_path = root / "source-ref.json"
        source_path.write_bytes(json_bytes(source_ref))
        packet_path = root / "packet.json"
        packet_path.write_bytes(json_bytes(packet))
        command = [PYTHON, "-B", str(HELPER), "sequence", str(packet_path), "--root", str(root),
                   "--original-source-ref", str(source_path), "--owner-provenance", source_ref["artifact_id"],
                   "--require-criteria-fidelity"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
        (OUT / "source-cli-valid.stdout.bin").write_bytes(process.stdout)
        (OUT / "source-cli-valid.stderr.bin").write_bytes(process.stderr)
        assert process.returncode == 0, process.stderr + process.stdout
        mutations = []
        for name, transform in [
            ("deleted-backticks", lambda text: text.replace("`", "")),
            ("punctuation", lambda text: text[:-1] + "!"),
            ("capitalization", lambda text: text.replace("When", "when", 1)),
            ("meaningful-space", lambda text: text.replace("print exactly", "print  exactly", 1)),
            ("meaningful-tab", lambda text: text.replace("print exactly", "print\texactly", 1)),
            ("meaningful-newline", lambda text: text + "\n"),
            ("changed-meaning", lambda text: text.replace("1.0.0", "9.9.9", 1)),
        ]:
            changed = copy.deepcopy(expected)
            changed[0]["criterion"] = transform(changed[0]["criterion"])
            mutations.append((name, changed))
        mutations.extend([
            ("missing-criterion", expected[:-1]),
            ("reordered-criteria", list(reversed(expected))),
            ("duplicate-criterion", [*expected, expected[0]]),
            ("added-mandatory-criterion", [*expected, {"id": "AC4", "criterion": "Invented extra mandatory requirement."}]),
        ])
        for name, changed in mutations:
            check(name, publication(root, changed, source_ref))
        packet = publication(root, expected, source_ref)
        check("missing-original-reference", packet, options={"original_source_ref": None})
        check("hash-is-not-owner-authorization", packet, options={"owner_provenance": set()})
        source_file = root / source_ref["path"]
        source_file.unlink()
        check("missing-original-file", packet)
        source_file.write_bytes(raw + b"changed source\n")
        check("stale-replaced-original", packet)
        source_file.write_bytes(raw)
        altered = copy.deepcopy(expected)
        altered[0]["criterion"] = altered[0]["criterion"].replace("`", "")
        derivative_ref = write_ref(root, "owner-criteria.json", {"criteria": altered},
                                   "generated-derivative", "owner-approved-criteria")
        altered_packet = publication(root, altered, source_ref)
        check("consistent-plan-and-derivative-contradict-original", altered_packet,
              options={"authoritative_criteria_ref": derivative_ref})
        masquerade = dict(derivative_ref, kind="owner-original-source")
        check("generated-json-masquerades-as-original", publication(root, altered, masquerade),
              options={"original_source_ref": masquerade, "owner_provenance": {masquerade["artifact_id"]}})
        substituted_ref = write_ref(root, "rewritten-original.txt",
                                    raw.replace(b"`", b""), "substituted-original", "owner-original-source")
        check("internal-original-reference-substitution", publication(root, altered, substituted_ref))
        # Derivative provenance must not silently contradict the pinned raw original.
        wrong_derivative = write_ref(root, "wrong-source-derivative.json",
             {"source_ref": substituted_ref, "criteria": expected}, "wrong-source-derivative", "owner-approved-criteria")
        check("derivative-source-reference-substitution", publication(root, expected, source_ref),
              options={"authoritative_criteria_ref": wrong_derivative})
        collision = write_ref(root, "identity-collision-derivative.json",
                              {"source_ref": source_ref, "criteria": expected},
                              source_ref["artifact_id"], "owner-approved-criteria")
        collision_packet = publication(root, expected, source_ref)
        collision_packet["evidence_refs"] = [collision_packet["payload"]["plan_ref"]]
        check("original-derivative-artifact-identity-collision", collision_packet,
              options={"authoritative_criteria_ref": collision})
        # Newline/tab preservation in supported multi-line source, with exact source hash.
        rich = b"AC1: Keep\tthis  spacing.\r\nContinuation `x`.\r\nAC2: Last line.\r\n"
        rich_ref = write_ref(root, "rich-source.txt", rich, "rich-original", "owner-original-source")
        rich_capture = contracts.capture_criteria(rich_ref, root, owner_provenance={rich_ref["artifact_id"]})
        assert rich_capture["criteria"] == [{"id": "AC1", "criterion": "Keep\tthis  spacing.\r\nContinuation `x`."},
                                           {"id": "AC2", "criterion": "Last line."}]
        results.append({"name": "exact-tabs-and-CRLF-multiline", "verdict": "ACCEPTED_UNCHANGED"})
    report = {"kind": "Independent maintenance source/API/CLI controls, synthetic packets only",
              "helper_sha256": sha(HELPER.read_bytes()), "original_source": str(ORIGINAL),
              "original_source_sha256": ORIGINAL_SHA, "results": results,
              "valid_cli": {"command": command[0], "arguments": command[1:], "workdir": str(ROOT),
                            "exit_code": process.returncode,
                            "normalized_stdout_sha256": sha(process.stdout.replace(b"\r\n", b"\n"))}}
    (OUT / "source-fidelity-results.json").write_bytes(json_bytes(report))
    print(json.dumps({"source_controls": len(results), "attacks_rejected": sum(x["verdict"] == "REJECTED" for x in results),
                      "unchanged_controls_passed": sum(x["verdict"] == "ACCEPTED_UNCHANGED" for x in results)}))


if __name__ == "__main__":
    main()
