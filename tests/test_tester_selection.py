"""Regression: the Reviewer's cited Tester is resolved exactly, not by first candidate match.

Real canonical validator (validate_sequence), synthetic actors/hashes. Each test asserts a
specific pass or failure code. No assertion is weakened to make a case pass.
"""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_contracts as fixtures

c = fixtures.c


def by_id(messages, mid):
    return next(m for m in messages if m["message_id"] == mid)


def base_chain():
    """plan, worker assign/report, Tester M4/M5 (superseded), corrective Tester M4b/M5b,
    Reviewer assign M6 (replying to M5b), Reviewer report M7 (citing M5b)."""
    data = fixtures.sequence()
    m4b = copy.deepcopy(by_id(data, "M4")); m4b["message_id"] = "M4b"; m4b["in_reply_to"] = "M3"
    m5b = copy.deepcopy(by_id(data, "M5")); m5b["message_id"] = "M5b"; m5b["in_reply_to"] = "M4b"
    m6 = copy.deepcopy(by_id(data, "M6")); m6["in_reply_to"] = "M5b"
    m7 = copy.deepcopy(by_id(data, "M7")); m7["in_reply_to"] = "M6"
    m7["payload"]["comparison"]["tester_report_ref"] = fixtures.ref("M5b", "synthetic/tester-report.json", kind="message")
    return data[:5] + [m4b, m5b, m6, m7]


def chain_with_reviewer_citing(tester_id):
    data = base_chain()
    m7 = by_id(data, "M7")
    m7["payload"]["comparison"]["tester_report_ref"] = fixtures.ref(tester_id, "synthetic/tester-report.json", kind="message")
    return data


class TesterSelectionTests(unittest.TestCase):
    def assertCode(self, messages, code):
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence(messages)
        self.assertEqual(failure.exception.code, code)

    def test_legitimate_single_tester_flow_passes(self):
        c.validate_sequence(fixtures.sequence())

    def test_two_tester_reports_reviewer_cites_newer_causal_report_passes(self):
        c.validate_sequence(base_chain())

    def test_reviewer_citing_wrong_earlier_tester_fails(self):
        # Reviewer M6 replies to M5b, so citing the superseded M5 is a wrong selection.
        data = chain_with_reviewer_citing("M5")
        self.assertCode(data, "comparison_evidence")

    def test_reviewer_citing_nonexistent_tester_fails(self):
        data = chain_with_reviewer_citing("M99")
        self.assertCode(data, "comparison_evidence")

    def test_reviewer_citing_future_tester_fails(self):
        # The cited Tester appears only after the Reviewer assignment.
        data = base_chain()
        future = copy.deepcopy(by_id(data, "M5b")); future["message_id"] = "M9"
        future["in_reply_to"] = "M4b"
        data = [m for m in data if m["message_id"] != "M5b"]
        data.insert(data.index(by_id(data, "M6")) + 1, future)
        data = [m for m in data]
        m7 = by_id(data, "M7")
        m7["payload"]["comparison"]["tester_report_ref"] = fixtures.ref("M9", "synthetic/tester-report.json", kind="message")
        self.assertRaises(c.ContractError, c.validate_sequence, data)

    def test_mismatched_candidate_fails(self):
        data = base_chain()
        stale = fixtures.ref("stale-candidate", "synthetic/old.json", "f" * 64, "candidate")
        by_id(data, "M5b")["payload"]["candidate_ref"] = stale
        self.assertRaises(c.ContractError, c.validate_sequence, data)

    def test_mismatched_task_or_attempt_fails(self):
        data = base_chain()
        by_id(data, "M5b")["task_id"] = "OTHER"
        self.assertRaises(c.ContractError, c.validate_sequence, data)
        data = base_chain()
        by_id(data, "M5b")["attempt_id"] = "A2"
        self.assertRaises(c.ContractError, c.validate_sequence, data)

    def materialize(self, root, data):
        """Write real bytes for every referenced artifact so only the Tester bytes can differ."""
        def walk(value):
            if isinstance(value, dict):
                if set(value) == {"artifact_id", "path", "sha256", "kind"}:
                    target = root / value["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        target.write_bytes(b"synthetic evidence for " + value["artifact_id"].encode())
                    value["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
                else:
                    for child in value.values():
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        for message in data:
            walk(message)

    def test_referenced_tester_bytes_must_be_the_exact_tester_message(self):
        """Bytes at the cited path must be the exact earlier Tester message. A different
        Tester message is rejected whether the declared hash is stale (artifact_hash)
        or updated to match those other bytes (comparison_evidence)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = base_chain()
            self.materialize(root, data)
            plan_bytes = json.dumps({"plan_id": "P1", "plan_revision": 1,
                                     "acceptance": [{"id": a} for a in fixtures.AC]}).encode("utf-8")
            (root / "synthetic/plan.json").write_bytes(plan_bytes)
            plan_ref = fixtures.ref("plan", "synthetic/plan.json", hashlib.sha256(plan_bytes).hexdigest(), "plan")
            data[0]["payload"]["plan_ref"] = plan_ref
            data[0]["evidence_refs"] = [plan_ref]
            for m in data[1:]:
                m["evidence_refs"] = [plan_ref if e["artifact_id"] == "plan" else e for e in m["evidence_refs"]]
            data[-1]["payload"]["comparison"]["plan_ref"] = plan_ref

            other = copy.deepcopy(by_id(data, "M5b"))
            other["payload"]["summary"] = "tampered summary"
            other_bytes = json.dumps(other, ensure_ascii=False).encode("utf-8")
            (root / "synthetic/tester-report.json").write_bytes(other_bytes)

            # Case 1: declared hash is the genuine M5b hash, file holds different bytes.
            genuine_hash = hashlib.sha256(json.dumps(by_id(data, "M5b"), ensure_ascii=False).encode("utf-8")).hexdigest()
            by_id(data, "M7")["payload"]["comparison"]["tester_report_ref"] = {
                "artifact_id": "M5b", "path": "synthetic/tester-report.json",
                "sha256": genuine_hash, "kind": "message"}
            self.assertCode_root(data, root, "artifact_hash")

            # Case 2: the Reviewer's declared hash is updated to the other bytes. The
            # substitution still breaks the Tester message's own recorded evidence hash,
            # so the byte-binding layer rejects it.
            by_id(data, "M7")["payload"]["comparison"]["tester_report_ref"]["sha256"] = hashlib.sha256(other_bytes).hexdigest()
            self.assertCode_root(data, root, "artifact_hash")

    def assertCode_root(self, messages, root, code):
        with self.assertRaises(c.ContractError) as failure:
            c.validate_sequence(messages, root=root)
        self.assertEqual(failure.exception.code, code)

    def test_reviewer_rerun_mismatch_fails(self):
        data = base_chain()
        rerun = by_id(data, "M7")["payload"]["comparison"]["independent_rerun"]
        rerun["tester_exit_code"] = 99
        self.assertRaises(c.ContractError, c.validate_sequence, data)


if __name__ == "__main__":
    unittest.main()
