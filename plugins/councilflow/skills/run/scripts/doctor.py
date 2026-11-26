"""Check local evidence structure and byte digests without authenticating claims."""

import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import sys

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)  # sibling modules also load when this file is imported by path
# Roles must not find __pycache__ written into the installed skill folder.
sys.dont_write_bytecode = True

import strict_json  # noqa: E402


ROLES = ("planner", "worker", "tester", "reviewer")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS_V1 = {"schema_version", "source_artifact", "source_hash_valid", "native_role_evidence",
              "tester_evidence", "reviewer_rerun", "planner_check", "dashboard"}
_FIELDS_V2 = _FIELDS_V1 | {"executable_artifact", "native_host"}


def load_evidence(raw):
    """Parse strict JSON, rejecting duplicate fields and non-finite values."""
    try:
        return strict_json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"invalid evidence JSON: {exc}") from exc


def _result(check, status, detail):
    return {"check": check, "status": status, "detail": detail}


def _relative_parts(relative):
    if (not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative
            or relative.startswith("/") or ntpath.splitdrive(relative)[0]):
        return None
    parts = relative.split("/")
    return parts if all(part not in {"", ".", ".."} for part in parts) else None


def _open_directory_chain(path, directory_flags):
    absolute = Path(os.path.abspath(path))
    current_fd = os.open(absolute.anchor, directory_flags)
    opened = [(current_fd, None, None)]
    try:
        for part in absolute.parts[1:]:
            info = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode):
                raise NotADirectoryError(part)
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            opened.append((next_fd, current_fd, (part, info.st_dev, info.st_ino)))
            current_fd = next_fd
    except BaseException:
        for descriptor_fd, _, _ in reversed(opened):
            os.close(descriptor_fd)
        raise
    return opened, current_fd


def _hash_artifact(root, relative):
    parts = _relative_parts(relative)
    if parts is None:
        return {"status": "FAIL", "detail": "artifact path must be a normalized relative path", "digest": None}
    if (os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd
            or os.stat not in os.supports_follow_symlinks or not hasattr(os, "O_NOFOLLOW")):
        return {"status": "UNVERIFIED", "detail": "this platform cannot enforce descriptor-relative no-follow reads", "digest": None}
    try:
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
        opened, current_fd = _open_directory_chain(root, directory_flags)
        try:
            for part in parts[:-1]:
                info = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
                if not stat.S_ISDIR(info.st_mode):
                    return {"status": "BLOCKED", "detail": "artifact path contains a non-directory component", "digest": None}
                next_fd = os.open(part, directory_flags, dir_fd=current_fd)
                opened.append((next_fd, current_fd, (part, info.st_dev, info.st_ino)))
                current_fd = next_fd
            info = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                return {"status": "FAIL", "detail": "symlink artifacts are not read", "digest": None}
            file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
            file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
            try:
                before = os.fstat(file_fd)
                path_before = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
                if not stat.S_ISREG(before.st_mode) or (before.st_dev, before.st_ino) != (path_before.st_dev, path_before.st_ino):
                    return {"status": "BLOCKED", "detail": "artifact is not a regular in-root file", "digest": None}
                digest = hashlib.sha256()
                with os.fdopen(file_fd, "rb", closefd=False) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                after = os.fstat(file_fd)
                path_after = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
                for directory_fd, parent_fd, identity in opened[1:]:
                    name, device, inode = identity
                    current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                    opened_info = os.fstat(directory_fd)
                    if ((current.st_dev, current.st_ino) != (device, inode)
                            or (opened_info.st_dev, opened_info.st_ino) != (device, inode)):
                        return {"status": "BLOCKED", "detail": "artifact ancestor changed during verification", "digest": None}
                signature = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                final_signature = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                path_signature = (path_after.st_dev, path_after.st_ino, path_after.st_size, path_after.st_mtime_ns, path_after.st_ctime_ns)
                if signature != final_signature or final_signature != path_signature:
                    return {"status": "BLOCKED", "detail": "artifact changed during verification", "digest": None}
            finally:
                os.close(file_fd)
        finally:
            for directory_fd, _, _ in reversed(opened):
                os.close(directory_fd)
    except (OSError, RuntimeError, ValueError):
        return {"status": "BLOCKED", "detail": "artifact cannot be safely opened beneath the evidence root", "digest": None}
    return {"status": "PASS", "detail": "artifact bytes were read from a stable regular file", "digest": digest.hexdigest()}


def _artifact_check(name, artifact, root):
    if artifact is None:
        return _result(name, "BLOCKED", "artifact reference is missing")
    if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
        return _result(name, "FAIL", "artifact must contain only path and sha256")
    digest = artifact["sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        return _result(name, "FAIL", "artifact SHA-256 is malformed")
    check = _hash_artifact(root, artifact["path"])
    if check["status"] != "PASS":
        return _result(name, check["status"], check["detail"])
    if check["digest"] != artifact["sha256"]:
        return _result(name, "FAIL", "artifact bytes do not match the declared SHA-256")
    return _result(name, "PASS", "artifact bytes match the declared SHA-256")


def _source_check(evidence, root):
    artifact = evidence.get("source_artifact")
    if artifact is None:
        if evidence.get("source_hash_valid") is not None:
            return _result("source_integrity", "UNVERIFIED", "caller hash claim is not independently checked")
        return _result("source_integrity", "BLOCKED", "source artifact reference is missing")
    if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
        return _result("source_integrity", "FAIL", "source_artifact must contain only path and sha256")
    relative, expected = artifact["path"], artifact["sha256"]
    if not isinstance(relative, str) or not relative or not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        return _result("source_integrity", "FAIL", "source artifact path or SHA-256 is malformed")
    if _relative_parts(relative) is None:
        return _result("source_integrity", "FAIL", "source artifact path must stay within the evidence root")
    check = _hash_artifact(root, relative)
    if check["status"] != "PASS":
        detail = ("referenced source artifact cannot be read within the evidence root"
                  if check["status"] == "BLOCKED" else check["detail"])
        return _result("source_integrity", check["status"], detail)
    if check["digest"] != expected:
        return _result("source_integrity", "FAIL", "source artifact bytes do not match the declared SHA-256")
    return _result("source_integrity", "PASS", "referenced source bytes match the declared SHA-256")


def _native_host_check(host):
    if host is None:
        return _result("native_host", "BLOCKED", "native host reference is missing")
    if not isinstance(host, dict) or set(host) != {"name", "version", "evidence_ref"}:
        return _result("native_host", "FAIL", "native_host must contain name, version, and evidence_ref")
    if any(not isinstance(value, str) or not value.strip() for value in host.values()):
        return _result("native_host", "FAIL", "native_host fields must be non-empty strings")
    return _result("native_host", "UNVERIFIED", "host name/version/reference are caller claims")


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
    version = evidence.get("schema_version")
    if type(version) is not int or version not in {1, 2}:
        raise ValueError("schema_version must be integer 1 or 2")
    fields = _FIELDS_V1 if version == 1 else _FIELDS_V2
    if not set(evidence).issubset(fields):
        raise ValueError("evidence contains unsupported fields")
    if version == 2 and not {"executable_artifact", "native_host"}.issubset(evidence):
        raise ValueError("schema_version 2 requires executable_artifact and native_host")
    if "source_hash_valid" in evidence and type(evidence["source_hash_valid"]) is not bool:
        raise ValueError("source_hash_valid must be a caller-claimed boolean")
    root = Path.cwd() if evidence_root is None else Path(evidence_root)
    results = [_result("evidence_schema", "PASS", f"top-level evidence object uses schema version {version}")]
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
    if version == 2:
        results.append(_artifact_check("executable_integrity", evidence["executable_artifact"], root))
        results.append(_native_host_check(evidence["native_host"]))
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
            raw = _read_evidence_file(evidence_path)
            root = evidence_path.absolute().parent.resolve()
        result = diagnose(load_evidence(raw), root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


def _read_evidence_file(path):
    if (os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd
            or os.stat not in os.supports_follow_symlinks or not hasattr(os, "O_NOFOLLOW")):
        raise ValueError("this platform cannot safely open an evidence file path; use stdin with '-'")
    absolute = Path(os.path.abspath(path))
    parts = absolute.parts[1:]
    if not parts:
        raise ValueError("evidence input must name a regular file")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    opened = []
    try:
        current_fd = os.open(absolute.anchor, directory_flags)
        opened.append((current_fd, None, None))
        for part in parts[:-1]:
            before_dir = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before_dir.st_mode):
                raise ValueError("evidence path contains a linked or non-directory component")
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            opened.append((next_fd, current_fd, (part, before_dir.st_dev, before_dir.st_ino)))
            current_fd = next_fd
        fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        try:
            before = os.fstat(fd)
            path_before = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("evidence input must be a regular file")
            if (before.st_dev, before.st_ino) != (path_before.st_dev, path_before.st_ino):
                raise ValueError("evidence file changed while opening")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read()
            after = os.fstat(fd)
            path_after = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
            signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
            if signature(before) != signature(after) or signature(after) != signature(path_after):
                raise ValueError("evidence input changed during reading")
        finally:
            os.close(fd)
        for directory_fd, parent_fd, identity in opened[1:]:
            name, device, inode = identity
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            opened_info = os.fstat(directory_fd)
            if ((current.st_dev, current.st_ino) != (device, inode)
                    or (opened_info.st_dev, opened_info.st_ino) != (device, inode)):
                raise ValueError("evidence file ancestor changed during reading")
    except OSError as exc:
        raise ValueError(f"evidence file cannot be safely opened ({type(exc).__name__})") from exc
    finally:
        for directory_fd, _, _ in reversed(opened):
            os.close(directory_fd)
    return raw.decode("utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
