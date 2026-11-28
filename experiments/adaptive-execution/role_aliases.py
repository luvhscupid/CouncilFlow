"""Role-name display aliases. Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import run_cli  # noqa: E402

WIRE = ["worker", "tester", "reviewer", "planner", "manager"]
EXPECTED = {"Software Engineer": "worker", "QA Engineer": "tester",
            "Technical Audit Director": "reviewer"}


def validate_aliases(obj):
    if not isinstance(obj, dict):
        return ["document must be an object"]
    errs = []
    if obj.get("version") != 1 or isinstance(obj.get("version"), bool):
        errs.append("version must be 1")
    if obj.get("wire_roles") != WIRE:
        errs.append("wire_roles must be exactly %s" % WIRE)
    al = obj.get("aliases")
    if not isinstance(al, dict):
        return errs + ["aliases must be an object"]
    for name, target in al.items():
        if name.lower() in WIRE:
            errs.append("alias %r is itself a wire role" % name)
        if target not in WIRE:
            errs.append("alias %r targets unknown role %r" % (name, target))
    if al != EXPECTED:
        errs.append("aliases must be exactly the three ADR names: %s" % sorted(EXPECTED))
    return errs


def display_name(role):
    for name, target in EXPECTED.items():
        if target == role:
            return name
    return role


def wire_role(alias):
    return EXPECTED[alias]


def validate_wire_untouched(obj):
    """Errors if any alias name appears as a 'role' value in a message-shaped JSON."""
    names = {n.lower() for n in EXPECTED}
    errs = []

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "role" and isinstance(v, str) and v.strip().lower() in names:
                    errs.append("%s.role uses alias %r" % (path, v))
                walk(v, path + "." + k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, "%s[%d]" % (path, i))

    walk(obj, "$")
    return errs


if __name__ == "__main__":
    sys.exit(run_cli(validate_aliases, sys.argv[1:]))
