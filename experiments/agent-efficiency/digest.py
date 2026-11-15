"""Deterministic command-output capture, digest, and explicit artifact expansion."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

DEFAULT_LIMIT = 4000
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
IMPORTANT = re.compile(r"error|failed|failure|exception|traceback|warning|fatal", re.I)

def _safe_root(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root

def _artifact_path(root, run_id, stream):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id): raise ValueError("invalid run_id")
    path = root / f"{run_id}.{stream}.bin"
    if path.is_symlink(): raise ValueError("artifact symlink refused")
    return path

def _summary(data, limit):
    text = data.decode("utf-8", errors="replace")
    malformed = "\ufffd" in text
    clean = ANSI.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = clean.splitlines()
    important = [line for line in lines if IMPORTANT.search(line)]
    # Keep a deterministic head and tail. Failure lines outside the excerpt remain
    # discoverable through the explicit expandable full artifact.
    excerpt = clean if len(clean) <= limit else clean[:limit // 2] + "\n...[SUMMARY TRUNCATED]...\n" + clean[-(limit // 2):]
    parse_errors = []
    try:
        if clean.lstrip().startswith(("{", "[")): json.loads(clean)
    except json.JSONDecodeError as exc:
        parse_errors.append(f"JSON parse failed at line {exc.lineno}, column {exc.colno}")
    return excerpt, important[:20], len(clean) > limit, malformed, parse_errors

def capture(command, *, artifact_dir, cwd=None, timeout=None, limit=DEFAULT_LIMIT, env=None):
    """Run an explicit command and preserve complete stdout/stderr; timeout keeps partial output."""
    if not command: raise ValueError("command must not be empty")
    run_id = uuid.uuid4().hex
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        stdout, stderr, code, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
    return build_digest(stdout, stderr, exit_code=code, command=command, artifact_dir=artifact_dir,
                        run_id=run_id, cwd=cwd, timeout=timeout, timed_out=timed_out, limit=limit)

def build_digest(stdout, stderr, *, exit_code, command, artifact_dir, run_id=None, cwd=None, timeout=None, timed_out=False, limit=DEFAULT_LIMIT):
    if limit < 128: raise ValueError("summary limit must be at least 128 characters")
    run_id = run_id or uuid.uuid4().hex
    root = _safe_root(artifact_dir)
    output = {}
    flags = []
    for name, data in (("stdout", bytes(stdout)), ("stderr", bytes(stderr))):
        path = _artifact_path(root, run_id, name)
        path.write_bytes(data)
        excerpt, important, truncated, malformed, errors = _summary(data, limit)
        if truncated: flags.append("SUMMARY_TRUNCATED")
        if malformed: flags.append("MALFORMED_UTF8")
        if errors: flags.append("DIGEST_INCOMPLETE")
        output[name] = {"artifact": path.name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "excerpt": excerpt, "important_lines": important, "summary_truncated": truncated, "malformed_utf8": malformed, "parse_errors": errors}
    if timed_out: flags.append("TIMED_OUT")
    if exit_code not in (0, None): flags.append("COMMAND_FAILED")
    result = {"run_id":run_id,"command":list(command),"cwd":str(cwd) if cwd else None,"exit_code":exit_code,"timed_out":timed_out,"timeout_seconds":timeout,"streams":output,"flags":sorted(set(flags)),"artifact_dir":str(root)}
    return result

def expand(digest, stream):
    if stream not in ("stdout", "stderr"): raise ValueError("stream must be stdout or stderr")
    root = Path(digest["artifact_dir"]).resolve()
    name = digest["streams"][stream]["artifact"]
    if Path(name).name != name: raise ValueError("unsafe artifact path")
    path = root / name
    if path.is_symlink() or not path.is_file(): raise FileNotFoundError(f"artifact missing or unsafe: {name}")
    data = path.read_bytes()
    expected = digest["streams"][stream]["sha256"]
    if hashlib.sha256(data).hexdigest() != expected: raise ValueError("artifact integrity check failed")
    return data.decode("utf-8", errors="replace")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest="action",required=True)
    run=sub.add_parser("run"); run.add_argument("--artifacts",required=True); run.add_argument("--digest-output",required=True); run.add_argument("--timeout",type=float); run.add_argument("--limit",type=int,default=DEFAULT_LIMIT); run.add_argument("command",nargs=argparse.REMAINDER)
    exp=sub.add_parser("expand"); exp.add_argument("digest"); exp.add_argument("stream",choices=("stdout","stderr"))
    args=parser.parse_args(argv)
    if args.action=="run":
        command=args.command[1:] if args.command and args.command[0]=="--" else args.command
        result=capture(command,artifact_dir=args.artifacts,timeout=args.timeout,limit=args.limit)
        Path(args.digest_output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2,sort_keys=True)); return result["exit_code"] if result["exit_code"] is not None else 124
    digest=json.loads(Path(args.digest).read_text(encoding="utf-8")); sys.stdout.write(expand(digest,args.stream)); return 0

if __name__=="__main__": raise SystemExit(main())
