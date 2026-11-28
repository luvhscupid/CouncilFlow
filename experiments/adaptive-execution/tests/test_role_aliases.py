"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import ast
import os
import re
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PKG))
sys.path.insert(0, PKG)
import role_aliases as ra  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s2")
NAMES = ["Software Engineer", "QA Engineer", "Technical Audit Director"]


def fx(n):
    return os.path.join(FX, n)


def cli(path):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, os.path.join(PKG, "role_aliases.py"), path],
                          capture_output=True, text=True, env=env)


class AliasTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(ra.validate_aliases(strict_load(fx("valid-aliases.json"))), [])
        self.assertEqual(ra.validate_aliases(strict_load(os.path.join(PKG, "role_aliases.json"))), [])
        self.assertEqual(ra.validate_wire_untouched(strict_load(fx("valid-message.json"))), [])

    def test_invalid_alias_files(self):
        for n in ["unknown-role", "fourth-alias", "alias-is-wire-role"]:
            self.assertTrue(ra.validate_aliases(strict_load(fx("invalid-%s.json" % n))), n)
            self.assertEqual(cli(fx("invalid-%s.json" % n)).returncode, 2, n)

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ValueError):
            strict_load(fx("invalid-duplicate-key.json"))
        r = cli(fx("invalid-duplicate-key.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("duplicate key", r.stdout)

    def test_alias_as_sender(self):
        self.assertTrue(ra.validate_wire_untouched(strict_load(fx("invalid-alias-as-sender.json"))))

    def test_valid_cli_and_helpers(self):
        r = cli(fx("valid-aliases.json"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(ra.display_name("worker"), "Software Engineer")
        self.assertEqual(ra.display_name("planner"), "planner")
        self.assertEqual(ra.wire_role("QA Engineer"), "tester")

    def test_against_contracts_roles_text_only(self):
        p = os.path.join(ROOT, "plugins", "councilflow", "skills", "run", "scripts", "contracts.py")
        with open(p, encoding="utf-8") as f:
            m = re.search(r"^ROLES\s*=\s*(\{.*?\})\s*$", f.read(), re.M)
        self.assertTrue(m, "ROLES definition not found")
        roles = ast.literal_eval(m.group(1))
        for r in ra.WIRE:
            self.assertIn(r, roles)
        for n in NAMES:
            self.assertNotIn(n, roles)
            self.assertNotIn(n.lower(), roles)
        data = strict_load(os.path.join(PKG, "role_aliases.json"))
        self.assertLessEqual(set(data["wire_roles"]) | set(data["aliases"].values()), roles)

    def test_no_alias_used_as_role_value_in_new_files(self):
        pat = re.compile(r"(role|sender|recipient)[\"']?\s*[:=]\s*\{?\s*[\"']?(%s)" % "|".join(NAMES), re.I)
        for base in (PKG, os.path.join(ROOT, "docs", "adaptive")):
            for d, _, files in os.walk(base):
                for f in files:
                    if not f.endswith((".py", ".json", ".md")) or f == "test_role_aliases.py" \
                            or f == "invalid-alias-as-sender.json":
                        continue
                    with open(os.path.join(d, f), encoding="utf-8") as fh:
                        self.assertIsNone(pat.search(fh.read()), os.path.join(d, f))


if __name__ == "__main__":
    unittest.main()
