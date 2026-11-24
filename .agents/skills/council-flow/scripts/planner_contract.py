"""Fail-closed validation for READY Planner plans and Worker instruction transfer.

This is a standalone production copy of the tested experimental contract; it
does not import from the experiments directory or enforce host permissions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

MAX_PLAN_BYTES = 65_536


class ContractError(ValueError):
    def __init__(self, code: str, field: str, detail: str):
        self.code, self.field, self.detail = code, field, detail
        super().__init__(f"{code} at {field}: {detail}")


def _fail(code, field, detail):
    raise ContractError(code, field, detail)


def _object(value, field, fields):
    if type(value) is not dict:
        _fail("type", field, "expected object")
    if set(value) != fields:
        _fail("fields", field, f"expected {sorted(fields)}; got {sorted(value)}")


def _identifier(value, field):
    if type(value) is not str or not value.strip() or value != value.strip():
        _fail("id", field, "expected nonempty string without surrounding whitespace")


def _unique_ids(values, field):
    if type(values) is not list:
        _fail("array", field, "expected string array")
    seen = set()
    for index, value in enumerate(values):
        _identifier(value, f"{field}[{index}]")
        if value in seen:
            _fail("duplicate_id", f"{field}[{index}]", f"duplicate ID {value!r}")
        seen.add(value)
    return seen


def _cycles(tasks):
    remaining = {key: set(value) for key, value in tasks.items()}
    ready = [key for key, deps in remaining.items() if not deps]
    visited = set()
    while ready:
        done = ready.pop()
        visited.add(done)
        for key, deps in remaining.items():
            if done in deps:
                deps.remove(done)
                if not deps and key not in visited:
                    ready.append(key)
    if len(visited) != len(tasks):
        _fail("dependency_cycle", "plan.tasks.depends_on", "dependency graph contains a cycle")


def validate_plan(plan, original_acceptance):
    """Validate a complete dispatchable plan against caller-pinned criteria."""
    _object(plan, "plan", {"plan_id", "plan_revision", "acceptance", "tasks"})
    _identifier(plan["plan_id"], "plan.plan_id")
    rev = plan["plan_revision"]
    if type(rev) is not int or rev < 1:
        _fail("revision", "plan.plan_revision", "expected positive integer")

    acceptance = plan["acceptance"]
    if type(acceptance) is not list or not acceptance:
        _fail("acceptance", "plan.acceptance", "expected nonempty array")
    ids, criteria = [], {}
    for index, item in enumerate(acceptance):
        field = f"plan.acceptance[{index}]"
        _object(item, field, {"id", "criterion"})
        _identifier(item["id"], field + ".id")
        if type(item["criterion"]) is not str or not item["criterion"].strip():
            _fail("criterion", field + ".criterion", "expected nonempty criterion text")
        item["criterion"].encode("utf-8", "strict")
        ids.append(item["id"])
        criteria[item["id"]] = item["criterion"]
    _unique_ids(ids, "plan.acceptance[].id")

    if type(original_acceptance) is not list or not original_acceptance:
        _fail("original_acceptance", "original_acceptance", "frozen criteria are required")
    original_ids, original = [], {}
    for index, item in enumerate(original_acceptance):
        field = f"original_acceptance[{index}]"
        _object(item, field, {"id", "criterion"})
        _identifier(item["id"], field + ".id")
        if type(item["criterion"]) is not str or not item["criterion"].strip():
            _fail("criterion", field + ".criterion", "expected nonempty criterion text")
        original_ids.append(item["id"])
        original[item["id"]] = item["criterion"]
    _unique_ids(original_ids, "original_acceptance[].id")
    if ids != original_ids or criteria != original:
        _fail("criteria_fidelity", "plan.acceptance", "ordered criteria differ from frozen source")

    rows = plan["tasks"]
    if type(rows) is not list or not rows:
        _fail("tasks", "plan.tasks", "dispatchable READY plan requires tasks")
    task_ids, graph, covered = [], {}, set()
    for index, task in enumerate(rows):
        field = f"plan.tasks[{index}]"
        _object(task, field, {"id", "instructions", "acceptance_ids", "depends_on"})
        _identifier(task["id"], field + ".id")
        task_ids.append(task["id"])
        instructions = task["instructions"]
        if type(instructions) is not list or not instructions:
            _fail("instructions", field + ".instructions", "expected nonempty instruction array")
        for n, text in enumerate(instructions):
            if type(text) is not str or not text.strip():
                _fail("instruction", f"{field}.instructions[{n}]", "expected nonempty string")
            text.encode("utf-8", "strict")
        refs = task["acceptance_ids"]
        refs_set = _unique_ids(refs, field + ".acceptance_ids")
        if not refs_set:
            _fail("coverage", field + ".acceptance_ids", "each task must cover acceptance")
        unknown = refs_set - set(ids)
        if unknown:
            _fail("unknown_acceptance", field + ".acceptance_ids", str(sorted(unknown)))
        covered.update(refs_set)
        graph[task["id"]] = _unique_ids(task["depends_on"], field + ".depends_on")
    _unique_ids(task_ids, "plan.tasks[].id")
    task_set = set(task_ids)
    for task_id, deps in graph.items():
        if deps - task_set:
            _fail("unknown_dependency", f"plan.tasks.{task_id}.depends_on", str(sorted(deps - task_set)))
        if task_id in deps:
            _fail("dependency_cycle", f"plan.tasks.{task_id}.depends_on", "task cannot depend on itself")
    _cycles(graph)
    if covered != set(ids):
        _fail("missing_coverage", "plan.tasks[].acceptance_ids", str(sorted(set(ids) - covered)))
    return None


def validate_plan_bytes(data, original_acceptance):
    if type(data) not in (bytes, bytearray, memoryview):
        _fail("type", "plan", "expected bytes")
    raw = bytes(data)
    if len(raw) > MAX_PLAN_BYTES:
        _fail("size", "plan", f"maximum is {MAX_PLAN_BYTES} bytes")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("duplicate_key", "plan", f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        plan = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs,
                          parse_constant=lambda value: _fail("json", "plan", value))
    except ContractError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        _fail("json", "plan", str(exc))
    return validate_plan(plan, original_acceptance)


def validate_worker_assignment(plan, *, plan_id, plan_revision, task_id,
                               acceptance_ids, instructions, original_acceptance):
    validate_plan(plan, original_acceptance)
    if plan_id != plan["plan_id"] or plan_revision != plan["plan_revision"]:
        _fail("plan_identity", "job.assign", "assignment plan identity/revision differs")
    _identifier(task_id, "job.assign.task_id")
    task = next((item for item in plan["tasks"] if item["id"] == task_id), None)
    if task is None:
        _fail("unknown_task", "job.assign.task_id", task_id)
    if acceptance_ids != task["acceptance_ids"]:
        _fail("acceptance_transfer", "job.assign.acceptance_ids", "must equal selected Planner task")
    if instructions != task["instructions"]:
        _fail("instruction_transfer", "job.assign.instructions", "must exactly match Planner text and order")
    return None


def _read(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_PLAN_BYTES:
        _fail("size", str(path), f"maximum is {MAX_PLAN_BYTES} bytes")
    return json.loads(raw.decode("utf-8", "strict"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("assignment", help="validate a READY plan and exact Worker assignment")
    check.add_argument("plan")
    check.add_argument("original_criteria", help="JSON array of frozen {id, criterion} items")
    check.add_argument("assignment", help="council-flow 1.0 job.assign envelope")
    args = parser.parse_args(argv)
    try:
        plan = _read(args.plan)
        criteria = _read(args.original_criteria)
        message = _read(args.assignment)
        if type(message) is not dict or message.get("message_type") != "job.assign":
            _fail("assignment", "message_type", "expected job.assign envelope")
        payload = message.get("payload")
        if type(payload) is not dict:
            _fail("assignment", "payload", "expected object")
        validate_worker_assignment(plan, plan_id=message.get("plan_id"),
                                   plan_revision=message.get("plan_revision"),
                                   task_id=message.get("task_id"),
                                   acceptance_ids=payload.get("acceptance_ids"),
                                   instructions=payload.get("instructions"),
                                   original_acceptance=criteria)
    except (ContractError, OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "dispatchable": True}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
