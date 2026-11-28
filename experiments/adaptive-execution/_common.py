"""Shared helpers. Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import hashlib
import json
import re
import sys
from datetime import datetime

sys.dont_write_bytecode = True


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate key: %s" % k)
        out[k] = v
    return out


def _const(name):
    raise ValueError("invalid JSON constant: %s" % name)


def strict_load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read(), object_pairs_hook=_pairs, parse_constant=_const)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def is_iso_timestamp(s):
    if not isinstance(s, str) or not _TS.match(s):
        return False
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def run_cli(validate_fn, argv):
    """argv: [FILE]. Prints {"valid", "errors"}; returns exit code 0 or 2."""
    if len(argv) != 1:
        errors = ["usage: FILE"]
    else:
        try:
            errors = validate_fn(strict_load(argv[0]))
        except (OSError, ValueError) as e:
            errors = ["cannot load: %s" % e]
    print(json.dumps({"valid": not errors, "errors": errors}))
    return 0 if not errors else 2
