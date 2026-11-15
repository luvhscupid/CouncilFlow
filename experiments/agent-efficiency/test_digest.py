import json
import sys
import tempfile
import unittest
from pathlib import Path
from digest import build_digest, capture, expand

class DigestTests(unittest.TestCase):
    def test_preserves_exact_code_full_streams_and_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            digest=build_digest(b"ok\r\n",b"warning: fixture\r\n",exit_code=7,command=["fixture"],artifact_dir=d,run_id="one")
            self.assertEqual(digest["exit_code"],7)
            self.assertEqual(expand(digest,"stdout"),"ok\r\n")
            self.assertIn("COMMAND_FAILED",digest["flags"])

    def test_failure_detail_outside_excerpt_is_recoverable_and_blind_spot_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            detail="ROOT_CAUSE_SECRET_TEST_MARKER"
            body=("ordinary line\n"*100)+"ERROR: "+detail+"\n"+("tail\n"*100)
            digest=build_digest(body.encode(),b"",exit_code=1,command=["fixture"],artifact_dir=d,run_id="two",limit=128)
            self.assertTrue(digest["streams"]["stdout"]["summary_truncated"])
            self.assertNotIn(detail,digest["streams"]["stdout"]["excerpt"])
            self.assertIn(detail,expand(digest,"stdout"))
            self.assertTrue(digest["streams"]["stdout"]["important_lines"])

    def test_malformed_json_and_utf8_are_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            digest=build_digest(b'{"broken":\xff}',b"",exit_code=0,command=["fixture"],artifact_dir=d,run_id="three")
            self.assertIn("MALFORMED_UTF8",digest["flags"])
            self.assertIn("DIGEST_INCOMPLETE",digest["flags"])

    def test_timeout_partial_output_and_missing_or_corrupt_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            result=capture([sys.executable,"-c","import sys,time; print('partial',flush=True); time.sleep(2)"],artifact_dir=d,timeout=.05)
            self.assertTrue(result["timed_out"])
            self.assertIn("TIMED_OUT",result["flags"])
            self.assertIn("partial",expand(result,"stdout"))
            p=Path(d)/result["streams"]["stdout"]["artifact"]; p.unlink()
            with self.assertRaises(FileNotFoundError): expand(result,"stdout")

    def test_integrity_failure_path_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            result=build_digest(b"data",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="four")
            (Path(d)/result["streams"]["stdout"]["artifact"]).write_bytes(b"altered")
            with self.assertRaises(ValueError): expand(result,"stdout")
            bad=json.loads(json.dumps(result)); bad["streams"]["stderr"]["artifact"]="../escape"
            with self.assertRaises(ValueError): expand(bad,"stderr")
            (Path(d)/"four.stdout.bin").unlink(); (Path(d)/"four.stdout.bin").symlink_to(Path(d)/"four.stderr.bin")
            with self.assertRaises(ValueError): build_digest(b"new",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="four")

if __name__=="__main__": unittest.main()
