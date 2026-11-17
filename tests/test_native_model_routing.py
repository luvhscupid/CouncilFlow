"""Offline synthetic checks; these do not establish live routing behavior."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/native-model-routing"))
sys.path.insert(0, str(ROOT / "experiments/skilllab-integration"))
import routing
from adapter import suggest

IDENTITY = {"provider": "example", "route_id": "route-1", "model_id": "model-1", "harness": "codex-child"}


def policy_fixture():
    return {
        "owner_approved": True,
        "approved_providers": ["example"],
        "roles": {"worker": {"enabled": True, "task_ids": ["task-1"],
                               "reasoning_efforts": ["low"], "required_capabilities": ["text"]}},
        "routes": [{"identity": IDENTITY.copy(), "availability": "available",
                    "available_route_ids": ["route-1"], "usage_restrictions": [],
                    "qualification": {"status": "verified", "valid_until": "2099-12-31",
                                      "evidence_ref": {"artifact_id": "qual-1", "path": "evidence/qual.json",
                                                        "kind": "qualification", "sha256": "a" * 64},
                                      "capabilities": ["text"], "reasoning_efforts": ["low"]}}],
        "limits": {"tokens": 100},
    }


def authorize(policy=None, **kwargs):
    return routing.authorize_request(policy if policy is not None else policy_fixture(),
                                     role=kwargs.pop("role", "worker"), task_id=kwargs.pop("task_id", "task-1"),
                                     requested=kwargs.pop("requested", IDENTITY),
                                     reasoning_effort=kwargs.pop("reasoning_effort", "low"),
                                     as_of=kwargs.pop("as_of", "2026-11-17"),
                                     resource_request=kwargs.pop("resource_request", {"tokens": 10}), **kwargs)


class RoutingContractTests(unittest.TestCase):
    def test_exact_identity_qualifies_and_returns_rationale(self):
        result = authorize()
        self.assertTrue(result["eligible"])
        self.assertEqual(result["selected"], IDENTITY)
        self.assertTrue(result["rationale"])

    def test_empty_or_unapproved_policy_fails_closed(self):
        self.assertEqual(authorize({})["reason_code"], "POLICY_NOT_OWNER_APPROVED")
        policy = policy_fixture(); policy["owner_approved"] = False
        self.assertFalse(authorize(policy)["eligible"])

    def test_exact_route_identity_includes_provider_route_model_harness(self):
        for field in IDENTITY:
            requested = IDENTITY.copy(); requested[field] += "-different"
            self.assertEqual(authorize(requested=requested)["reason_code"], "ROUTE_NOT_APPROVED")

    def test_role_and_task_constraints(self):
        self.assertEqual(authorize(role="tester")["reason_code"], "ROLE_OR_TASK_UNAUTHORIZED")
        self.assertEqual(authorize(task_id="other")["reason_code"], "ROLE_OR_TASK_UNAUTHORIZED")

    def test_unsupported_reasoning_effort_denied(self):
        self.assertEqual(authorize(reasoning_effort="high")["reason_code"], "UNSUPPORTED_REASONING_EFFORT")

    def test_missing_and_invalid_credentials_are_not_echoed(self):
        for state in ("missing", "invalid", "unknown"):
            result = authorize(credentials=state)
            self.assertEqual(result["reason_code"], "CREDENTIAL_UNAVAILABLE")
            self.assertNotIn("secret", json.dumps(result).lower())

    def test_unverified_and_expired_qualification_denied(self):
        policy = policy_fixture(); policy["routes"][0]["qualification"]["status"] = "unverified"
        self.assertEqual(authorize(policy)["reason_code"], "QUALIFICATION_UNVERIFIED")
        policy = policy_fixture(); policy["routes"][0]["qualification"]["valid_until"] = "2020-01-01"
        self.assertEqual(authorize(policy)["reason_code"], "QUALIFICATION_EXPIRED")

    def test_missing_or_unhandled_usage_restrictions_deny(self):
        policy = policy_fixture(); del policy["routes"][0]["usage_restrictions"]
        self.assertEqual(authorize(policy)["reason_code"], "USAGE_RESTRICTION_UNSUPPORTED")
        policy = policy_fixture(); policy["routes"][0]["usage_restrictions"] = ["region-bound"]
        self.assertEqual(authorize(policy)["reason_code"], "USAGE_RESTRICTION_UNSUPPORTED")

    def test_fallback_and_escalation_require_explicit_approval(self):
        self.assertEqual(authorize(fallback_requested=True)["reason_code"], "UNAUTHORIZED_FALLBACK")
        self.assertEqual(authorize(escalation_requested=True)["reason_code"], "UNAUTHORIZED_ESCALATION")

    def test_resource_limit_missing_unknown_and_excess_rejected(self):
        for resources in ({}, {"tokens": 101}, {"tokens": "unknown"}):
            self.assertEqual(authorize(resource_request=resources)["reason_code"], "RESOURCE_LIMIT_EXCEEDED_OR_UNKNOWN")

    def test_exact_role_task_assignment_succeeds(self):
        self.assertTrue(authorize()["eligible"])

    def test_native_request_is_explicit_but_does_not_claim_dispatch(self):
        request = routing.native_child_request(IDENTITY, "low", supports_model=True)
        self.assertEqual(request["status"], "REQUEST_READY_NOT_DISPATCHED")
        self.assertEqual(request["native_arguments"], {"model": "model-1", "reasoning_effort": "low"})
        self.assertFalse(request["dispatch_attempted"])
        self.assertIsNone(request["effective_identity"])

    def test_unsupported_native_model_routing_fails_closed(self):
        result = routing.native_child_request(IDENTITY, "low", supports_model=False)
        self.assertEqual(result["status"], "UNSUPPORTED_NATIVE_MODEL_ROUTING")
        self.assertFalse(result["dispatch_attempted"])

    def test_parent_inheritance_and_host_reported_mismatch_denied(self):
        self.assertEqual(routing.validate_dispatch_observation(requested=IDENTITY, parent=IDENTITY,
                    host_reported=None, effective=None)["status"], "DENIED_PARENT_INHERITANCE_MISMATCH")
        wrong = {**IDENTITY, "model_id": "other"}
        self.assertEqual(routing.validate_dispatch_observation(requested=IDENTITY, parent=None,
                    host_reported=wrong, effective=None)["status"], "DENIED_HOST_IDENTITY_MISMATCH")

    def test_missing_effective_identity_remains_unverified(self):
        result = routing.validate_dispatch_observation(requested=IDENTITY, parent=None,
                    host_reported=None, effective=None)
        self.assertEqual(result["status"], "NATIVE_MODEL_ROUTING_UNVERIFIED")
        self.assertIsNone(result["effective_identity"])

    def test_effective_identity_mismatch_denied(self):
        wrong = {**IDENTITY, "harness": "different"}
        self.assertEqual(routing.validate_dispatch_observation(requested=IDENTITY, parent=None,
                    host_reported=IDENTITY, effective=wrong)["status"], "DENIED_EFFECTIVE_IDENTITY_MISMATCH")

    def test_execution_record_redacts_unknowns_and_tracks_resources(self):
        record = routing.execution_record(requested=IDENTITY, outcome="dispatch_failed", retry_count=1,
            resources={"tokens": {"value": None, "disposition": "reported"},
                       "price": {"value": "secret", "disposition": "estimated"},
                       "bad": {"value": 9, "disposition": "invented"}},
            isolation={"worker_context_separate": True, "tester_blind_to_worker_private_state": True, "os_enforced": False},
            rollback={"status": "not_attempted", "target": None})
        self.assertIsNone(record["effective_identity"])
        self.assertEqual(record["outcome"], "dispatch_failed")
        self.assertNotIn("bad", record["resources"])
        self.assertNotIn("credential", json.dumps(record).replace("credential_material", ""))
        self.assertFalse(record["isolation"]["os_enforced"])

    def test_dispatch_failure_retry_cancel_incomplete_and_rollback_are_descriptive(self):
        for outcome in ("dispatch_failed", "retrying", "cancelled", "incomplete"):
            record = routing.execution_record(requested=IDENTITY, outcome=outcome, retry_count=1,
                rollback={"status": "available", "target": "previous-approved-config"},
                isolation={"worker_context_separate": True, "tester_blind_to_worker_private_state": True, "os_enforced": False})
            self.assertEqual(record["outcome"], outcome)
            self.assertEqual(record["rollback"]["status"], "available")
            self.assertTrue(record["isolation"]["tester_blind_to_worker_private_state"])
            self.assertFalse(record["isolation"]["os_enforced"])

    def test_execution_record_drops_secret_like_and_malformed_metadata(self):
        secret = "token=do-not-store"
        record = routing.execution_record(
            policy_sha256="bad-digest", qualification_ref={"artifact_id": "q", "path": "../secret",
                "kind": "qualification", "sha256": "x" * 64, "token": secret},
            reasoning_effort=secret,
            resources={"tokens": {"value": secret, "disposition": "reported", "unit": "count"},
                       "cost_usd": {"value": 3, "disposition": "estimated", "unit": "secret"},
                       "input_tokens": {"value": {"token": secret}, "disposition": "reported", "unit": "count"},
                       "unknown_secret": {"value": secret, "disposition": "reported", "unit": secret}},
            rollback={"status": "completed", "target": secret, "token": secret},
            isolation={"worker_context_separate": True, "tester_blind_to_worker_private_state": True,
                       "os_enforced": False, "credential": secret})
        rendered = json.dumps(record)
        self.assertNotIn(secret, rendered)
        self.assertIsNone(record["policy_sha256"])
        self.assertIsNone(record["qualification_ref"])
        self.assertIsNone(record["reasoning_effort"])
        self.assertIsNone(record["resources"]["tokens"]["value"])
        self.assertIsNone(record["resources"]["cost_usd"]["value"])
        self.assertNotIn("unknown_secret", record["resources"])
        self.assertIsNone(record["isolation"]["worker_context_separate"])

    def test_execution_record_rejects_bool_and_nonfinite_resource_values(self):
        record = routing.execution_record(resources={
            "tokens": {"value": True, "disposition": "reported", "unit": "count"},
            "duration_ms": {"value": float("inf"), "disposition": "estimated", "unit": "milliseconds"}})
        self.assertIsNone(record["resources"]["tokens"]["value"])
        self.assertIsNone(record["resources"]["duration_ms"]["value"])

    def test_execution_record_rejects_secret_words_in_safe_shaped_metadata(self):
        ref = {"artifact_id": "token-do-not-store", "path": "evidence/qualification.json",
               "kind": "qualification", "sha256": "a" * 64}
        record = routing.execution_record(qualification_ref=ref,
                                          rollback={"status": "completed", "target": "token-do-not-store"})
        self.assertIsNone(record["qualification_ref"])
        self.assertIsNone(record["rollback"]["target"])

    def test_execution_record_rejects_injected_marker_in_refs_and_rollback_enum(self):
        marker = "S3CRET_PROBE_value"
        for field in ("artifact_id", "path"):
            with self.subTest(field=field):
                ref = {"artifact_id": "qual-1", "path": "evidence/qualification.json",
                       "kind": "qualification", "sha256": "a" * 64}
                ref[field] = marker if field == "artifact_id" else f"evidence/{marker}.json"
                record = routing.execution_record(qualification_ref=ref,
                    rollback={"status": "completed", "target": marker})
                rendered = json.dumps(record)
                self.assertNotIn(marker, rendered)
                self.assertIsNone(record["qualification_ref"])
                self.assertIsNone(record["rollback"]["target"])

    def test_execution_record_accepts_fixed_safe_refs_and_rollback_target(self):
        record = routing.execution_record(
            qualification_ref={"artifact_id": "qual-1", "path": "evidence/qual.json",
                               "kind": "qualification", "sha256": "a" * 64},
            rollback={"status": "available", "target": "previous-approved-config"})
        self.assertEqual(record["qualification_ref"]["artifact_id"], "qual-1")
        self.assertEqual(record["qualification_ref"]["path"], "evidence/qual.json")
        self.assertEqual(record["rollback"]["target"], "previous-approved-config")

    def test_execution_record_drops_secret_like_route_identity_fields(self):
        secret_identity = {**IDENTITY, "model_id": "token-secret"}
        record = routing.execution_record(configured=secret_identity, requested=IDENTITY,
                                          host_reported=secret_identity, effective=secret_identity)
        self.assertIsNone(record["configured_identity"])
        self.assertIsNone(record["host_reported_identity"])
        self.assertIsNone(record["effective_identity"])
        self.assertEqual(record["requested_identity"], IDENTITY)

    def test_execution_record_drops_obfuscated_marker_from_every_identity_slot(self):
        marker = "S3CRET_PROBE_value"
        for slot in ("configured", "requested", "host_reported", "effective"):
            for field in routing.IDENTITY_FIELDS:
                with self.subTest(slot=slot, field=field):
                    unsafe = {**IDENTITY, field: marker}
                    record = routing.execution_record(**{slot: unsafe})
                    self.assertNotIn(marker, json.dumps(record))
                    self.assertIsNone(record[f"{slot}_identity"])

    def test_execution_record_keeps_safe_lowercase_identity_labels(self):
        identity = {"provider": "openai", "route_id": "approved-route.v2",
                    "model_id": "gpt-6-luna", "harness": "codex-child"}
        record = routing.execution_record(configured=identity, requested=identity,
                                          host_reported=identity, effective=identity)
        for slot in ("configured", "requested", "host_reported", "effective"):
            self.assertEqual(record[f"{slot}_identity"], identity)


class SkillLabAdapterTests(unittest.TestCase):
    def test_role_authority_denial_and_unavailable(self):
        args = dict(repository=ROOT, role="worker", task="test", actions=[], tools=[], conditions=[], candidate_ids=[])
        self.assertEqual(suggest(**args)["status"], "denied")
        args["role"] = "manager"; args["unavailable"] = True
        self.assertEqual(suggest(**args)["status"], "unavailable")

    def test_seven_candidate_cap_and_manager_denial(self):
        args = dict(repository=ROOT, role="manager", task="test", actions=[], tools=[], conditions=[], candidate_ids=[str(x) for x in range(8)])
        self.assertEqual(suggest(**args)["status"], "denied")
        args["candidate_ids"] = []; args["denied"] = True
        self.assertEqual(suggest(**args)["status"], "denied")

    def test_real_cli_no_skill_and_activation_unverified(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="unrelated task token", actions=["delegate"], tools=[], conditions=[], candidate_ids=[])
        result = suggest(**args)
        self.assertEqual(result["status"], "no_skill")
        self.assertEqual(result["activated"], "unverified")
        self.assertFalse(result["adds_permissions"])
        self.assertFalse(result["mutates_skilllab"])

    def test_selected_candidate_is_only_a_suggestion_from_seven_allowlist(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="call chain architecture find callers", actions=[],
                    tools=["graph_search", "graph_trace", "graph_snippet", "graph_coverage"],
                    conditions=["exact_project_bound", "index_fresh", "coverage_checked"],
                    candidate_ids=["codebase-memory"])
        result = suggest(**args)
        self.assertEqual(result["status"], "suggested")
        self.assertEqual(result["selected"], "codebase-memory")
        self.assertEqual(result["activated"], "unverified")
        self.assertEqual(result["source_identity"]["commit"], "40b4239e14f3c711ec3d32bb7ef4bb0820abdc63")

    def test_selection_outside_seven_candidate_set_is_denied(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="call chain architecture find callers", actions=[],
                    tools=["graph_search", "graph_trace", "graph_snippet", "graph_coverage"],
                    conditions=["exact_project_bound", "index_fresh", "coverage_checked"], candidate_ids=[])
        self.assertEqual(suggest(**args)["status"], "denied")

    def test_malformed_request_and_cli_failures_fail_closed(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="task", actions=[], tools=[], conditions=[], candidate_ids=["codebase-memory"])
        bad = dict(args, actions={"token": "secret"})
        self.assertEqual(suggest(**bad)["status"], "denied")
        with mock.patch("adapter.subprocess.run", side_effect=OSError("secret path")):
            result = suggest(**args)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("secret", json.dumps(result))

    def test_cli_output_secret_is_never_forwarded(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="task", actions=[], tools=[], conditions=[], candidate_ids=[])
        response = mock.Mock(returncode=0, stdout='{"decisions":[],"selected":null,"reason":"token=secret"}', stderr="")
        git_ok = mock.Mock(returncode=0, stdout="40b4239e14f3c711ec3d32bb7ef4bb0820abdc63\n", stderr="")
        with mock.patch("adapter.subprocess.run", side_effect=[git_ok, response]):
            result = suggest(**args)
        self.assertEqual(result["status"], "no_skill")
        self.assertNotIn("secret", json.dumps(result))

    def test_modified_cli_bytes_are_denied_before_execution(self):
        args = dict(repository=r"E:\Saint\PROJECTS\CouncilFlow-SkillLab", role="manager",
                    task="task", actions=[], tools=[], conditions=[], candidate_ids=[])
        original = Path.read_bytes
        def tampered(path):
            if path.name == "skilllab.py":
                return original(path) + b"# modified"
            return original(path)
        with mock.patch("adapter.Path.read_bytes", side_effect=tampered), mock.patch("adapter.subprocess.run") as run:
            result = suggest(**args)
        self.assertIn(result["status"], {"denied", "unavailable"})
        run.assert_not_called()
        args["candidate_ids"] = ["unregistered"]
        self.assertEqual(suggest(**args)["status"], "denied")


class DocumentationTests(unittest.TestCase):
    def test_readme_relative_links_and_mermaid_fences(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
        for target in links:
            if target.startswith(("https://", "http://", "mailto:")) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            self.assertTrue((ROOT / target).exists(), f"broken README link: {target}")
        self.assertEqual(readme.count("```") % 2, 0)
        self.assertIn("```mermaid\nflowchart LR", readme)


if __name__ == "__main__":
    unittest.main()
