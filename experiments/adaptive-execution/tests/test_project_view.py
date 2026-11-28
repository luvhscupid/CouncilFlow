"""Tests for project_view.py. Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
AE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(AE))
FX = os.path.join(AE, "fixtures", "s11")
PV = os.path.join(AE, "project_view.py")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(*args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, PV] + list(args), cwd=ROOT, capture_output=True, text=True, env=env)


def fx(n):
    return os.path.join(FX, n)


def entry(i, t, st, c="c"):
    return dict(id=i, type=t, content=c, source_ids=["S"], status=st, timestamp="2026-11-27T10:00:00Z",
                version_introduced=1, superseded_entry_ids=[], affected_slices=["a"])


def ledger(entries):
    return dict(schema_version="adaptive-1", ledger_id="l", ledger_version=1, author_role="planner", entries=entries)


class T(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)

    def p(self, n):
        return os.path.join(self.td.name, n)

    def wjson(self, n, o):
        with open(self.p(n), "w", encoding="utf-8", newline="\n") as f:
            json.dump(o, f)
        return self.p(n)

    def full(self, out):
        return ["--ledger", fx("ledger.json"), "--slices", fx("slices.json"), "--readiness", fx("readiness.json"),
                "--qa", fx("qa.json"), "--audit", fx("audit.json"), "--out", out]

    def test_golden_and_stable(self):
        names = ["ledger.json", "slices.json", "readiness.json", "qa.json", "audit.json"]
        before = [sha(fx(n)) for n in names]
        a, b = self.p("a.md"), self.p("b.md")
        self.assertEqual(run(*self.full(a)).returncode, 0)
        self.assertEqual(run(*self.full(b)).returncode, 0)
        ra, rb = open(a, "rb").read(), open(b, "rb").read()
        self.assertEqual(ra, rb)
        self.assertEqual(ra, open(fx("expected-view.md"), "rb").read())
        self.assertNotIn(b"\r", ra)
        self.assertEqual(before, [sha(fx(n)) for n in names])

    def test_edit_view_is_not_read_back(self):
        a = self.p("a.md")
        run(*self.full(a))
        with open(a, "a", encoding="utf-8") as f:
            f.write("tampered\n")
        b = self.p("b.md")
        run(*self.full(b))
        self.assertEqual(open(b, "rb").read(), open(fx("expected-view.md"), "rb").read())

    def test_invalid_ledger_refused(self):
        out = self.p("o.md")
        r = run("--ledger", fx("invalid-ledger.json"), "--out", out)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(os.path.exists(out))

    def test_out_equals_input_or_dir_refused(self):
        led = self.wjson("l.json", ledger([entry("G1", "Goal", "established")]))
        before = sha(led)
        self.assertEqual(run("--ledger", led, "--out", led).returncode, 2)
        self.assertEqual(sha(led), before)
        self.assertEqual(run("--ledger", led, "--out", self.td.name).returncode, 2)

    def test_inert_rendering(self):
        bad = "# Fake heading\n| a | b |\n<script>alert(1)</script> [x](http://e) `c`"
        led = self.wjson("l.json", ledger([entry("G1", "Goal", "established", bad)]))
        out = self.p("o.md")
        self.assertEqual(run("--ledger", led, "--out", out).returncode, 0)
        text = open(out, encoding="utf-8").read()
        self.assertNotIn("<script>", text)
        self.assertNotIn("[x](", text)
        for line in text.split("\n"):
            if line.startswith("#"):
                self.assertTrue(line.startswith("## "), line)
            self.assertFalse(line.startswith("|"), line)
        self.assertEqual(sum(1 for l in text.split("\n") if l.startswith("# ")), 0)
        self.assertIn("\| a \| b \|", text)

    def test_budget_line(self):
        for n, extra, want in [(0, [], "0 of 5"), (5, [], "5 of 5"), (6, [], "6 of 5"), (6, ["--budget-limit", "8"], "6 of 8")]:
            ents = [entry("G1", "Goal", "established")] + [entry("A%d" % i, "Assumption", "provisional") for i in range(n)]
            led = self.wjson("l.json", ledger(ents))
            out = self.p("o.md")
            self.assertEqual(run("--ledger", led, "--out", out, *extra).returncode, 0)
            text = open(out, encoding="utf-8").read()
            self.assertIn("- %s used\n" % want, text)
            self.assertIn("readiness: not provided", text)
            self.assertIn("audit findings: not provided", text)


if __name__ == "__main__":
    unittest.main()
