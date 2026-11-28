"""Owner-message preservation and question packets (ADR 4).
Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Best-effort local file record; not authenticated capture and not transport enforcement.
The caller supplies store_dir; this module never defaults to a repo path and writes only inside it."""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import is_iso_timestamp, run_cli, sha256_bytes  # noqa: E402

SCHEMA = "adaptive-1"
KIND = "owner-message"
REVERSIBILITY = ["cheap_reversible", "costly_reversible", "irreversible_or_external",
                 "security_data_financial_legal", "owner_controlled"]
PACKET_FIELDS = ["question_id", "exact_text", "blocking", "reversibility", "affected_slices",
                 "permitted_default", "reason"]
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")  # no dots/slashes: ids cannot escape store_dir or collide by suffix
_SEQ = re.compile(r"^OS-(\d{4,})\.json$")


def _check_id(x, what):
    if not (isinstance(x, str) and _ID.match(x)):
        raise ValueError("%s must match %s" % (what, _ID.pattern))


def _write_new(path, data):
    with open(path, "xb") as f:  # 'x' refuses to overwrite
        f.write(data)


def _next_id(store_dir):
    nums = [int(m.group(1)) for n in os.listdir(store_dir) for m in [_SEQ.match(n)] if m]
    return "OS-%04d" % (max(nums, default=0) + 1)


def capture_owner_message(store_dir, raw_bytes, received_at, source_id=None):
    """Store exact bytes and a record; refuse to overwrite. Owner responses use this same call."""
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise ValueError("raw_bytes must be bytes")
    if not is_iso_timestamp(received_at):
        raise ValueError("received_at must be an ISO-8601 timestamp with timezone")
    os.makedirs(store_dir, exist_ok=True)
    if source_id is None:
        source_id = _next_id(store_dir)
    _check_id(source_id, "source_id")
    raw = bytes(raw_bytes)
    rec = {"schema_version": SCHEMA, "source_id": source_id, "sha256": sha256_bytes(raw),
           "byte_length": len(raw), "received_at": received_at, "kind": KIND}
    txt, js = (os.path.join(store_dir, source_id + e) for e in (".txt", ".json"))
    if os.path.exists(txt) or os.path.exists(js):
        raise FileExistsError("source_id already exists: %s" % source_id)
    _write_new(txt, raw)
    _write_new(js, (json.dumps(rec, indent=2) + "\n").encode("utf-8"))
    return rec


def verify_record(store_dir, source_id):
    """Re-hash the stored bytes against the record; returns error list (empty = intact)."""
    _check_id(source_id, "source_id")
    try:
        with open(os.path.join(store_dir, source_id + ".json"), "r", encoding="utf-8") as f:
            rec = json.load(f)
        with open(os.path.join(store_dir, source_id + ".txt"), "rb") as f:
            raw = f.read()
    except (OSError, ValueError) as e:
        return ["cannot read source %s: %s" % (source_id, e)]
    if not isinstance(rec, dict):
        return ["record is not an object"]
    errs = []
    if rec.get("source_id") != source_id:
        errs.append("record source_id mismatch")
    if rec.get("kind") != KIND or rec.get("schema_version") != SCHEMA:
        errs.append("record kind/schema_version mismatch")
    if rec.get("sha256") != sha256_bytes(raw):
        errs.append("sha256 mismatch: stored bytes were altered")
    if rec.get("byte_length") != len(raw):
        errs.append("byte_length mismatch")
    return errs


def validate_interpretation(obj):
    if not isinstance(obj, dict):
        return ["interpretation must be an object"]
    keys = ["interpretation_id", "source_id", "text", "author_role"]
    errs = ["unknown field %r" % k for k in obj if k not in keys]
    errs += ["missing field %r" % k for k in keys if k not in obj]
    for k in ("interpretation_id", "source_id"):
        if k in obj and not (isinstance(obj[k], str) and _ID.match(obj[k])):
            errs.append("%s must match %s" % (k, _ID.pattern))
    if "text" in obj and not (isinstance(obj["text"], str) and obj["text"].strip()):
        errs.append("text must be a nonempty string")
    if "author_role" in obj and obj["author_role"] != "planner":
        errs.append("author_role must be 'planner'")
    return errs


def write_interpretation(store_dir, interp):
    """Separate record <interpretation_id>.interpretation.json; never touches source files."""
    errs = validate_interpretation(interp)
    if errs:
        raise ValueError("; ".join(errs))
    if not os.path.exists(os.path.join(store_dir, interp["source_id"] + ".json")):
        raise ValueError("unknown source_id: %s" % interp["source_id"])
    _write_new(os.path.join(store_dir, interp["interpretation_id"] + ".interpretation.json"),
               (json.dumps(interp, indent=2) + "\n").encode("utf-8"))


def validate_question_packet(obj):
    if not isinstance(obj, dict):
        return ["question packet must be an object"]
    errs = []
    for k in obj:
        if k in ("approved", "default_applied"):
            errs.append("%r is not allowed: a question packet is not an answer or approval" % k)
        elif k not in PACKET_FIELDS:
            errs.append("unknown field %r" % k)
    errs += ["missing field %r" % k for k in PACKET_FIELDS if k not in obj]
    for k in ("question_id", "exact_text", "reason"):
        if k in obj and not (isinstance(obj[k], str) and obj[k].strip()):
            errs.append("%s must be a nonempty string" % k)
    if "blocking" in obj and not isinstance(obj["blocking"], bool):
        errs.append("blocking must be a boolean")
    if "reversibility" in obj and obj["reversibility"] not in REVERSIBILITY:
        errs.append("reversibility must be one of %s" % REVERSIBILITY)
    a = obj.get("affected_slices")
    if "affected_slices" in obj and not (isinstance(a, list) and all(isinstance(i, str) and i.strip() for i in a)):
        errs.append("affected_slices must be a list of nonempty strings")
    if "permitted_default" in obj:
        d = obj["permitted_default"]
        if d is not None and not (isinstance(d, str) and d.strip()):
            errs.append("permitted_default must be a nonempty string or null")
        elif d is not None and obj.get("reversibility") != "cheap_reversible":
            errs.append("permitted_default must be null unless reversibility is cheap_reversible")
    return errs


def check_outbound(packet, outbound_text):
    """Errors unless UTF-8 bytes of outbound_text equal exact_text bytes (no normalization)."""
    errs = validate_question_packet(packet)
    if errs:
        return errs
    try:
        same = outbound_text.encode("utf-8") == packet["exact_text"].encode("utf-8")
    except (AttributeError, UnicodeEncodeError):
        return ["outbound_text must be a UTF-8 encodable string"]
    return [] if same else ["outbound text differs from exact_text bytes"]


if __name__ == "__main__":
    sys.exit(run_cli(validate_question_packet, sys.argv[1:]))
