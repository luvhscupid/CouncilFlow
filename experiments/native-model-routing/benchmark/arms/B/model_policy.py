"""Pure fail-closed authorization for an exact model route."""
from __future__ import annotations

import re
from datetime import datetime, timezone


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _deny(reason: str) -> dict:
    return {"decision": "deny", "reason_code": reason}


def _utc(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def authorize(identity: dict, policy: dict, request: dict, now_utc: datetime) -> dict:
    """Authorize only a fully qualified, exact route explicitly permitted."""
    if not all(isinstance(item, dict) for item in (identity, policy, request)):
        return _deny("malformed_input")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        return _deny("malformed_input")

    evidence = identity.get("qualification_evidence")
    if evidence is None:
        return _deny("qualification_evidence_missing")
    if not isinstance(evidence, dict):
        return _deny("qualification_evidence_malformed")
    evidence_id, digest = evidence.get("evidence_id"), evidence.get("sha256")
    expiry = _utc(evidence.get("valid_until"))
    if not isinstance(evidence_id, str) or not evidence_id.strip() or not isinstance(digest, str) or not _SHA256.fullmatch(digest) or expiry is None:
        return _deny("qualification_evidence_malformed")
    if expiry <= now_utc.astimezone(timezone.utc):
        return _deny("qualification_expired")

    if identity.get("available") is not True:
        return _deny("unavailable")
    if identity.get("compatibility_status") != "QUALIFIED":
        return _deny("not_qualified")

    fields = ("provider", "route_id", "model_id", "harness")
    values = [request.get(key) for key in fields]
    if any(not isinstance(value, str) or not value for value in values):
        return _deny("malformed_input")
    if any(identity.get(key) != request.get(key) for key in fields):
        return _deny("identity_mismatch")

    role, task_class = request.get("role"), request.get("task_class")
    efforts = identity.get("supported_reasoning_efforts")
    effort = request.get("reasoning_effort")
    if not isinstance(role, str) or not role or not isinstance(task_class, str) or not task_class:
        return _deny("malformed_input")
    if not isinstance(effort, str) or not isinstance(efforts, list) or effort not in efforts:
        return _deny("unsupported_effort")

    allowed = policy.get("allowed_models")
    if not isinstance(allowed, list):
        return _deny("not_authorized")
    permitted = False
    for entry in allowed:
        if not isinstance(entry, dict):
            continue
        if (all(entry.get(key) == request.get(key) for key in fields)
                and isinstance(entry.get("roles"), list) and role in entry["roles"]
                and isinstance(entry.get("task_classes"), list) and task_class in entry["task_classes"]):
            permitted = True
            if not isinstance(entry.get("reasoning_efforts"), list) or effort not in entry["reasoning_efforts"]:
                return _deny("unsupported_effort")
            break
    if not permitted:
        return _deny("not_authorized")

    required = request.get("required_capabilities", [])
    capabilities = identity.get("capabilities")
    if (not isinstance(required, list) or any(not isinstance(item, str) for item in required)
            or not isinstance(capabilities, list) or any(not isinstance(item, str) for item in capabilities)):
        return _deny("malformed_input")
    if any(item not in capabilities for item in required):
        return _deny("capability_missing")
    return {"decision": "allow", "reason_code": "eligible"}
