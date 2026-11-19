"""Validate caller-claimed review metadata; no automatic prompt injection."""

from copy import deepcopy


_KINDS = {"SUCCESS", "FAILURE", "INSIGHT"}


def validate_entry(entry):
    required = {"entry_id", "kind", "project_scope", "review_claim", "evidence_refs", "superseded_by"}
    if not isinstance(entry, dict) or set(entry) != required:
        raise ValueError("experience entry has an invalid schema")
    if not all(isinstance(entry[key], str) and entry[key].strip() for key in ("entry_id", "project_scope")):
        raise ValueError("entry_id and project_scope must be non-empty strings")
    if not isinstance(entry["kind"], str) or entry["kind"] not in _KINDS:
        raise ValueError("kind must be SUCCESS, FAILURE, or INSIGHT")
    if entry["review_claim"] != "owner_reviewed":
        raise ValueError("review_claim must be owner_reviewed")
    if not isinstance(entry["evidence_refs"], list) or not entry["evidence_refs"] or any(not isinstance(ref, str) or not ref.strip() for ref in entry["evidence_refs"]):
        raise ValueError("evidence_refs must contain non-empty references")
    if entry["superseded_by"] is not None and (not isinstance(entry["superseded_by"], str) or not entry["superseded_by"].strip()):
        raise ValueError("superseded_by must be null or a non-empty ID")
    result = deepcopy(entry)
    result["review_status"] = "UNVERIFIED"
    return result


def select_entries(entries, project_scope):
    if not isinstance(entries, list) or not isinstance(project_scope, str) or not project_scope:
        raise ValueError("entries and project_scope are required")
    selected = []
    for entry in entries:
        checked = validate_entry(entry)
        if checked["project_scope"] == project_scope and checked["superseded_by"] is None:
            selected.append(checked)
    return sorted(selected, key=lambda item: item["entry_id"])
