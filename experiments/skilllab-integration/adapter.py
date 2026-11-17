"""Invoke SkillLab's public CLI as a capped suggestion source, never authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

PINNED_SKILLLAB_COMMIT = "40b4239e14f3c711ec3d32bb7ef4bb0820abdc63"
PINNED_REGISTRY_SHA256 = "5f8c2f969d85ce95431661c60a520ea000b64661555dfb7136b0ee2ba3289a1b"
PINNED_REGISTRY_VERSION = "1.1"
PINNED_SKILLLAB_SHA256 = "fe38aaeeb5c9c28818519073add3dddafe0e78cb594ec262603cea6b8cf43ee6"
MAX_CANDIDATES = 7
ELIGIBLE_CANDIDATE_IDS = frozenset({
    "writing-for-agents", "tdd", "codebase-memory", "diagnosing-bugs",
    "frontend-design", "mattpocock-skills:codebase-design", "mattpocock-skills:pr",
})


def suggest(*, repository: str | Path, role: str, task: str, actions: list[str],
            tools: list[str], conditions: list[str], candidate_ids: list[str],
            unavailable: bool = False, denied: bool = False) -> dict[str, Any]:
    """Return a Manager-side suggestion only; do not assign or activate skills."""
    base = {"adapter": "skilllab-suggestion/1.0", "selected": None,
            "activated": "unverified", "adds_tools": False, "adds_actions": False,
            "adds_permissions": False, "mutates_skilllab": False}
    if role != "manager":
        return {**base, "status": "denied", "reason": "Only the Manager may request suggestions."}
    if denied:
        return {**base, "status": "denied", "reason": "Manager policy denied optional suggestions."}
    if unavailable:
        return {**base, "status": "unavailable", "reason": "SkillLab is unavailable; continue with no-skill context."}
    if (not isinstance(candidate_ids, list) or len(candidate_ids) > MAX_CANDIDATES
            or any(not isinstance(x, str) for x in candidate_ids)
            or len(candidate_ids) != len(set(candidate_ids))
            or not set(candidate_ids) <= ELIGIBLE_CANDIDATE_IDS):
        return {**base, "status": "denied", "reason": "Candidate set must be unique and capped at seven."}
    try:
        if (not isinstance(task, str) or not task.strip() or len(task) > 4096
                or any(not isinstance(values, list) or len(values) > 128
                       or any(not isinstance(x, str) or len(x) > 1024 for x in values)
                       for values in (actions, tools, conditions))):
            return {**base, "status": "denied", "reason": "Malformed suggestion request."}
        root = Path(repository).resolve(strict=True)
        cli, registry = root / "skilllab.py", root / "registry.json"
        if not cli.is_file() or not registry.is_file():
            return {**base, "status": "unavailable", "reason": "Pinned public CLI or registry is missing."}
        cli_bytes = cli.read_bytes()
        if hashlib.sha256(cli_bytes).hexdigest() != PINNED_SKILLLAB_SHA256:
            return {**base, "status": "denied", "reason": "SkillLab executable bytes differ from the pinned commit."}
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", check=False)
        if head.returncode != 0 or head.stdout.strip() != PINNED_SKILLLAB_COMMIT:
            return {**base, "status": "denied", "reason": "SkillLab checkout commit differs from pinned snapshot."}
        registry_bytes = registry.read_bytes()
        if hashlib.sha256(registry_bytes).hexdigest() != PINNED_REGISTRY_SHA256:
            return {**base, "status": "denied", "reason": "Registry digest differs from pinned snapshot."}
        version = json.loads(registry_bytes.decode("utf-8"))["version"]
        if not isinstance(version, str) or version != PINNED_REGISTRY_VERSION:
            return {**base, "status": "denied", "reason": "Registry version differs from pin."}
        request = {"role": role, "task": task, "actions": actions, "tools": tools, "conditions": conditions}
        with tempfile.TemporaryDirectory(prefix="councilflow-skilllab-") as temp:
            request_path = Path(temp) / "request.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(cli), "route", "--registry", str(registry),
                                     "--request", str(request_path)], cwd=root,
                                    capture_output=True, text=True, encoding="utf-8", check=False)
        if result.returncode != 0:
            return {**base, "status": "unavailable", "reason": "Validated CLI returned a nonzero result."}
        routed = json.loads(result.stdout)
        if (not isinstance(routed, dict) or set(routed) != {"decisions", "reason", "selected"}
                or not isinstance(routed["decisions"], list) or len(routed["decisions"]) > 4096
                or not isinstance(routed["reason"], str)
                or (routed["selected"] is not None and not isinstance(routed["selected"], str))):
            return {**base, "status": "unavailable", "reason": "Validated CLI returned an invalid JSON shape."}
        selected = routed.get("selected")
        if selected is None:
            return {**base, "status": "no_skill", "reason": "No eligible candidate.",
                    "source_identity": _source_identity()}
        if not isinstance(selected, str) or selected not in candidate_ids:
            return {**base, "status": "denied", "reason": "CLI selection was outside the bounded candidate set.",
                    "source_identity": _source_identity()}
        return {**base, "status": "suggested", "selected": selected,
                "reason": "Suggestion only; Manager retains role, scope, and authority checks.",
                "source_identity": _source_identity()}
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        return {**base, "status": "unavailable", "reason": "Pinned SkillLab source or validated CLI could not be safely checked."}


def _source_identity() -> dict[str, str]:
    return {"commit": PINNED_SKILLLAB_COMMIT, "skilllab_sha256": PINNED_SKILLLAB_SHA256,
            "registry_sha256": PINNED_REGISTRY_SHA256, "registry_version": PINNED_REGISTRY_VERSION}
