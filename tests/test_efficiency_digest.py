import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/skills/council-flow/scripts/efficiency"))
import digest as module
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
            self.assertIn("DIGEST_INCOMPLETE",digest["flags"])

    def test_malformed_json_and_utf8_are_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            digest=build_digest(b'{"broken":\xff}',b"",exit_code=0,command=["fixture"],artifact_dir=d,run_id="three")
            self.assertIn("MALFORMED_UTF8",digest["flags"])
            self.assertIn("DIGEST_INCOMPLETE",digest["flags"])

    def test_timeout_partial_output_and_missing_or_corrupt_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            result=capture([sys.executable,"-c","import sys,time; print('partial',flush=True); time.sleep(30)"],artifact_dir=d,timeout=2)
            self.assertTrue(result["timed_out"])
            self.assertIn("TIMED_OUT",result["flags"])
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])
            self.assertIsInstance(result["exit_code"],int)
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
    def test_artifact_symlink_is_rejected_when_available(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"target"; target.write_bytes(b"original")
            try: (Path(d)/"four.stdout.bin").symlink_to(target)
            except OSError as exc: self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(ValueError): build_digest(b"new",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="four")
            self.assertEqual(target.read_bytes(),b"original")

    def test_summaries_are_bounded_and_incomplete_when_truncated(self):
        with tempfile.TemporaryDirectory() as d:
            body=("ERROR: "+"x"*5000+"\n")*30
            result=build_digest(body.encode(),b"",exit_code=1,command=["fixture"],artifact_dir=d,limit=128)
            view=result["streams"]["stdout"]
            self.assertLessEqual(len(view["excerpt"]),128)
            self.assertLessEqual(sum(map(len,view["important_lines"])),128)
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])
            self.assertEqual(expand(result,"stdout"),body)

    def test_binary_expansion_and_hashes_are_exact(self):
        with tempfile.TemporaryDirectory() as d:
            out=b"\x00\xff\r\n\x1b[31mERROR\x1b[0m\n"; err=b"stderr\r\n\x80"
            result=build_digest(out,err,exit_code=3,command=["fixture"],artifact_dir=d)
            for name,data in (("stdout",out),("stderr",err)):
                self.assertEqual(result["streams"][name]["sha256"],hashlib.sha256(data).hexdigest())
                self.assertEqual(module.expand_bytes(result,name),data)
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])

    def test_cli_preserves_exit_and_original_expanded_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"digest.json"
            command=[sys.executable,"-c","import os; os.write(1,b'\\xff\\r\\n'); os.write(2,b'error\\r\\n'); raise SystemExit(7)"]
            proc=subprocess.run([sys.executable,module.__file__,"run","--artifacts",d,"--digest-output",str(path),"--",*command],capture_output=True)
            self.assertEqual(proc.returncode,7,proc.stderr)
            for stream,data in (("stdout",b"\xff\r\n"),("stderr",b"error\r\n")):
                expanded=subprocess.run([sys.executable,module.__file__,"expand",str(path),stream],capture_output=True)
                self.assertEqual(expanded.returncode,0,expanded.stderr)
                self.assertEqual(expanded.stdout,data)

    def test_ansi_and_crlf_only_normalize_the_summary(self):
        with tempfile.TemporaryDirectory() as d:
            data=b"\x1b[31mERROR\x1b[0m\r\nwarning\rnext\n"
            result=build_digest(data,b"",exit_code=1,command=["x"],artifact_dir=d)
            self.assertEqual(result["streams"]["stdout"]["excerpt"],"ERROR\nwarning\nnext\n")
            self.assertEqual((Path(d)/result["streams"]["stdout"]["artifact"]).read_bytes(),data)

    def test_invalid_utf8_without_json_is_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            result=build_digest(b"plain \xff",b"",exit_code=0,command=["x"],artifact_dir=d)
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])

    def test_failure_ids_and_stderr_blind_spot_are_recoverable(self):
        with tempfile.TemporaryDirectory() as d:
            data=(b"ordinary\n"*100+b"FAIL: test_total (fixture.Tests.test_total)\nFAILED test_fixture.py::test_other - root cause\n"+b"tail\n"*100)
            result=build_digest(b"",data,exit_code=1,command=["x"],artifact_dir=d,limit=128)
            stream=result["streams"]["stderr"]
            self.assertNotIn("root cause",stream["excerpt"])
            self.assertEqual(stream["failing_test_ids"],["test_total (fixture.Tests.test_total)","test_fixture.py::test_other"])
            self.assertIn(b"root cause",module.expand_bytes(result,"stderr"))
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])

    def test_parse_failure_is_incomplete_but_valid_replacement_character_is_not(self):
        with tempfile.TemporaryDirectory() as d:
            bad=build_digest(b'{"broken":',b"",exit_code=0,command=["x"],artifact_dir=d)
            self.assertTrue(bad["streams"]["stdout"]["parse_errors"])
            self.assertIn("DIGEST_INCOMPLETE",bad["flags"])
            valid=build_digest('\ufffd'.encode(),b"",exit_code=0,command=["x"],artifact_dir=d)
            self.assertFalse(valid["streams"]["stdout"]["malformed_utf8"])

    def test_existing_artifacts_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            result=build_digest(b"original",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="same")
            with self.assertRaises((ValueError,FileExistsError)):
                build_digest(b"replacement",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="same")
            self.assertEqual(expand(result,"stdout"),"original")

    def test_traversal_variants_and_invalid_run_id(self):
        with tempfile.TemporaryDirectory() as d:
            result=build_digest(b"x",b"",exit_code=0,command=["x"],artifact_dir=d)
            for name in ("../escape","..\\escape","/absolute","C:\\escape","file:stream",".",".."):
                with self.subTest(name=name):
                    result["streams"]["stdout"]["artifact"]=name
                    with self.assertRaises(ValueError): expand(result,"stdout")
            with self.assertRaises(ValueError):
                build_digest(b"x",b"",exit_code=0,command=["x"],artifact_dir=d,run_id="../escape")

    def test_linked_artifact_directory_is_rejected_when_available(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"outside"; target.mkdir(); link=Path(d)/"linked"
            try: link.symlink_to(target,target_is_directory=True)
            except OSError as exc: self.skipTest(f"directory symlink unavailable: {exc}")
            with self.assertRaises(ValueError): build_digest(b"x",b"",exit_code=0,command=["x"],artifact_dir=link)
            self.assertEqual(list(target.iterdir()),[])

    @unittest.skipUnless(os.name=="nt","Windows junction check")
    def test_windows_junction_directory_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"outside"; target.mkdir(); link=Path(d)/"linked"
            proc=subprocess.run(["cmd","/c","mklink","/J",str(link),str(target)],capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            with self.assertRaises(ValueError): build_digest(b"x",b"",exit_code=0,command=["x"],artifact_dir=link)
            self.assertEqual(list(target.iterdir()),[])
            result=build_digest(b"x",b"",exit_code=0,command=["x"],artifact_dir=target)
            result["artifact_dir"]=str(link)
            with self.assertRaises(ValueError): expand(result,"stdout")

    def test_summary_is_deterministic_and_full_oversized_output_is_retained(self):
        with tempfile.TemporaryDirectory() as d:
            data=b"ordinary\n"*100000+b"ERROR late root cause\r\n"
            first=build_digest(data,b"stderr",exit_code=9,command=["x"],artifact_dir=Path(d)/"a",run_id="same",limit=129)
            second=build_digest(data,b"stderr",exit_code=9,command=["x"],artifact_dir=Path(d)/"b",run_id="same",limit=129)
            self.assertEqual(first["streams"],second["streams"])
            self.assertEqual(module.expand_bytes(first,"stdout"),data)
            self.assertLessEqual(len(first["streams"]["stdout"]["excerpt"]),129)
            self.assertIn("DIGEST_INCOMPLETE",first["flags"])

    def test_invalid_options_are_rejected_before_running_command(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/"side-effect"
            command=[sys.executable,"-c",f"from pathlib import Path; Path({str(marker)!r}).touch()"]
            for options in ({"limit":0},{"limit":True},{"timeout":-1},{"timeout":float('nan')},{"timeout":float('inf')}):
                with self.subTest(options=options):
                    with self.assertRaises(ValueError): capture(command,artifact_dir=d,**options)
                    self.assertFalse(marker.exists())

    def test_timeout_cli_reports_124_and_retains_observed_termination_code(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"digest.json"
            proc=subprocess.run([sys.executable,module.__file__,"run","--artifacts",d,"--digest-output",str(path),"--timeout","0.05","--",sys.executable,"-c","import time; time.sleep(30)"],capture_output=True,timeout=10)
            self.assertEqual(proc.returncode,124,proc.stderr)
            result=json.loads(path.read_text())
            self.assertTrue(result["timed_out"])
            self.assertIsInstance(result["exit_code"],int)
            self.assertIn("DIGEST_INCOMPLETE",result["flags"])

    def test_existing_digest_file_is_refused_before_command_runs(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"digest.json"; path.write_text("original")
            marker=Path(d)/"side-effect"
            proc=subprocess.run([sys.executable,module.__file__,"run","--artifacts",d,"--digest-output",str(path),"--",sys.executable,"-c",f"from pathlib import Path; Path({str(marker)!r}).touch()"],capture_output=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(path.read_text(),"original")
            self.assertFalse(marker.exists())

    @unittest.skipIf(os.name=="nt","POSIX signal termination")
    def test_cli_preserves_signal_termination(self):
        import signal
        with tempfile.TemporaryDirectory() as d:
            proc=subprocess.run([sys.executable,module.__file__,"run","--artifacts",d,"--digest-output",str(Path(d)/"digest.json"),"--",sys.executable,"-c","import os,signal; os.kill(os.getpid(),signal.SIGTERM)"],capture_output=True)
            self.assertEqual(proc.returncode,-signal.SIGTERM)

if __name__=="__main__": unittest.main()
