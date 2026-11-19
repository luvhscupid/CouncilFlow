"""Check local evidence structure and byte digests without authenticating claims."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROLES = ("planner", "worker", "tester", "reviewer")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = {"schema_version", "source_artifact", "source_hash_valid", "native_role_evidence",
           "tester_evidence", "reviewer_rerun", "planner_check", "dashboard"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def load_evidence(raw):
    """Parse strict JSON, rejecting duplicate fields and non-finite values."""
    try:
        return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"invalid evidence JSON: {exc}") from exc


def _result(check, status, detail):
    return {"check": check, "status": status, "detail": detail}


def _source_check(evidence, root):
    artifact = evidence.get("source_artifact")
    if artifact is None:
        if evidence.get("source_hash_valid") is not None:
            return _result("source_integrity", "UNVERIFIED", "caller hash claim is not independently checked")
        return _result("source_integrity", "BLOCKED", "source artifact reference is missing")
    if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
        return _result("source_integrity", "FAIL", "source_artifact must contain only path and sha256")
    relative = artifact["path"]
    digest = artifact["sha256"]
    if not isinstance(relative, str) or not relative or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        return _result("source_integrity", "FAIL", "source artifact path or SHA-256 is malformed")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return _result("source_integrity", "FAIL", "source artifact path must stay within the evidence root")
    try:
        base = Path(root).resolve()
        target = (base / candidate).resolve(strict=True)
    except (OSError, RuntimeError):
        return _result("source_integrity", "BLOCKED", "referenced source artifact cannot be read within the evidence root")
    try:
        target.relative_to(base)
    except ValueError:
        return _result("source_integrity", "FAIL", "source artifact resolves outside the evidence root")
    if not target.is_file():
        return _result("source_integrity", "BLOCKED", "referenced source artifact is not a regular file")
    try:
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
    except OSError:
        return _result("source_integrity", "BLOCKED", "referenced source artifact cannot be read within the evidence root")
    if actual != digest:
        return _result("source_integrity", "FAIL", "source artifact bytes do not match the declared SHA-256")
    return _result("source_integrity", "PASS", "referenced source bytes match the declared SHA-256")


def _role_check(evidence):
    records = evidence.get("native_role_evidence")
    if records is None:
        return _result("native_role_sequence", "BLOCKED", "native role evidence references are missing")
    if not isinstance(records, list):
        return _result("native_role_sequence", "FAIL", "native_role_evidence must be a list")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {"role", "identity", "evidence_ref"}:
            return _result("native_role_sequence", "FAIL", "each role record needs role, identity, and evidence_ref strings")
        role, identity, ref = record["role"], record["identity"], record["evidence_ref"]
        if any(not isinstance(value, str) or not value.strip() for value in (role, identity, ref)):
            return _result("native_role_sequence", "FAIL", "role, identity, and evidence_ref must be non-empty strings")
        if role not in ROLES or role in seen:
            return _result("native_role_sequence", "FAIL", "role records contain an unknown or duplicate role")
        seen.add(role)
    if seen != set(ROLES):
        return _result("native_role_sequence", "BLOCKED", "one or more required role evidence references are missing")
    return _result("native_role_sequence", "UNVERIFIED", "role labels and references are caller claims; native sessions are not authenticated")


def diagnose(evidence, evidence_root=None):
    """Return checks; PASS is limited to local schema and digest validation."""
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    if not set(evidence).issubset(_FIELDS):
        raise ValueError("evidence contains unsupported fields")
    version = evidence.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("schema_version must be integer 1")
    if "source_hash_valid" in evidence and type(evidence["source_hash_valid"]) is not bool:
        raise ValueError("source_hash_valid must be a caller-claimed boolean")
    root = Path.cwd() if evidence_root is None else Path(evidence_root)
    results = [_result("evidence_schema", "PASS", "top-level evidence object uses schema version 1")]
    results.append(_source_check(evidence, root))
    results.append(_role_check(evidence))
    for key, check in (("tester_evidence", "independent_tester"), ("reviewer_rerun", "reviewer_rerun"),
                       ("planner_check", "planner_final_check")):
        value = evidence.get(key)
        if value is None:
            results.append(_result(check, "BLOCKED", "required evidence is missing"))
        elif type(value) is bool:
            results.append(_result(check, "UNVERIFIED", "caller-provided evidence claim is not independently authenticated"))
        else:
            results.append(_result(check, "FAIL", "evidence claim has an unsupported type"))
    dashboard = evidence.get("dashboard")
    if dashboard is None:
        results.append(_result("dashboard", "SKIP", "optional dashboard projection is not configured"))
    elif isinstance(dashboard, dict):
        results.append(_result("dashboard", "UNVERIFIED", "dashboard configuration is not independently checked"))
    else:
        results.append(_result("dashboard", "FAIL", "dashboard configuration must be an object or null"))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", help="JSON evidence file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        if args.evidence == "-":
            raw = sys.stdin.read()
            root = Path.cwd()
        else:
            evidence_path = Path(args.evidence)
            with evidence_path.open(encoding="utf-8") as evidence_file:
                raw = evidence_file.read()
            root = evidence_path.resolve().parent
        result = diagnose(load_evidence(raw), root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
