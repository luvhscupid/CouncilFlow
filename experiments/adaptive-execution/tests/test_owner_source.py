"""Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PKG)
import owner_source as osrc  # noqa: E402
from _common import strict_load  # noqa: E402

FX = os.path.join(PKG, "fixtures", "s7")
TS = "2026-11-27T10:00:00Z"
SAMPLES = {"crlf": b"a\r\nb\r\n", "lf": b"a\nb\n", "trailing": b"hi  \t \n", "utf8": "café 中文 \U0001f600".encode("utf-8"), "empty": b""}


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.d = self._t.name

    def test_round_trip_byte_exact(self):
        for name, raw in SAMPLES.items():
            with self.subTest(name):
                rec = osrc.capture_owner_message(self.d, raw, TS, source_id="S-" + name)
                with open(os.path.join(self.d, "S-%s.txt" % name), "rb") as f:
                    self.assertEqual(f.read(), raw)
                self.assertEqual(rec["byte_length"], len(raw))
                self.assertEqual(rec["kind"], "owner-message")
                self.assertEqual(osrc.verify_record(self.d, "S-" + name), [])

    def test_generated_ids_sequence(self):
        a = osrc.capture_owner_message(self.d, b"x", TS)
        b = osrc.capture_owner_message(self.d, b"y", TS)
        self.assertEqual((a["source_id"], b["source_id"]), ("OS-0001", "OS-0002"))

    def test_tamper_detected(self):
        osrc.capture_owner_message(self.d, b"original", TS, source_id="T1")
        with open(os.path.join(self.d, "T1.txt"), "wb") as f:
            f.write(b"0riginal")
        self.assertTrue(osrc.verify_record(self.d, "T1"))

    def test_duplicate_id_refused_original_unchanged(self):
        osrc.capture_owner_message(self.d, b"first", TS, source_id="D1")
        with self.assertRaises(FileExistsError):
            osrc.capture_owner_message(self.d, b"second", TS, source_id="D1")
        with open(os.path.join(self.d, "D1.txt"), "rb") as f:
            self.assertEqual(f.read(), b"first")
        self.assertEqual(osrc.verify_record(self.d, "D1"), [])

    def test_bad_inputs_rejected(self):
        for kw in ({"raw_bytes": "text"}, {"received_at": "2026-11-27T10:00:00"}, {"source_id": "../x"}, {"source_id": "a.b"}):
            args = dict(raw_bytes=b"x", received_at=TS)
            args.update(kw)
            with self.subTest(kw), self.assertRaises(ValueError):
                osrc.capture_owner_message(self.d, **args)

    def test_response_is_separate_source(self):
        q = osrc.capture_owner_message(self.d, b"question", TS)
        r = osrc.capture_owner_message(self.d, b"answer", TS)
        self.assertNotEqual(q["source_id"], r["source_id"])

    def test_interpretation_cannot_overwrite_source(self):
        osrc.capture_owner_message(self.d, b"owner words", TS, source_id="I1")
        interp = {"interpretation_id": "I1", "source_id": "I1", "text": "summary", "author_role": "planner"}
        osrc.write_interpretation(self.d, interp)
        with open(os.path.join(self.d, "I1.txt"), "rb") as f:
            self.assertEqual(f.read(), b"owner words")
        self.assertEqual(osrc.verify_record(self.d, "I1"), [])
        with self.assertRaises(FileExistsError):
            osrc.write_interpretation(self.d, interp)
        for bad in ({"interpretation_id": "I1.txt"}, {"source_id": "nope"}, {"author_role": "manager"}):
            with self.subTest(bad), self.assertRaises(ValueError):
                osrc.write_interpretation(self.d, dict(interp, **bad))


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.p = strict_load(os.path.join(FX, "valid-owner-controlled.json"))

    def test_valid_fixtures(self):
        for n in os.listdir(FX):
            if n.startswith("valid-"):
                self.assertEqual(osrc.validate_question_packet(strict_load(os.path.join(FX, n))), [], n)

    def test_invalid_fixtures(self):
        for n in os.listdir(FX):
            if n.startswith("invalid-"):
                self.assertTrue(osrc.validate_question_packet(strict_load(os.path.join(FX, n))), n)

    def test_cli(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for n, code in (("valid-cheap-default.json", 0), ("invalid-approved.json", 2)):
            r = subprocess.run([sys.executable, os.path.join(PKG, "owner_source.py"), os.path.join(FX, n)],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, code, n)
            self.assertEqual(json.loads(r.stdout)["valid"], code == 0)

    def test_outbound(self):
        t = self.p["exact_text"]
        self.assertEqual(osrc.check_outbound(self.p, t), [])
        for name, out in (("one char", t.replace("format", "formaT")), ("trailing newline", t + "\n"),
                          ("crlf vs lf", t.replace("\r\n", "\n")), ("nfc", "Which storage format should we use?")):
            with self.subTest(name):
                self.assertTrue(osrc.check_outbound(self.p, out))
        self.assertTrue(osrc.check_outbound(self.p, None))

    def test_permitted_default_rules(self):
        for rev in osrc.REVERSIBILITY:
            p = dict(self.p, reversibility=rev, permitted_default="x")
            self.assertEqual(osrc.validate_question_packet(p) == [], rev == "cheap_reversible", rev)

    def test_each_field_missing(self):
        for k in osrc.PACKET_FIELDS:
            with self.subTest(k):
                p = copy.deepcopy(self.p)
                del p[k]
                self.assertTrue(osrc.validate_question_packet(p))

    def test_unknown_reversibility_and_approval_flags(self):
        self.assertTrue(osrc.validate_question_packet(dict(self.p, reversibility="whatever")))
        for k in ("approved", "default_applied"):
            self.assertTrue(osrc.validate_question_packet(dict(self.p, **{k: True})), k)


if __name__ == "__main__":
    unittest.main()
