"""Disposable release output controls; these do not establish OS isolation."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_builder", ROOT / "tools/build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def fixture(root):
    root.mkdir()
    for directory in builder.DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for name in builder.FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"disposable standalone source")
    roles = root / ".claude/agents"
    roles.mkdir(parents=True, exist_ok=True)
    for role in builder.ROLES:
        (roles / (role + ".md")).write_bytes(b"disposable role")


class ReleaseOutputTests(unittest.TestCase):
    def test_existing_output_hardlinks_do_not_modify_outside_inodes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="release-output-") as temporary:
            parent = Path(temporary).resolve()
            authorized, outside = parent / "authorized", parent / "outside"
            fixture(authorized)
            outside.mkdir()
            destination = authorized / "dist"
            destination.mkdir()
            originals = {}
            for name in ("council-flow.zip.tmp", "council-flow.zip", "council-flow.zip.sha256", "council-flow.manifest.json"):
                sentinel = outside / name
                sentinel.write_bytes(b"outside sentinel: " + name.encode())
                originals[name] = sentinel.read_bytes()
                try:
                    os.link(sentinel, destination / name)
                except OSError as exc:
                    self.skipTest(f"hardlink creation unavailable: {exc}")
            builder.build(authorized)
            for name, data in originals.items():
                self.assertEqual((outside / name).read_bytes(), data, name)
            self.assertEqual((destination / "council-flow.zip.tmp").read_bytes(), originals["council-flow.zip.tmp"])

    def test_linked_output_directory_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="release-directory-") as temporary:
            parent = Path(temporary).resolve()
            authorized, outside = parent / "authorized", parent / "outside"
            fixture(authorized)
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_bytes(b"outside directory sentinel")
            link = authorized / "dist"
            junction = False
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                if os.name != "nt":
                    self.skipTest(f"directory symlink unavailable: {exc}")
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
                if result.returncode:
                    self.skipTest(f"directory symlink/junction unavailable: {exc}; mklink exit {result.returncode}")
                junction = True
            try:
                with self.assertRaises(ValueError):
                    builder.build(authorized)
                self.assertEqual(sentinel.read_bytes(), b"outside directory sentinel")
                self.assertEqual({p.name for p in outside.iterdir()}, {"sentinel.txt"})
            finally:
                # Remove only the link entry, before disposable-parent cleanup.
                self.assertEqual(link.parent.resolve(), authorized.resolve())
                if junction:
                    link.rmdir()
                else:
                    link.unlink()


if __name__ == "__main__":
    unittest.main()
