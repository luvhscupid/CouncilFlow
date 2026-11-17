"""Fail-closed validation for an explicitly approved model route."""
from __future__ import annotations

from datetime import datetime, timezone
import re


def _deny(reason: str) -> dict:
    return {"decision": "deny", "reason_code": reason}


def _mapping(value: object) -> bool:
    return type(value) is dict


def _text(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _utc(value: object) -> datetime | None:
    if type(value) is not str:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def authorize(identity: dict, policy: dict, request: dict, now_utc: datetime) -> dict:
    """Authorize an exact qualified route, returning only a fixed reason code."""
    if not all(_mapping(v) for v in (identity, policy, request)):
        return _deny("malformed_input")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None:
        return _deny("malformed_input")
    try:
        now = now_utc.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return _deny("malformed_input")

    if identity.get("available") is not True:
        return _deny("unavailable")
    if identity.get("compatibility_status") != "QUALIFIED":
        return _deny("not_qualified")

    evidence = identity.get("qualification_evidence")
    if not _mapping(evidence):
        return _deny("qualification_evidence_missing")
    evidence_id, digest = evidence.get("evidence_id"), evidence.get("sha256")
    if (not _text(evidence_id) or type(digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
        return _deny("qualification_evidence_invalid")
    expiry = _utc(evidence.get("valid_until"))
    if expiry is None:
        return _deny("qualification_evidence_invalid")
    if expiry <= now:
        return _deny("qualification_expired")

    effort = request.get("reasoning_effort")
    supported = identity.get("supported_reasoning_efforts")
    if (not _text(effort) or type(supported) is not list
            or any(not _text(item) for item in supported)
            or effort not in supported):
        return _deny("unsupported_effort")

    capabilities = request.get("required_capabilities")
    identity_capabilities = identity.get("capabilities")
    if (type(capabilities) is not list or type(identity_capabilities) is not list
            or any(not _text(item) for item in capabilities)
            or any(not _text(item) for item in identity_capabilities)):
        return _deny("capability_missing")
    if any(cap not in identity_capabilities for cap in capabilities):
        return _deny("capability_missing")

    route_fields = ("provider", "route_id", "model_id", "harness")
    if any(not _text(request.get(key)) or not _text(identity.get(key))
           for key in route_fields):
        return _deny("identity_mismatch")
    if any(request[key] != identity[key] for key in route_fields):
        return _deny("identity_mismatch")

    role, task_class = request.get("role"), request.get("task_class")
    entries = policy.get("allowed_models")
    if (not _text(role) or not _text(task_class) or type(entries) is not list):
        return _deny("not_authorized")
    for entry in entries:
        if not _mapping(entry):
            continue
        if any(entry.get(key) != request[key] for key in route_fields):
            continue
        roles, classes, efforts = entry.get("roles"), entry.get("task_classes"), entry.get("reasoning_efforts")
        if (type(roles) is list and role in roles
                and type(classes) is list and task_class in classes
                and type(efforts) is list and effort in efforts):
            return {"decision": "allow", "reason_code": "eligible"}
    return _deny("not_authorized")
