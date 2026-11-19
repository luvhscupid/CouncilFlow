"""Disposable release output controls; these do not establish OS isolation."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


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
    roles = root / ".codex/agents"
    roles.mkdir(parents=True)
    for role in builder.ROLES:
        (roles / (role + ".toml")).write_bytes(b"disposable role")


class ReleaseOutputTests(unittest.TestCase):
    def test_current_release_contains_dashboard_sources_and_tests(self):
        archive_path = ROOT / "dist/council-flow.zip"
        if not archive_path.is_file():
            report = builder.build(ROOT)
            archive_path = ROOT / report["archive"]
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
        required = {
            ".agents/skills/council-flow/scripts/dashboard.py",
            ".agents/skills/council-flow/dashboard/index.html",
            ".agents/skills/council-flow/dashboard/app.js",
            ".agents/skills/council-flow/dashboard/run-reader.js",
            ".agents/skills/council-flow/dashboard/styles.css",
            "demo/dashboard/tests/test_publisher.py",
            "demo/dashboard/tests/run-reader.test.cjs",
            "demo/dashboard/tests/auto-connection.test.cjs",
        }
        self.assertTrue(required <= names, f"missing dashboard release paths: {sorted(required - names)}")

    def test_release_and_ci_cover_the_documented_suites(self):
        release = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/verify-portable-release.yml").read_text(encoding="utf-8")
        expected = (
            "demo/gate3-demo",
            "python -m unittest discover -s demo/dashboard/tests -v",
            "node --test demo/dashboard/tests/run-reader.test.cjs demo/dashboard/tests/auto-connection.test.cjs",
        )
        for command in expected:
            with self.subTest(command=command):
                self.assertIn(command, release)
                self.assertIn(command, workflow)
        for path in ("demo/dashboard/tests/run-reader.test.cjs", "demo/dashboard/tests/auto-connection.test.cjs"):
            self.assertIn(path, release)
            self.assertIn(path, workflow)

    def test_archive_does_not_include_unbundled_experimental_tests(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="release-tests-") as temporary:
            authorized = Path(temporary).resolve() / "authorized"
            fixture(authorized)
            # Simulate an experimental test that imports source deliberately
            # excluded from the standalone release bundle.
            journal_test = authorized / "tests/test_journal.py"
            journal_test.write_text("import journal\n", encoding="utf-8")
            (authorized / "tests/test_portable.py").write_text(
                "import unittest\nclass PortableTests(unittest.TestCase):\n def test_runs(self): self.assertTrue(True)\n",
                encoding="utf-8")
            (authorized / "tests/test_efficiency_install.py").write_text(
                "import unittest\nclass IncludedTests(unittest.TestCase):\n def test_runs(self): self.assertTrue(True)\n",
                encoding="utf-8")
            self.assertTrue(builder.excluded("tests/test_journal.py"))
            report = builder.build(authorized)
            with zipfile.ZipFile(authorized / report["archive"]) as archive:
                self.assertNotIn("tests/test_journal.py", archive.namelist())
                archive.extractall(authorized / "extracted")
            run = subprocess.run([os.sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"],
                                 cwd=authorized / "extracted", capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Ran 2 tests", run.stderr)

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
