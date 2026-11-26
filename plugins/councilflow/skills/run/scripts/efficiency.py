"""Explicit, offline efficiency helpers; installation alone activates nothing."""
from pathlib import Path
import runpy
import sys

# Roles must not find __pycache__ written into the installed skill folder.
sys.dont_write_bytecode = True


def main():
    actions = {"record": "recorder.py", "digest": "digest.py",
               "codex": "codex_adapter.py", "claude": "claude_adapter.py"}
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print("Usage: efficiency.py {record|digest|codex|claude} [arguments]", file=sys.stderr)
        return 0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 2
    runtime = Path(__file__).resolve().with_name("efficiency")
    target = runtime / actions[sys.argv[1]]
    sys.path.insert(0, str(runtime))
    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
