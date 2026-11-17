"""Deterministic, fail-closed model route qualification data contract.

The module never dispatches a provider request and cannot enforce its result.
"""
from __future__ import annotations

from datetime import date
import re
import math
from typing import Any

IDENTITY_FIELDS = ("provider", "route_id", "model_id", "harness")
RESOURCE_CLASSES = {"enforced", "estimated", "reported"}
RESOURCE_SCHEMA = {
    "tokens": ("count", int), "input_tokens": ("count", int),
    "output_tokens": ("count", int), "duration_ms": ("milliseconds", (int, float)),
    "cost_usd": ("USD", (int, float)),
}
_SAFE_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
_QUALIFICATION_FIELDS = {"artifact_id", "path", "kind", "sha256"}
_SENSITIVE_WORDS = re.compile(r"(?:token|secret|password|credential|authorization|api[_-]?key)", re.IGNORECASE)
_OBFUSCATED_SENSITIVE_WORDS = re.compile(r"(?:token|secret|password|credential|authorization|api-key)")
_SAFE_LABEL = re.compile(r"[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*")
_SAFE_ROLLBACK_TARGETS = {"previous-approved-config"}
_DENIED = {"eligible": False, "selected": None}


def _identity(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == set(IDENTITY_FIELDS)
        and all(isinstance(value[k], str) and value[k].strip() for k in IDENTITY_FIELDS)
    )


def _same_identity(left: Any, right: Any) -> bool:
    return _identity(left) and _identity(right) and all(left[k] == right[k] for k in IDENTITY_FIELDS)


def authorize_request(
    policy: dict[str, Any], *, role: str, task_id: str, requested: dict[str, Any],
    reasoning_effort: str, as_of: str, credentials: str = "not_required",
    resource_request: dict[str, Any] | None = None, fallback_requested: bool = False,
    escalation_requested: bool = False,
) -> dict[str, Any]:
    """Select only an exact, owner-approved, currently qualified route.

    `credentials` is a state enum only; secret values are neither accepted nor
    echoed. Caller attestations and this result are not authenticated.
    """
    denied = {**_DENIED, "role": role, "task_id": task_id, "rationale": [], "credential_state": credentials}
    if not isinstance(policy, dict) or policy.get("owner_approved") is not True:
        denied["reason_code"] = "POLICY_NOT_OWNER_APPROVED"
        denied["rationale"].append("No owner-approved route policy is present.")
        return denied
    if fallback_requested:
        denied["reason_code"] = "UNAUTHORIZED_FALLBACK"
        denied["rationale"].append("Fallback selection is not implemented; the request is denied without substitution.")
        return denied
    if escalation_requested:
        denied["reason_code"] = "UNAUTHORIZED_ESCALATION"
        denied["rationale"].append("Role/resource escalation is not implemented; the request is denied.")
        return denied
    roles = policy.get("roles", {})
    if role not in roles or not isinstance(task_id, str) or not task_id.strip():
        denied["reason_code"] = "ROLE_OR_TASK_UNAUTHORIZED"
        denied["rationale"].append("Role/task is not authorized by the policy.")
        return denied
    rule = roles[role]
    if not isinstance(rule, dict) or not rule.get("enabled") or task_id not in rule.get("task_ids", []):
        denied["reason_code"] = "ROLE_OR_TASK_UNAUTHORIZED"
        denied["rationale"].append("Role/task is not authorized by the policy.")
        return denied
    if not _identity(requested):
        denied["reason_code"] = "INVALID_ROUTE_IDENTITY"
        denied["rationale"].append("Exact provider, route, model, and harness identity is required.")
        return denied
    if not isinstance(reasoning_effort, str) or reasoning_effort not in rule.get("reasoning_efforts", []):
        denied["reason_code"] = "UNSUPPORTED_REASONING_EFFORT"
        denied["rationale"].append("Requested reasoning effort is not allowed for this role.")
        return denied
    if credentials not in {"not_required", "available", "missing", "invalid", "unknown"}:
        credentials = "unknown"
        denied["credential_state"] = credentials
    if credentials in {"missing", "invalid", "unknown"}:
        denied["reason_code"] = "CREDENTIAL_UNAVAILABLE"
        denied["rationale"].append("Required credential state is unavailable; no credential value was read or recorded.")
        return denied
    candidates = policy.get("routes", [])
    entry = next((item for item in candidates if isinstance(item, dict) and _same_identity(item.get("identity"), requested)), None)
    if entry is None:
        denied["reason_code"] = "ROUTE_NOT_APPROVED"
        denied["rationale"].append("No exact identity match exists in the approved route pool.")
        return denied
    qualification = entry.get("qualification", {})
    if qualification.get("status") != "verified":
        denied["reason_code"] = "QUALIFICATION_UNVERIFIED"
        denied["rationale"].append("Route qualification is not independently verified.")
        return denied
    evidence = qualification.get("evidence_ref")
    if (not isinstance(evidence, dict) or set(evidence) != {"artifact_id", "path", "kind", "sha256"}
            or not all(isinstance(evidence.get(key), str) and evidence[key] for key in evidence)
            or not re.fullmatch(r"[0-9a-f]{64}", evidence.get("sha256", ""))):
        denied["reason_code"] = "QUALIFICATION_EVIDENCE_MISSING"
        denied["rationale"].append("A verified qualification evidence reference is required.")
        return denied
    try:
        if date.fromisoformat(qualification["valid_until"]) < date.fromisoformat(as_of):
            denied["reason_code"] = "QUALIFICATION_EXPIRED"
            denied["rationale"].append("Qualification validity has expired.")
            return denied
    except (KeyError, TypeError, ValueError):
        denied["reason_code"] = "QUALIFICATION_VALIDITY_INVALID"
        denied["rationale"].append("Qualification validity must use an ISO date.")
        return denied
    if requested["provider"] not in policy.get("approved_providers", []):
        denied["reason_code"] = "PROVIDER_NOT_APPROVED"
        denied["rationale"].append("Provider is outside the explicitly approved pool.")
        return denied
    if requested["route_id"] not in entry.get("available_route_ids", []):
        denied["reason_code"] = "ROUTE_UNAVAILABLE"
        denied["rationale"].append("Route is not declared available for this request.")
        return denied
    if reasoning_effort not in qualification.get("reasoning_efforts", []):
        denied["reason_code"] = "UNQUALIFIED_REASONING_EFFORT"
        denied["rationale"].append("Qualification does not cover the requested reasoning effort.")
        return denied
    if not set(rule.get("required_capabilities", [])) <= set(qualification.get("capabilities", [])):
        denied["reason_code"] = "CAPABILITY_UNSUPPORTED"
        denied["rationale"].append("The qualified route lacks a required capability.")
        return denied
    limits = policy.get("limits", {})
    request = resource_request or {}
    for name, configured in limits.items():
        if name not in request or not isinstance(request[name], (int, float)) or request[name] < 0 or request[name] > configured:
            denied["reason_code"] = "RESOURCE_LIMIT_EXCEEDED_OR_UNKNOWN"
            denied["rationale"].append(f"Resource {name} is missing, invalid, or above its policy limit.")
            return denied
    if entry.get("availability") != "available":
        denied["reason_code"] = "ROUTE_UNAVAILABLE"
        denied["rationale"].append("Route availability is not confirmed.")
        return denied
    restrictions = entry.get("usage_restrictions")
    if not isinstance(restrictions, list) or restrictions:
        denied["reason_code"] = "USAGE_RESTRICTION_UNSUPPORTED"
        denied["rationale"].append("Usage restrictions are missing or cannot be evaluated safely.")
        return denied
    return {
        "eligible": True, "selected": requested.copy(), "role": role, "task_id": task_id,
        "reasoning_effort": reasoning_effort, "qualification_evidence_ref": evidence.copy(),
        "rationale": ["Exact approved identity and role/task constraints passed declared-data validation."],
        "disclaimer": "Validation result only; does not authenticate policy or authorize/enforce dispatch.",
    }


def native_child_request(identity: dict[str, Any], reasoning_effort: str, *, supports_model: bool) -> dict[str, Any]:
    """Prepare explicit native delegation arguments without dispatching."""
    if not _identity(identity):
        return {"status": "DENIED_INVALID_REQUEST", "requested_identity": None, "host_reported_identity": None, "effective_identity": None}
    if not supports_model:
        return {"status": "UNSUPPORTED_NATIVE_MODEL_ROUTING", "requested_identity": identity.copy(),
                "requested_model": identity["model_id"], "reasoning_effort": reasoning_effort,
                "host_reported_identity": None, "effective_identity": None,
                "dispatch_attempted": False}
    return {"status": "REQUEST_READY_NOT_DISPATCHED", "requested_identity": identity.copy(),
            "requested_model": identity["model_id"], "reasoning_effort": reasoning_effort,
            "host_reported_identity": None, "effective_identity": None,
            "dispatch_attempted": False,
            "native_arguments": {"model": identity["model_id"], "reasoning_effort": reasoning_effort}}


def validate_dispatch_observation(*, requested: dict[str, Any], parent: dict[str, Any] | None,
                                  host_reported: dict[str, Any] | None,
                                  effective: dict[str, Any] | None) -> dict[str, Any]:
    """Compare externally observed identities; missing observations stay unknown."""
    if not _identity(requested):
        return {"status": "DENIED_INVALID_REQUEST", "reason_code": "INVALID_ROUTE_IDENTITY"}
    if parent is not None and _same_identity(parent, requested):
        return {"status": "DENIED_PARENT_INHERITANCE_MISMATCH", "reason_code": "REQUEST_EQUALS_PARENT"}
    if host_reported is not None and not _same_identity(requested, host_reported):
        return {"status": "DENIED_HOST_IDENTITY_MISMATCH", "reason_code": "HOST_REPORTED_IDENTITY_MISMATCH"}
    if effective is not None and not _same_identity(requested, effective):
        return {"status": "DENIED_EFFECTIVE_IDENTITY_MISMATCH", "reason_code": "EFFECTIVE_IDENTITY_MISMATCH"}
    observed = host_reported is not None and effective is not None
    return {"status": "OBSERVED_MATCH" if observed else "NATIVE_MODEL_ROUTING_UNVERIFIED",
            "requested_identity": requested.copy(), "parent_identity": parent.copy() if _identity(parent) else None,
            "host_reported_identity": host_reported.copy() if _identity(host_reported) else None,
            "effective_identity": effective.copy() if _identity(effective) else None}


def execution_record(*, configured: dict[str, Any] | None = None, requested: dict[str, Any] | None = None,
                     host_reported: dict[str, Any] | None = None, effective: dict[str, Any] | None = None,
                     reasoning_effort: str | None = None, policy_sha256: str | None = None,
                     qualification_ref: dict[str, Any] | None = None,
                     resources: dict[str, dict[str, Any]] | None = None,
                     outcome: str = "incomplete", retry_count: int = 0,
                     rollback: dict[str, Any] | None = None,
                     isolation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a redacted, descriptive execution record; null means unknown."""
    def safe_ref(value: Any) -> dict[str, str] | None:
        if not isinstance(value, dict) or set(value) != _QUALIFICATION_FIELDS:
            return None
        if not all(isinstance(value.get(k), str) and value[k] and len(value[k]) <= 1024 for k in _QUALIFICATION_FIELDS):
            return None
        if not re.fullmatch(r"[0-9a-f]{64}", value["sha256"]):
            return None
        if (not _safe_label(value["artifact_id"])
                or value["kind"] != "qualification"):
            return None
        path = value["path"]
        parts = path.split("/")
        if (path.startswith("/") or "\\" in path
                or any(not _safe_label(part) for part in parts)):
            return None
        return {k: value[k] for k in ("artifact_id", "path", "kind", "sha256")}

    def _safe_label(value: str) -> bool:
        if not isinstance(value, str) or len(value) > 128 or not _SAFE_LABEL.fullmatch(value):
            return False
        normalized = value.translate(str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"}))
        return _OBFUSCATED_SENSITIVE_WORDS.search(normalized) is None

    def safe_identity(value: Any) -> dict[str, str] | None:
        if not _identity(value):
            return None
        # Execution records may persist only bounded, lowercase identifier
        # labels. This keeps arbitrary host/provider text out of evidence and
        # applies the same obfuscation check used for qualification metadata.
        if any(not _safe_label(value[k]) for k in IDENTITY_FIELDS):
            return None
        return {k: value[k] for k in IDENTITY_FIELDS}

    resources = resources if isinstance(resources, dict) else {}
    clean_resources = {}
    for name, item in resources.items():
        if name not in RESOURCE_SCHEMA or not isinstance(item, dict) or set(item) != {"value", "disposition", "unit"}:
            continue
        unit, value_type = RESOURCE_SCHEMA[name]
        value = item["value"]
        valid_number = type(value) in (value_type if isinstance(value_type, tuple) else (value_type,))
        if (not isinstance(item["disposition"], str) or item["disposition"] not in RESOURCE_CLASSES or item["unit"] != unit or not valid_number
                or not math.isfinite(value) or value < 0):
            clean_resources[name] = {"value": None, "disposition": item["disposition"] if item["disposition"] in RESOURCE_CLASSES else "reported", "unit": unit}
            continue
        clean_resources[name] = {"value": value, "disposition": item["disposition"], "unit": unit}
    if not isinstance(retry_count, int) or isinstance(retry_count, bool) or retry_count < 0:
        retry_count = 0
    safe_isolation = ({k: isolation[k] for k in ("worker_context_separate", "tester_blind_to_worker_private_state", "os_enforced")}
                      if isinstance(isolation, dict) and set(isolation) == {"worker_context_separate", "tester_blind_to_worker_private_state", "os_enforced"}
                      and all(v is None or type(v) is bool for v in isolation.values())
                      else {"worker_context_separate": None, "tester_blind_to_worker_private_state": None, "os_enforced": False})
    safe_rollback = ({"status": rollback["status"], "target": rollback["target"]}
                     if isinstance(rollback, dict) and set(rollback) == {"status", "target"}
                     and isinstance(rollback["status"], str) and rollback["status"] in {"not_attempted", "available", "completed", "failed"}
                     and (rollback["target"] is None or rollback["target"] in _SAFE_ROLLBACK_TARGETS)
                     else {"status": "not_attempted", "target": None})
    return {
        "schema": "councilflow.native-model-routing.execution/1.0",
        "configured_identity": safe_identity(configured),
        "requested_identity": safe_identity(requested),
        "host_reported_identity": safe_identity(host_reported),
        "effective_identity": safe_identity(effective),
        "reasoning_effort": reasoning_effort if isinstance(reasoning_effort, str) and reasoning_effort in _SAFE_EFFORTS else None,
        "policy_sha256": policy_sha256 if isinstance(policy_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", policy_sha256) else None,
        "qualification_ref": safe_ref(qualification_ref),
        "resources": clean_resources,
        "outcome": outcome if isinstance(outcome, str) and outcome in {"authorized", "denied", "dispatch_failed", "retrying", "cancelled", "incomplete", "completed"} else "incomplete",
        "retry_count": retry_count,
        "rollback": safe_rollback,
        "isolation": safe_isolation,
        "credential_material": "never_recorded",
        "disclaimer": "Descriptive data only; no authentication, resource enforcement, dispatch, or OS isolation.",
    }
