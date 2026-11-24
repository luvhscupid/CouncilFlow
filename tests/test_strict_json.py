"""Shared strict JSON reader and the Plan contract's plan-file checks."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/council-flow/scripts"
sys.path.insert(0, str(SCRIPTS))

import contracts  # noqa: E402
import doctor  # noqa: E402
import planner_contract  # noqa: E402
import strict_json  # noqa: E402


def plan_file():
    return {"plan_id": "P1", "plan_revision": 1, "project_note": "metadata stays project-owned",
            "acceptance": [{"id": "AC1", "criterion": "Keep\r\nbehavior."}, {"id": "AC2"}]}


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_constants_fail_closed(self):
        for raw, code in (('{"a":1,"a":2}', "duplicate_key"), (b'{"a":{"b":1,"b":1}}', "duplicate_key"),
                          ('{"a":NaN}', "nonfinite"), ('[Infinity]', "nonfinite"),
                          ('{"a":-Infinity}', "nonfinite")):
            with self.subTest(raw=raw), self.assertRaises(strict_json.ContractError) as failure:
                strict_json.loads(raw, field="plan")
            self.assertEqual((failure.exception.code, failure.exception.field), (code, "plan"))
            self.assertIsInstance(failure.exception, ValueError)

    def test_valid_and_malformed_json(self):
        self.assertEqual(strict_json.loads('{"a":[1,2.5,"x"]}'), {"a": [1, 2.5, "x"]})
        with self.assertRaises(ValueError):
            strict_json.loads('{"a":')

    def test_every_contract_raises_one_error_type(self):
        self.assertIs(contracts.ContractError, strict_json.ContractError)
        self.assertIs(planner_contract.ContractError, strict_json.ContractError)

    def test_text_identity_and_criterion_fields(self):
        self.assertEqual(strict_json.identity("AC1", "id"), "AC1")
        self.assertEqual(strict_json.criterion("a\tb\r\nc", "c"), "a\tb\r\nc")
        for call, value in ((strict_json.text, "a\nb"), (strict_json.identity, "x" * 129),
                            (strict_json.criterion, "a\rb"), (strict_json.text, " "),
                            (strict_json.criterion, 7)):
            with self.subTest(call=call.__name__, value=value), self.assertRaises(strict_json.ContractError):
                call(value, "field")

    def test_scripts_reject_duplicate_keys_through_the_shared_reader(self):
        with self.assertRaises(ValueError):
            doctor.load_evidence('{"schema_version":1,"schema_version":2}')
        with self.assertRaises(contracts.ContractError) as failure:
            contracts.loads('{"x":1,"x":2}')
        self.assertEqual(failure.exception.code, "duplicate_key")
        with self.assertRaises(planner_contract.ContractError) as failure:
            planner_contract.validate_plan_bytes(b'{"plan_id":"P","plan_id":"Q"}', [])
        self.assertEqual((failure.exception.code, failure.exception.field), ("duplicate_key", "plan"))
        for adapter in ("codex_adapter.py", "claude_adapter.py"):
            run = subprocess.run([sys.executable, "-c",
                                  "import importlib.util,sys;"
                                  "s=importlib.util.spec_from_file_location('a',sys.argv[1]);"
                                  "m=importlib.util.module_from_spec(s);"
                                  "sys.path.insert(0,sys.argv[2]);s.loader.exec_module(m);"
                                  "print(m.strict_loads.__module__)",
                                  str(SCRIPTS / "efficiency" / adapter), str(SCRIPTS / "efficiency")],
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.strip(), "strict_json")


class PlanContextTests(unittest.TestCase):
    def check(self, plan, **overrides):
        options = {"plan_id": "P1", "plan_revision": 1, "acceptance_ids": ["AC1", "AC2"]}
        options.update(overrides)
        return planner_contract.validate_plan_context(plan, **options)

    def expect(self, code, field, plan, **overrides):
        with self.assertRaises(planner_contract.ContractError) as failure:
            self.check(plan, **overrides)
        self.assertEqual((failure.exception.code, failure.exception.field), (code, field))

    def test_accepts_project_owned_metadata_and_optional_criterion(self):
        self.assertIsNone(self.check(plan_file()))

    def test_identity_revision_and_acceptance_rules(self):
        self.expect("plan_artifact", "payload.plan_ref", [])
        self.expect("plan_artifact", "payload.plan_ref", plan_file(), plan_id="P2")
        self.expect("plan_artifact", "payload.plan_ref", plan_file(), plan_revision=2)
        for revision in (True, 0, 2147483648, "1"):
            with self.subTest(revision=revision):
                self.expect("plan_artifact", "plan.plan_revision", {**plan_file(), "plan_revision": revision})
        self.expect("string", "plan.plan_id", {**plan_file(), "plan_id": ""})
        self.expect("plan_artifact", "plan.acceptance", {**plan_file(), "acceptance": []})
        self.expect("plan_artifact", "plan.acceptance", {**plan_file(), "acceptance": ["AC1"]})
        self.expect("plan_artifact", "plan.acceptance",
                    {**plan_file(), "acceptance": [{"id": "AC1"}, {"id": "AC1"}]}, acceptance_ids=["AC1", "AC1"])
        self.expect("plan_artifact", "payload.acceptance_ids", plan_file(), acceptance_ids=["AC2", "AC1"])
        self.expect("control", "plan.acceptance.criterion",
                    {**plan_file(), "acceptance": [{"id": "AC1", "criterion": "a\rb"}, {"id": "AC2"}]})

    def test_fidelity_to_pinned_criteria_and_source(self):
        full = {**plan_file(), "acceptance": [{"id": "AC1", "criterion": "One"}, {"id": "AC2", "criterion": "Two"}]}
        pinned = [("AC1", "One"), ("AC2", "Two")]
        self.assertIsNone(self.check(full, expected_criteria=pinned))
        self.expect("acceptance_fidelity", "plan.acceptance", full, expected_criteria=pinned[:1])
        self.expect("acceptance_fidelity", "plan.acceptance", full, expected_criteria=[("AC1", "One"), ("AC2", "Two ")])
        # A count mismatch is reported before a missing criterion text.
        self.expect("acceptance_fidelity", "plan.acceptance", plan_file(), expected_criteria=pinned[:1])
        self.expect("string", "plan.acceptance.criterion", plan_file(), expected_criteria=pinned)
        source = {"artifact_id": "S1", "path": "source.txt", "sha256": "0" * 64, "kind": "owner-original-source"}
        self.expect("criteria_source", "plan.original_source_ref", full, original_source_ref=source)
        self.assertIsNone(self.check({**full, "original_source_ref": source}, original_source_ref=source))


if __name__ == "__main__":
    unittest.main()
