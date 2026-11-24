"""The shared usage-tracker pipeline keeps both trackers' output byte-identical.

adapter-golden.json was generated from the Codex and Claude trackers on main
(bdda379) before they were split into host event readers plus pipeline.py.
Every case runs the installed CLI with a fixed run id; stdout, exit code, the
--records line and the digest artifact bytes must match that golden output.
Regenerate only on purpose: python tests/test_efficiency_pipeline.py --write
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / ".agents/skills/council-flow/scripts/efficiency.py"
FIXTURES = ROOT / "tests/efficiency-fixtures"
GOLDEN = FIXTURES / "adapter-golden.json"
CODEX_FIXTURE = (FIXTURES / "codex-exec-sanitized.jsonl").read_text(encoding="utf-8")
CLAUDE_FIXTURE = (FIXTURES / "claude-stream-sanitized.jsonl").read_text(encoding="utf-8")


def lines(*events):
    return "".join(json.dumps(event) + "\n" for event in events)


CASES = {
    "codex-fixture": ("codex", CODEX_FIXTURE, ["--source", "synthetic-fixture", "--route", "codex/native-or-configured",
                                               "--revision", "abc123", "--elapsed-ms", "1500", "--cli-version", "0.1.0"]),
    "codex-fixture-exit-1": ("codex", CODEX_FIXTURE, ["--process-exit-code", "1"]),
    "codex-cancelled": ("codex", CODEX_FIXTURE, ["--cancelled"]),
    "codex-malformed-and-unsupported": ("codex", "{not json\n" + lines({"type": "mystery"}, {"type": "turn.started", "version": 2},
                                        {"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"}), []),
    "codex-failed-turn": ("codex", lines({"type": "thread.started", "thread_id": "t1"}, {"type": "turn.started"},
                                         {"type": "turn.failed", "error": {"message": "x"}}), []),
    "codex-empty": ("codex", "", []),
    "claude-fixture": ("claude", CLAUDE_FIXTURE, ["--source", "synthetic-fixture", "--gateway", "xkiro",
                                                  "--gateway-source", "configured", "--configured-model", "model-a",
                                                  "--cli-version", "2.0.0", "--revision", "abc123", "--elapsed-ms", "900"]),
    "claude-fixture-exit-2": ("claude", CLAUDE_FIXTURE, ["--process-exit-code", "2"]),
    "claude-cancelled": ("claude", CLAUDE_FIXTURE, ["--cancelled"]),
    "claude-single-json": ("claude", json.dumps({"type": "result", "subtype": "success", "is_error": False,
                                                 "session_id": "s1", "usage": {"input_tokens": 3, "output_tokens": 4}},
                                                indent=2), []),
    "claude-malformed-and-unsupported": ("claude", "{nope\n" + lines({"type": "mystery"}, {"type": "system", "version": 1}), []),
    "claude-empty": ("claude", "", []),
}


def _portable(data, root):
    """Same text on Windows and Linux: LF line ends, temp root hidden, '/' separators."""
    text = data.decode("utf-8").replace("\r\n", "\n")
    text = text.replace(root.replace("\\", "\\\\"), "<tmp>").replace(root, "<tmp>")
    return text.replace("\\\\", "/")


def run_case(name):
    host, stream, extra = CASES[name]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()  # one spelling of the temp root (Windows short names)
        artifacts, records = tmp / "artifacts", tmp / "records.jsonl"
        result = subprocess.run([sys.executable, "-I", str(CLI), host, "--artifacts", str(artifacts),
                                 "--records", str(records), "--run-id", "golden-" + name, *extra],
                                input=stream.encode("utf-8"), capture_output=True)
        root = str(tmp)
        files = {}
        if artifacts.exists():
            for path in sorted(artifacts.rglob("*")):
                if path.is_file():
                    files[path.relative_to(artifacts).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            "exit": result.returncode,
            "stdout": _portable(result.stdout, root),
            "stderr": _portable(result.stderr, root),
            "records": records.read_text(encoding="utf-8") if records.exists() else None,
            "artifacts": files,
        }


class PipelineGoldenTests(unittest.TestCase):
    def test_outputs_match_golden(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.assertEqual(sorted(golden), sorted(CASES))
        for name in CASES:
            with self.subTest(case=name):
                self.assertEqual(run_case(name), golden[name])

    def test_trackers_do_not_import_each_other(self):
        base = ROOT / ".agents/skills/council-flow/scripts/efficiency"
        self.assertNotIn("codex_adapter", (base / "claude_adapter.py").read_text(encoding="utf-8"))
        self.assertNotIn("claude_adapter", (base / "codex_adapter.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        GOLDEN.write_text(json.dumps({name: run_case(name) for name in CASES}, indent=1, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
    else:
        unittest.main()
