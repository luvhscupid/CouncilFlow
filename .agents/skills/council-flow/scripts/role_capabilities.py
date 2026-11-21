"""Offline role preference and host-capability reporting; never routes a model."""

from copy import deepcopy


_ROLES = {"planner", "manager", "worker", "tester", "reviewer"}
_PREFERENCES = {"inherit_host", "lower_cost_if_qualified", "higher_reasoning_if_needed"}


def validate_profile(data):
    """Validate and copy the version 1 role preference profile."""
    if not isinstance(data, dict) or set(data) != {"schema_version", "roles"}:
        raise ValueError("profile must contain only schema_version and roles")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported profile schema_version")
    roles = data["roles"]
    if not isinstance(roles, dict) or not set(roles).issubset(_ROLES):
        raise ValueError("roles must be an object with known role names")
    for role, settings in roles.items():
        if not isinstance(settings, dict) or set(settings) != {"preference"}:
            raise ValueError(f"{role} settings must contain only preference")
        if not isinstance(settings["preference"], str) or settings["preference"] not in _PREFERENCES:
            raise ValueError(f"unsupported preference for {role}")
    return deepcopy(data)


def resolve_role(profile, capabilities, role):
    """Describe safe selection behavior from explicit capability evidence.

    This function never invokes a host or selects/configures a provider. Until a
    documented host-specific adapter exists, the effective model stays unknown.
    """
    profile = validate_profile(profile)
    if not isinstance(role, str) or role not in _ROLES:
        raise ValueError("unknown role")
    if not isinstance(capabilities, dict):
        raise ValueError("capabilities must be an object")
    explicit = capabilities.get("explicit_role_selection")
    if explicit is not None and type(explicit) is not bool:
        raise ValueError("explicit_role_selection must be true, false, or null")
    evidence_ref = capabilities.get("evidence_ref")
    if evidence_ref is not None and (not isinstance(evidence_ref, str) or not evidence_ref.strip()):
        raise ValueError("evidence_ref must be a non-empty string or null")
    return {
        "role": role,
        "preference": profile["roles"].get(role, {}).get("preference", "inherit_host"),
        "selection": "INHERIT_HOST",
        "capability_status": "UNKNOWN",
        "capability_reported": explicit is not None,
        "capability_evidence_ref": evidence_ref,
        "configured_model": None,
        "reported_model": None,
        "effective_model": None,
        "route_verified": False,
    }
