"""The Plan contract: every rule a CouncilFlow plan file must meet.

- validate_plan_context: the plan file a plan.publish message points to
  (identity, revision and acceptance; other plan metadata stays project-owned).
- validate_plan / validate_plan_bytes: a dispatchable READY plan with tasks.
- validate_worker_assignment: exact Planner-to-Worker instruction transfer.
- validate_readiness: a Planner readiness answer (READY, PROCEED_WITH_ASSUMPTIONS
  or BLOCKED), optionally checked against the project ledger and default budget.

The CLI checks a plan before publishing (`plan`) and a Worker job.assign before
dispatch (`assignment`). Each takes the frozen Owner criteria file, or
--planner-generated-criteria when the Owner supplied none (native planning).
`readiness <answer.json> [--project DIR]` checks a readiness answer and reports
whether it is dispatchable and whether it must go to the Owner.

A task may carry an optional `model_hint` (model, reasoning, reason). It is
advice only; the Manager decides the assignment.

It does not import from the experiments directory or enforce host permissions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)  # sibling modules also load when this file is imported by path
# Roles must not find __pycache__ written into the installed skill folder.
sys.dont_write_bytecode = True

import strict_json  # noqa: E402
from strict_json import MAX_ITEMS, ContractError, criterion, fail as _fail, identity  # noqa: E402

MAX_PLAN_BYTES = 65_536
READINESS_STATES = ("READY", "PROCEED_WITH_ASSUMPTIONS", "BLOCKED")
DECISION_CLASSES = ("cheap_reversible", "costly_reversible", "irreversible_external",
                    "security_data_financial_legal", "owner_objective")
REASONING_LEVELS = ("low", "medium", "high")
READINESS_FIELDS = {"schema", "version", "status", "slice_id", "ledger_version",
                    "discovery_cycle", "assumption_ids", "questions", "reason"}
QUESTION_FIELDS = {"question_id", "text", "blocking", "decision_class", "affected_slices",
                   "permitted_default", "reason"}


def _object(value, field, fields):
    if type(value) is not dict:
        _fail("type", field, "expected object")
    if set(value) != fields:
        _fail("fields", field, f"expected {sorted(fields)}; got {sorted(value)}")


def _identifier(value, field):
    if type(value) is not str or not value.strip() or value != value.strip():
        _fail("id", field, "expected nonempty string without surrounding whitespace")


def _model_hint(hint, field):
    _object_hint = type(hint) is dict and set(hint) == {"model", "reasoning", "reason"}
    if not _object_hint:
        _fail("model_hint", field, "expected object with exactly model, reasoning, reason")
    model = hint["model"]
    if type(model) is not str or not model.strip() or model != model.strip() or len(model) > 128:
        _fail("model_hint", field + ".model", "expected nonempty string without surrounding whitespace, max 128 chars")
    if type(hint["reasoning"]) is not str or hint["reasoning"] not in REASONING_LEVELS:
        _fail("model_hint", field + ".reasoning", "expected low, medium or high")
    if type(hint["reason"]) is not str or not hint["reason"].strip():
        _fail("model_hint", field + ".reason", "expected nonempty string")


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


def validate_plan_context(plan, *, plan_id, plan_revision, acceptance_ids,
                          expected_criteria=None, original_source_ref=None):
    """Check the plan file a plan.publish message points to.

    Plan metadata is project-owned, not a second wire schema: only identity,
    revision and acceptance are checked, plus fidelity to caller-pinned criteria
    and original source when the caller supplies them.
    """
    if type(plan) is not dict:
        _fail("plan_artifact", "payload.plan_ref", "plan context must be an object")
    identity(plan.get("plan_id"), "plan.plan_id")
    revision = plan.get("plan_revision")
    if type(revision) is not int or not 1 <= revision <= 2147483647:
        _fail("plan_artifact", "plan.plan_revision", "expected positive integer, never bool")
    if plan["plan_id"] != plan_id or revision != plan_revision:
        _fail("plan_artifact", "payload.plan_ref", "plan identity differs")
    acceptance = plan.get("acceptance")
    if type(acceptance) is not list or not acceptance or len(acceptance) > MAX_ITEMS:
        _fail("plan_artifact", "plan.acceptance", "expected bounded nonempty criterion array")
    ids = []
    for entry in acceptance:
        if type(entry) is not dict:
            _fail("plan_artifact", "plan.acceptance", "criterion entry must be an object")
        identity(entry.get("id"), "plan.acceptance.id")
        if "criterion" in entry:
            criterion(entry["criterion"], "plan.acceptance.criterion")
        ids.append(entry["id"])
    if len(set(ids)) != len(ids):
        _fail("plan_artifact", "plan.acceptance", "criterion identities must be unique")
    if ids != acceptance_ids:
        _fail("plan_artifact", "payload.acceptance_ids", "does not match original artifact")
    if expected_criteria is not None:
        if len(acceptance) != len(expected_criteria):
            _fail("acceptance_fidelity", "plan.acceptance", "criteria count differs from authoritative source")
        actual = [(identity(entry.get("id"), "plan.acceptance.id"),
                   criterion(entry.get("criterion"), "plan.acceptance.criterion"))
                  for entry in acceptance]
        if actual != expected_criteria:
            _fail("acceptance_fidelity", "plan.acceptance", "ordered criteria differ byte-for-byte from authoritative source")
    if original_source_ref is not None and plan.get("original_source_ref") != original_source_ref:
        _fail("criteria_source", "plan.original_source_ref", "plan must preserve the caller-pinned original source reference")
    return None


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
        task_fields = {"id", "instructions", "acceptance_ids", "depends_on"}
        if type(task) is dict and "model_hint" in task:
            task_fields = task_fields | {"model_hint"}
        _object(task, field, task_fields)
        if "model_hint" in task:
            _model_hint(task["model_hint"], field + ".model_hint")
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

    try:
        plan = strict_json.loads(raw.decode("utf-8", "strict"), field="plan")
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


def _text(value, field, code="readiness_field"):
    if type(value) is not str or not value.strip():
        _fail(code, field, "expected nonempty string")


def _optional_text(value, field):
    if value is not None:
        _text(value, field)


def _load_project_state():
    import project_state  # sibling module, same pattern as strict_json
    return project_state


def validate_question(question, field, seen=None):
    """Validate one question packet; `seen` (a set of question ids) also rejects duplicates."""
    _object(question, field, QUESTION_FIELDS)
    _identifier(question["question_id"], field + ".question_id")
    if seen is not None:
        if question["question_id"] in seen:
            _fail("duplicate_question", field + ".question_id", f"duplicate ID {question['question_id']!r}")
        seen.add(question["question_id"])
    _text(question["text"], field + ".text")
    _text(question["reason"], field + ".reason")
    if type(question["blocking"]) is not bool:
        _fail("readiness_field", field + ".blocking", "expected boolean")
    if type(question["decision_class"]) is not str or question["decision_class"] not in DECISION_CLASSES:
        _fail("decision_class", field + ".decision_class", f"expected one of {list(DECISION_CLASSES)}")
    _unique_ids(question["affected_slices"], field + ".affected_slices")
    _optional_text(question["permitted_default"], field + ".permitted_default")
    if question["decision_class"] != "cheap_reversible" and (
            not question["blocking"] or question["permitted_default"] is not None):
        _fail("class_downgrade", field,
              "a class other than cheap_reversible must be blocking and carry no permitted_default")


def validate_readiness(answer, project=None):
    """Validate a Planner readiness answer; return the dispatch summary.

    With `project` (a directory), also validate the project state and check that
    each assumption id is an unconfirmed Assumption in the answer's ledger version.
    """
    if type(answer) is not dict:
        _fail("type", "readiness", "expected object")
    if set(answer) != READINESS_FIELDS:
        _fail("fields", "readiness", f"expected {sorted(READINESS_FIELDS)}; got {sorted(answer)}")
    if answer["schema"] != "councilflow-readiness" or answer["version"] != "1.0":
        _fail("readiness_schema", "readiness", "expected councilflow-readiness 1.0")
    status = answer["status"]
    if type(status) is not str or status not in READINESS_STATES:
        _fail("readiness_status", "readiness.status", f"expected one of {list(READINESS_STATES)}")
    if answer["slice_id"] is not None:
        _identifier(answer["slice_id"], "readiness.slice_id")
    version = answer["ledger_version"]
    if version is not None and (type(version) is not int or version < 1):
        _fail("readiness_field", "readiness.ledger_version", "expected integer >= 1 or null")
    if type(answer["discovery_cycle"]) is not int or answer["discovery_cycle"] not in (1, 2):
        _fail("readiness_field", "readiness.discovery_cycle", "expected 1 or 2")
    assumption_ids = _unique_ids(answer["assumption_ids"], "readiness.assumption_ids")
    _text(answer["reason"], "readiness.reason")

    questions = answer["questions"]
    if type(questions) is not list:
        _fail("readiness_field", "readiness.questions", "expected array")
    seen, blocking = set(), 0
    for index, question in enumerate(questions):
        field = f"readiness.questions[{index}]"
        validate_question(question, field, seen)
        blocking += question["blocking"]

    if status == "READY":
        if assumption_ids or blocking:
            _fail("readiness_state", "readiness.status", "READY allows no assumption_ids and no blocking questions")
    elif status == "PROCEED_WITH_ASSUMPTIONS":
        if not assumption_ids or blocking:
            _fail("readiness_state", "readiness.status",
                  "PROCEED_WITH_ASSUMPTIONS needs assumption_ids and no blocking questions")
        if version is None:
            _fail("readiness_state", "readiness.ledger_version", "PROCEED_WITH_ASSUMPTIONS needs a ledger_version")
    elif not blocking:
        _fail("readiness_state", "readiness.status", "BLOCKED needs at least one blocking question")

    budget, reasons = None, []
    if project is not None:
        state = _load_project_state()
        errors, extra = state.validate(Path(project))
        if errors:
            _fail("project_invalid", str(project), "project state failed validation")
        budget = extra["budget"]
        if version is not None:
            if extra["ledger_version"] is None or version > extra["ledger_version"]:
                _fail("assumption_ref", "readiness.ledger_version", "ledger version does not exist in the project")
            ledger = json.loads((Path(project) / "ledger" / f"L{version:04d}.json").read_text(encoding="utf-8"))
            entries = {entry["id"]: entry for entry in ledger["entries"]}
            for aid in sorted(assumption_ids):
                entry = entries.get(aid)
                if entry is None or entry["type"] != "Assumption" or entry["status"] != "unconfirmed":
                    _fail("assumption_ref", "readiness.assumption_ids",
                          f"{aid!r} is not an unconfirmed Assumption in ledger version {version}")
        elif assumption_ids:
            _fail("assumption_ref", "readiness.ledger_version", "assumption_ids need a ledger_version")

    if status == "READY":
        dispatchable = True
    elif status == "BLOCKED":
        dispatchable = False
    elif budget is None:
        dispatchable = False
        reasons.append("budget_unchecked")
    elif budget["exceeded"]:
        dispatchable = False
        reasons.append("budget_exhausted")
    else:
        dispatchable = True
    return {"valid": True, "status": status, "dispatchable": dispatchable,
            "escalate_to_owner": status == "BLOCKED" and answer["discovery_cycle"] == 2,
            "budget": budget, "reasons": reasons}


def _read(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_PLAN_BYTES:
        _fail("size", str(path), f"maximum is {MAX_PLAN_BYTES} bytes")
    return json.loads(raw.decode("utf-8", "strict"))


def _criteria(plan, files, generated, others):
    """Return (criteria, remaining files, source label): frozen file XOR planner-generated flag."""
    if generated and len(files) == others:
        acceptance = plan.get("acceptance") if type(plan) is dict else None
        return acceptance, files, "planner-generated"
    if not generated and len(files) == others + 1:
        return _read(files[0]), files[1:], "frozen"
    _fail("criteria_source", "original_criteria",
          "pass either the frozen criteria file or --planner-generated-criteria, exactly one")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generated_help = ("the Owner supplied no frozen criteria (native planning): check the plan's own "
                      "acceptance structurally and say so; never copy it into a frozen-criteria file")
    check = sub.add_parser("assignment", help="validate a READY plan and exact Worker assignment",
                           usage="%(prog)s plan.json (frozen-criteria.json | --planner-generated-criteria) assignment.json")
    check.add_argument("plan")
    check.add_argument("files", nargs="+", metavar="file",
                       help="[frozen-criteria.json] assignment.json: the criteria JSON array of "
                            "{id, criterion} items, then the council-flow 1.0 job.assign envelope")
    check.add_argument("--planner-generated-criteria", action="store_true", help=generated_help)
    self_check = sub.add_parser("plan", help="validate a READY plan before publishing it",
                                usage="%(prog)s plan.json (frozen-criteria.json | --planner-generated-criteria)")
    self_check.add_argument("plan")
    self_check.add_argument("files", nargs="*", metavar="frozen-criteria.json")
    self_check.add_argument("--planner-generated-criteria", action="store_true", help=generated_help)
    ready = sub.add_parser("readiness", help="validate a Planner readiness answer")
    ready.add_argument("answer")
    ready.add_argument("--project", help="project state directory: check ledger references and the default budget")
    args = parser.parse_args(argv)
    if args.command == "readiness":
        try:
            raw = Path(args.answer).read_bytes()
            if len(raw) > MAX_PLAN_BYTES:
                _fail("size", args.answer, f"maximum is {MAX_PLAN_BYTES} bytes")
            result = validate_readiness(strict_json.loads(raw.decode("utf-8", "strict"), field="readiness"),
                                        args.project)
        except (ContractError, OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
            print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
        print(json.dumps(result, separators=(",", ":")))
        return 0
    try:
        plan = _read(args.plan)
        if args.command == "plan":
            criteria, _, source = _criteria(plan, args.files, args.planner_generated_criteria, 0)
            validate_plan(plan, criteria)
            print(json.dumps({"valid": True, "criteria_source": source}, separators=(",", ":")))
            return 0
        criteria, rest, source = _criteria(plan, args.files, args.planner_generated_criteria, 1)
        message = _read(rest[0])
        if type(message) is not dict or message.get("message_type") != "job.assign":
            _fail("assignment", "message_type", "expected job.assign envelope")
        payload = message.get("payload")
        if type(payload) is not dict:
            _fail("assignment", "payload", "expected object")
        # payload.plan_task_id names the Planner task; the envelope task_id is the run's
        # task and only selects a plan task when plan_task_id is absent (single-task runs).
        validate_worker_assignment(plan, plan_id=message.get("plan_id"),
                                   plan_revision=message.get("plan_revision"),
                                   task_id=payload.get("plan_task_id", message.get("task_id")),
                                   acceptance_ids=payload.get("acceptance_ids"),
                                   instructions=payload.get("instructions"),
                                   original_acceptance=criteria)
    except (ContractError, OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "dispatchable": True, "criteria_source": source}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
