"""Worker, Tester and Reviewer are told to return full packets, which save accepts.

Follow-up to cleanup slice 1 (decision D2): one pointer line in both copies of each
role, so a role no longer returns the bare report body the first dogfood run saved.
"""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINE = ("Return your job.report as a full council-flow packet: the envelope plus the payload "
        "fields for your role listed in references/communication.md. The Manager saves it with "
        "scripts/contracts.py save, which refuses a bare report body.")


class ReportPacketPointerTests(unittest.TestCase):
    def test_every_role_copy_points_at_full_packets(self):
        for role in ("worker", "tester", "reviewer"):
            codex = ROOT / f".codex/agents/council-{role}.toml"
            with self.subTest(copy=str(codex)):
                text = tomllib.loads(codex.read_text(encoding="utf-8"))["developer_instructions"]
                self.assertIn(LINE, " ".join(text.split()))
            plugin = ROOT / f"plugins/councilflow/agents/council-{role}.md"
            if plugin.exists():
                with self.subTest(copy=str(plugin)):
                    self.assertIn("- " + LINE, plugin.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
