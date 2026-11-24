"""Hash-linked, non-authoritative route decision records."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from .contract import DecisionStatus, RouteDecision

_ACTIONS = {"accepted", "overridden", "ignored", "blocked"}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _record_hash(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _seal(record: dict[str, Any]) -> dict[str, Any]:
    record["record_sha256"] = _record_hash(record)
    return record


def build_decision_record(decision: RouteDecision, *, manager_action: str, evidence_ref: str | None = None) -> dict[str, Any]:
    if not isinstance(decision, RouteDecision):
        raise ValueError("decision must be a RouteDecision")
    if manager_action not in _ACTIONS:
        raise ValueError("manager action is unsupported")
    if evidence_ref is not None and (not isinstance(evidence_ref, str) or not evidence_ref.strip() or len(evidence_ref) > 256):
        raise ValueError("evidence reference must be bounded text")
    record = {
        "schema_version": "routing-decision-v1",
        "status": decision.status.value,
        "route": decision.route,
        "confidence": decision.confidence,
        "threshold": decision.threshold,
        "margin": decision.margin,
        "router_version": decision.router_version,
        "route_config_sha256": decision.route_config_sha256,
        "input_sha256": decision.input_sha256,
        "encoder_id": decision.encoder_id,
        "reason_codes": list(decision.reason_codes),
        "manager_action": manager_action,
    }
    if evidence_ref is not None:
        record["evidence_ref"] = evidence_ref
    _seal(record)
    validate_decision_record(record)
    return record


def validate_decision_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ValueError("decision record must be an object")
    allowed = {
        "schema_version", "status", "route", "confidence", "threshold", "margin", "router_version",
        "route_config_sha256", "input_sha256", "encoder_id", "reason_codes", "manager_action",
        "evidence_ref", "manager_reason", "record_sha256",
    }
    if set(record) - allowed:
        raise ValueError("decision record contains unsupported fields")
    if record.get("schema_version") != "routing-decision-v1":
        raise ValueError("unsupported decision record schema")
    if record.get("status") not in {status.value for status in DecisionStatus}:
        raise ValueError("unsupported decision status")
    if record.get("route") is not None and (not isinstance(record["route"], str) or not record["route"].strip()):
        raise ValueError("route must be null or nonempty text")
    for field in ("confidence", "threshold", "margin"):
        value = record.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{field} must be between 0 and 1")
    for field in ("router_version", "encoder_id"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"{field} must be nonempty text")
    for field in ("route_config_sha256", "input_sha256", "record_sha256"):
        if not isinstance(record.get(field), str) or not _DIGEST.fullmatch(record[field]):
            raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    if record["record_sha256"] != _record_hash(record):
        raise ValueError("decision record integrity hash mismatch")
    if not isinstance(record.get("reason_codes"), list) or any(not isinstance(item, str) or not item.strip() for item in record["reason_codes"]):
        raise ValueError("reason_codes must be a list of nonempty text")
    if record.get("manager_action") not in _ACTIONS:
        raise ValueError("manager action is unsupported")
    if "evidence_ref" in record and (not isinstance(record["evidence_ref"], str) or not record["evidence_ref"].strip()):
        raise ValueError("evidence_ref must be nonempty text")
    if "manager_reason" in record and (not isinstance(record["manager_reason"], str) or not record["manager_reason"].strip()):
        raise ValueError("manager_reason must be nonempty text")


def accept_route(record: dict[str, Any]) -> dict[str, Any]:
    validate_decision_record(record)
    accepted = copy.deepcopy(record)
    accepted["manager_action"] = "accepted"
    accepted.pop("manager_reason", None)
    _seal(accepted)
    validate_decision_record(accepted)
    return accepted


def override_route(record: dict[str, Any], reason: str) -> dict[str, Any]:
    validate_decision_record(record)
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 1024:
        raise ValueError("override reason must be bounded nonempty text")
    overridden = copy.deepcopy(record)
    overridden["manager_action"] = "overridden"
    overridden["manager_reason"] = reason
    _seal(overridden)
    validate_decision_record(overridden)
    return overridden
