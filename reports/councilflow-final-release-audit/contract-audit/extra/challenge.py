"""Disposable synthetic contract challenges; no Owner or host provenance proof."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "3879c3d97efb6dfb5256445bf21748a95d0d2eab"
PRODUCTION = ".agents/skills/council-flow/scripts/contracts.py"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    source = ((ROOT / PRODUCTION).read_bytes() if args.current else
              subprocess.check_output(["git", "show", BASELINE + ":" + PRODUCTION], cwd=ROOT))
    results = []
    with tempfile.TemporaryDirectory() as directory:
        parent = Path(directory)
        module = parent / "contracts.py"
        module.write_bytes(source)
        spec = importlib.util.spec_from_file_location("challenged_contracts", module)
        c = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(c)
        root = parent / "authorized"
        root.mkdir()

        def run(name, expected, operation):
            try:
                operation()
                actual = True
                error = None
            except c.ContractError as exc:
                actual = False
                error = exc.code
            except Exception as exc:
                actual = "UNEXPECTED_EXCEPTION"
                error = type(exc).__name__
            results.append({"case": name, "expected_valid": expected, "actual_valid": actual,
                            "satisfied": actual == expected, "error": error})

        def ref(identity, path, kind="synthetic"):
            return {"artifact_id": identity, "path": path,
                    "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest(), "kind": kind}

        criteria = [{"id": "AC1", "criterion": "Print `café` exactly.\nKeep **Markdown**, punctuation, and 空白."},
                    {"id": "AC2", "criterion": "Second requirement.\r\nRetain CRLF."}]

        def context(changed=None):
            (root / "criteria.json").write_bytes(json.dumps({"criteria": criteria}, ensure_ascii=False).encode("utf-8"))
            acceptance = criteria if changed is None else changed
            (root / "plan.json").write_bytes(json.dumps({"plan_id": "P1", "plan_revision": 1,
                                                        "acceptance": acceptance}, ensure_ascii=False).encode("utf-8"))
            plan_ref = ref("plan", "plan.json", "plan")
            packet = {"protocol": "council-flow", "version": "1.0", "message_id": "M1",
                      "message_type": "plan.publish", "plan_id": "P1", "plan_revision": 1,
                      "task_id": "T1", "attempt_id": "A1", "sender": {"role": "planner", "instance_id": "planner"},
                      "recipient": {"role": "manager", "instance_id": "manager"}, "in_reply_to": None,
                      "payload": {"objective": "Synthetic challenge", "scope": ["demo/"],
                                  "acceptance_ids": [item["id"] for item in criteria], "plan_ref": plan_ref},
                      "evidence_refs": [plan_ref]}
            return packet, ref("criteria", "criteria.json", "owner-approved-criteria")

        def fidelity(changed=None):
            packet, trusted = context(changed)
            c.validate_sequence([packet], root=root, authoritative_criteria_ref=trusted, require_criteria_fidelity=True)

        run("exact_utf8_unicode_multiline_markdown", True, fidelity)
        mutations = {
            "added_space": lambda s: s.replace("Print ", "Print  "),
            "omitted_space": lambda s: s.replace("Print ", "Print"),
            "trailing_whitespace": lambda s: s + " ",
            "case": lambda s: s.replace("Print", "print"),
            "markdown_removed": lambda s: s.replace("`", ""),
            "punctuation_removed": lambda s: s.replace(".", ""),
            "unicode_normalized": lambda s: unicodedata.normalize("NFD", s),
            "unicode_confusable": lambda s: s.replace("café", "cаfé"),
            "lf_to_crlf": lambda s: s.replace("\n", "\r\n"),
            "newline_removed": lambda s: s.replace("\n", " "),
        }
        for name, transform in mutations.items():
            changed = copy.deepcopy(criteria)
            changed[0]["criterion"] = transform(changed[0]["criterion"])
            run("criteria_" + name, False, lambda value=changed: fidelity(value))
        for name, changed in {
            "omitted": criteria[:1], "duplicated": [criteria[0], criteria[0]],
            "reordered": list(reversed(criteria)),
            "added": criteria + [{"id": "AC3", "criterion": "New mandatory criterion."}],
            "source_id_mismatch": [{"id": "RENAMED", "criterion": criteria[0]["criterion"]}, criteria[1]],
        }.items():
            run("criteria_" + name, False, lambda value=changed: fidelity(value))

        packet, trusted = context()
        run("missing_mandatory_source", False, lambda: c.validate_sequence([packet], root=root, require_criteria_fidelity=True))
        run("ordinary_request_no_mandatory_sidecar", True, lambda: c.validate_sequence([packet], root=root))
        run("mandatory_without_root", False, lambda: c.validate_sequence([packet], authoritative_criteria_ref=trusted, require_criteria_fidelity=True))
        wrong_kind = dict(trusted, kind="agent-written")
        run("wrong_source_kind", False, lambda: c.validate_sequence([packet], root=root, authoritative_criteria_ref=wrong_kind, require_criteria_fidelity=True))
        (root / "criteria.json").write_bytes(b'{"criteria":[]}')
        run("stale_source_digest", False, lambda: c.validate_sequence([packet], root=root, authoritative_criteria_ref=trusted, require_criteria_fidelity=True))
        packet, trusted = context()
        (root / "criteria.json").rename(root / "renamed.json")
        run("renamed_source_stale_reference", False, lambda: c.validate_sequence([packet], root=root, authoritative_criteria_ref=trusted, require_criteria_fidelity=True))
        packet, trusted = context()
        (root / "criteria.json").write_bytes(b'{"criteria":[],"criteria":[]}')
        duplicate_ref = ref("criteria", "criteria.json", "owner-approved-criteria")
        run("source_duplicate_json_key", False, lambda: c.validate_sequence([packet], root=root, authoritative_criteria_ref=duplicate_ref, require_criteria_fidelity=True))
        packet, trusted = context()
        (root / "plan.json").write_bytes(b'{"plan_id":"P1","plan_id":"P1","plan_revision":1,"acceptance":[]}')
        packet["payload"]["plan_ref"] = ref("plan", "plan.json", "plan")
        packet["evidence_refs"] = [packet["payload"]["plan_ref"]]
        run("plan_duplicate_json_key", False, lambda: c.validate_sequence([packet], root=root, authoritative_criteria_ref=trusted, require_criteria_fidelity=True))

        raw_cases = [
            ("duplicate_keys", b'{"a":1,"a":2}'),
            ("invalid_utf8", b'\xff'),
            ("surrogate", b'"\\ud800"'),
            ("nonfinite", b'{"a":NaN}'),
            ("overflow", b'{"a":1e9999}'),
            ("oversize", b" " * (c.MAX_BYTES + 1)),
            ("overdepth", b"[" * 17 + b"0" + b"]" * 17),
            ("oversized_container", json.dumps(list(range(129))).encode()),
            ("oversized_string", json.dumps("x" * (c.MAX_STRING + 1)).encode()),
        ]
        for name, raw in raw_cases:
            run("json_" + name, False, lambda value=raw: c.loads(value))
        packet, trusted = context()
        for name, field, value in [
            ("boolean_integer", "plan_revision", True), ("unknown_field", "unknown", "x"),
            ("control_identity", "message_id", "M\x00"), ("surrogate_identity", "message_id", "\ud800"),
        ]:
            changed = copy.deepcopy(packet)
            changed[field] = value
            run("message_" + name, False, lambda value=changed: c.validate_message(value))
        for name, value in [("nul", "bad\x00text"), ("tab", "bad\ttext"), ("lone_cr", "bad\rtext")]:
            changed = copy.deepcopy(criteria)
            changed[0]["criterion"] = value
            run("criterion_control_" + name, False, lambda value=changed: fidelity(value))

        target = root / "evidence.txt"
        target.write_bytes(b"disposable evidence")
        good = ref("evidence", "evidence.txt")
        run("relative_artifact", True, lambda: c.artifact(good, root))
        stale = dict(good, sha256="0" * 64)
        run("stale_target_digest", False, lambda: c.artifact(stale, root))
        for name, spelling in [
            ("parent_traversal", "../evidence.txt"), ("posix_absolute", "/disposable/evidence.txt"),
            ("backslash", "dir\\evidence.txt"), ("windows_absolute_shape", "C:/disposable/evidence.txt"),
            ("windows_drive_relative_shape", "C:evidence.txt"),
        ]:
            item = dict(good, path=spelling)
            run("path_" + name, False, lambda value=item: c.artifact(value))
        if target.drive:
            for name, spelling in [("windows_absolute_in_root", target.as_posix()),
                                   ("windows_drive_relative_in_root", target.drive + "evidence.txt")]:
                item = dict(good, path=spelling)
                run("path_" + name, False, lambda value=item: c.artifact(value, root))
        outside = parent / "outside.txt"
        outside.write_bytes(b"actual outside fixture")
        outside_ref = dict(good, path=outside.as_posix(), sha256=hashlib.sha256(outside.read_bytes()).hexdigest())
        run("absolute_outside_rejected_before_open", False, lambda: c.artifact(outside_ref, root))

        for name, destination, expected in [("inside", target, True), ("outside", outside, False)]:
            link = root / (name + "-link.txt")
            try:
                link.symlink_to(destination)
            except (OSError, NotImplementedError) as exc:
                results.append({"case": "symlink_" + name, "status": "SKIPPED",
                                "reason": type(exc).__name__, "winerror": getattr(exc, "winerror", None),
                                "satisfied": None})
            else:
                item = dict(good, path=link.name, sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
                run("symlink_" + name, expected, lambda value=item: c.artifact(value, root))

    checked = [r for r in results if r["satisfied"] is not None]
    summary = {"source": "current" if args.current else BASELINE, "source_sha256": hashlib.sha256(source).hexdigest(),
               "kind": "synthetic-standalone-controls", "cases": len(results),
               "passed": sum(r["satisfied"] for r in checked), "failed": sum(not r["satisfied"] for r in checked),
               "skipped": len(results) - len(checked), "results": results,
               "limits": "No Owner authentication, actor provenance, race freedom, live host activation, or OS isolation established."}
    print(json.dumps(summary, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
