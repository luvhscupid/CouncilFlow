import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / ".agents" / "skills" / "council-flow"
PLUGIN = ROOT / "plugins" / "councilflow" / "skills" / "run"


def load_builder():
    path = ROOT / "tools" / "build_claude_plugin.py"
    spec = importlib.util.spec_from_file_location("build_claude_plugin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoutingPackageTests(unittest.TestCase):
    def test_routing_sources_match_between_host_packages(self):
        relative = [
            "scripts/routing/__init__.py", "scripts/routing/contract.py", "scripts/routing/core.py",
            "scripts/routing/encoders.py", "scripts/routing/composition.py", "scripts/routing/decision.py",
            "scripts/route.py",
        ]
        for name in relative:
            with self.subTest(name=name):
                self.assertTrue((CANON / name).is_file())
                self.assertTrue((PLUGIN / name).is_file())
                self.assertEqual(
                    hashlib.sha256((CANON / name).read_bytes()).hexdigest(),
                    hashlib.sha256((PLUGIN / name).read_bytes()).hexdigest(),
                )

    def test_route_entry_points_are_present(self):
        self.assertTrue((CANON / "scripts" / "route.py").is_file())
        self.assertTrue((PLUGIN / "scripts" / "route.py").is_file())

    def test_release_allowlist_includes_routing_sources(self):
        builder = load_builder()
        self.assertEqual(builder.drift(), [])
        self.assertIn("scripts/route.py", builder.shared_files(CANON))
        self.assertIn("scripts/routing/contract.py", builder.shared_files(CANON))


if __name__ == "__main__":
    unittest.main()
