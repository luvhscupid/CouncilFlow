"""Deterministic, evidence-only diagnostics; absence never counts as success."""

import argparse
import json
import sys


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def load_evidence(raw):
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant: {value}")))


def diagnose(evidence):
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    results = []

    def add(check, status, detail):
        results.append({"check": check, "status": status, "detail": detail})

    source = evidence.get("source_hash_valid")
    add("source_integrity", "UNVERIFIED",
        "caller-supplied hash claim is not independently checked" if source is not None else "source hash evidence missing")

    required = evidence.get("required_roles", ["planner", "worker", "tester", "reviewer"])
    native_roles = evidence.get("native_roles")
    if not isinstance(required, list) or not isinstance(native_roles, list):
        add("native_role_sequence", "UNVERIFIED", "native role evidence missing or malformed")
    else:
        add("native_role_sequence", "UNVERIFIED", "caller-supplied role labels do not prove native sessions")

    for key, check in (("tester_evidence", "independent_tester"), ("reviewer_rerun", "reviewer_rerun"),
                       ("planner_check", "planner_final_check")):
        value = evidence.get(key)
        add(check, "UNVERIFIED",
            "caller-supplied success/failure claim is not independently checked" if value is not None else "evidence missing")

    add("dashboard", "SKIP" if evidence.get("dashboard") is None else "UNVERIFIED",
        "no dashboard projection configured" if evidence.get("dashboard") is None else "dashboard evidence requires review")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", help="JSON evidence file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.evidence == "-" else open(args.evidence, encoding="utf-8").read()
        result = diagnose(load_evidence(raw))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
