"""Deterministic command-output capture, digest, and explicit artifact expansion."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import uuid

DEFAULT_LIMIT = 4000
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IMPORTANT = re.compile(r"error|failed|failure|exception|traceback|warning|fatal", re.I)
FAILURE_ID = re.compile(r"^(?:FAIL|ERROR): (.+)$|^FAILED (\S+::\S+)", re.M)

def _reject_links(path):
    # Check before resolve(), which would hide symlinks and Windows junctions.
    # This is a best-effort path check, not race-free OS containment.
    for part in (path, *path.parents):
        try: info = part.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError("linked artifact path refused")

def _safe_root(root, *, create=True):
    root = Path(os.path.abspath(root))
    _reject_links(root)
    if create: root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir(): raise FileNotFoundError("artifact directory missing")
    return root

def _artifact_path(root, run_id, stream):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id): raise ValueError("invalid run_id")
    path = root / f"{run_id}.{stream}.bin"
    _reject_links(path)
    return path

def _bounded(text, limit):
    if len(text) <= limit: return text
    marker = "\n...[SUMMARY TRUNCATED]...\n"
    head = (limit - len(marker)) // 2
    tail = limit - len(marker) - head
    return text[:head] + marker + text[-tail:]

def _summary(data, limit):
    try:
        text = data.decode("utf-8"); malformed = False
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace"); malformed = True
    clean = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    failure_ids = []
    identifiers_truncated = False
    remaining_ids = limit
    for match in FAILURE_ID.finditer(clean):
        identifier = match.group(1) or match.group(2)
        if len(failure_ids) == 20 or len(identifier) > remaining_ids:
            identifiers_truncated = True; continue
        failure_ids.append(identifier)
        remaining_ids -= len(identifier)
    lines = clean.splitlines()
    important = []
    remaining = limit
    important_truncated = False
    for line in lines:
        if not IMPORTANT.search(line): continue
        if len(important) == 20 or not remaining:
            important_truncated = True; continue
        selected = line[:remaining]
        important_truncated |= len(selected) < len(line)
        important.append(selected)
        remaining -= len(selected)
    # Keep a deterministic head and tail. Failure lines outside the excerpt remain
    # discoverable through the explicit expandable full artifact.
    excerpt = _bounded(clean, limit)
    parse_errors = []
    try:
        if clean.lstrip().startswith(("{", "[")): json.loads(clean)
    except json.JSONDecodeError as exc:
        parse_errors.append(f"JSON parse failed at line {exc.lineno}, column {exc.colno}")
    return excerpt, important, failure_ids, len(clean) > limit or important_truncated or identifiers_truncated, malformed, parse_errors

def _validate_options(limit, timeout):
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 128:
        raise ValueError("summary limit must be at least 128 characters")
    if timeout is not None and (not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError("timeout must be finite and positive")

def capture(command, *, artifact_dir, cwd=None, timeout=None, limit=DEFAULT_LIMIT, env=None):
    """Run an explicit command and preserve complete stdout/stderr; timeout keeps partial output."""
    if not command: raise ValueError("command must not be empty")
    _validate_options(limit, timeout)
    _safe_root(artifact_dir)
    run_id = uuid.uuid4().hex
    with subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            timed_out = True
        code = proc.returncode
    result = build_digest(stdout, stderr, exit_code=code, command=command, artifact_dir=artifact_dir,
                        run_id=run_id, cwd=cwd, timeout=timeout, timed_out=timed_out, limit=limit)
    result["cwd"] = str(Path(cwd or os.getcwd()).resolve())
    # Relative/PATH lookup is host dependent; never claim an unobserved executable.
    result["executable"] = str(command[0]) if os.path.isabs(command[0]) else None
    result["environment"] = "inherited" if env is None else "caller-supplied; values not recorded"
    return result

def build_digest(stdout, stderr, *, exit_code, command, artifact_dir, run_id=None, cwd=None, timeout=None, timed_out=False, limit=DEFAULT_LIMIT):
    _validate_options(limit, timeout)
    run_id = run_id or uuid.uuid4().hex
    root = _safe_root(artifact_dir)
    output = {}
    flags = []
    paths = {name: _artifact_path(root, run_id, name) for name in ("stdout", "stderr")}
    for path in paths.values():
        if path.exists(): raise FileExistsError(f"artifact already exists: {path.name}")
    for name, data in (("stdout", bytes(stdout)), ("stderr", bytes(stderr))):
        path = paths[name]
        with path.open("xb") as artifact: artifact.write(data)
        excerpt, important, failure_ids, truncated, malformed, errors = _summary(data, limit)
        if truncated: flags.append("SUMMARY_TRUNCATED")
        if malformed: flags.append("MALFORMED_UTF8")
        if truncated or malformed or errors: flags.append("DIGEST_INCOMPLETE")
        output[name] = {"artifact": path.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "excerpt": excerpt, "important_lines": important, "failing_test_ids": failure_ids, "summary_truncated": truncated, "malformed_utf8": malformed, "parse_errors": errors}
    if timed_out: flags.extend(("TIMED_OUT", "DIGEST_INCOMPLETE"))
    if exit_code is None: flags.append("DIGEST_INCOMPLETE")
    if exit_code not in (0, None): flags.append("COMMAND_FAILED")
    result = {"run_id":run_id,"command":list(command),"cwd":str(cwd) if cwd is not None else None,"exit_code":exit_code,"timed_out":timed_out,"timeout_seconds":timeout,"streams":output,"flags":sorted(set(flags)),"artifact_dir":str(root)}
    return result

def expand_bytes(digest, stream):
    """Return original bytes only after validating their path and SHA-256."""
    if stream not in ("stdout", "stderr"): raise ValueError("stream must be stdout or stderr")
    root = _safe_root(digest["artifact_dir"], create=False)
    name = digest["streams"][stream]["artifact"]
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\." + stream + r"\.bin", name): raise ValueError("unsafe artifact path")
    path = root / name
    _reject_links(path)
    if not path.is_file(): raise FileNotFoundError(f"artifact missing or unsafe: {name}")
    data = path.read_bytes()
    expected = digest["streams"][stream]["sha256"]
    if hashlib.sha256(data).hexdigest() != expected: raise ValueError("artifact integrity check failed")
    return data

def expand(digest, stream):
    """Compatibility text view; use expand_bytes or CLI expand for original bytes."""
    return expand_bytes(digest, stream).decode("utf-8", errors="replace")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest="action",required=True)
    run=sub.add_parser("run"); run.add_argument("--artifacts",required=True); run.add_argument("--digest-output",required=True); run.add_argument("--timeout",type=float); run.add_argument("--limit",type=int,default=DEFAULT_LIMIT); run.add_argument("command",nargs=argparse.REMAINDER)
    exp=sub.add_parser("expand"); exp.add_argument("digest"); exp.add_argument("stream",choices=("stdout","stderr"))
    args=parser.parse_args(argv)
    if args.action=="run":
        output_path = Path(os.path.abspath(args.digest_output))
        _safe_root(output_path.parent)
        _reject_links(output_path)
        if output_path.exists(): raise FileExistsError("digest output already exists")
        command=args.command[1:] if args.command and args.command[0]=="--" else args.command
        result=capture(command,artifact_dir=args.artifacts,timeout=args.timeout,limit=args.limit)
        with output_path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True)); return 124 if result["timed_out"] else result["exit_code"]
    digest=json.loads(Path(args.digest).read_text(encoding="utf-8")); sys.stdout.buffer.write(expand_bytes(digest,args.stream)); return 0

if __name__=="__main__":
    code = main()
    if os.name != "nt" and code < 0:
        # Preserve signal termination as well as ordinary exit codes on POSIX.
        signal.signal(-code, signal.SIG_DFL)
        os.kill(os.getpid(), -code)
    raise SystemExit(code)
