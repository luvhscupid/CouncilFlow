"""Pure validation for dependency graphs; this module never schedules work."""

from collections import defaultdict, deque


def validate_graph(nodes, plan_revision):
    errors = []
    blocked = set()
    by_id = {}
    if not isinstance(nodes, list) or type(plan_revision) is not int:
        raise ValueError("nodes must be a list and plan_revision an integer")
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("task_id"), str) or not node["task_id"]:
            raise ValueError("each node requires a non-empty task_id")
        task_id = node["task_id"]
        if task_id in by_id:
            errors.append("DUPLICATE_TASK_ID")
        by_id[task_id] = node
        if not isinstance(node.get("depends_on"), list) or any(not isinstance(dep, str) or not dep for dep in node["depends_on"]):
            raise ValueError("depends_on must be a list of task IDs")
        revision = node.get("plan_revision")
        if type(revision) is not int:
            raise ValueError("plan_revision on each node must be an integer")
        if revision != plan_revision:
            errors.append("STALE_PLAN_REVISION")
            blocked.add(task_id)
        status = node.get("status")
        if status is not None and not isinstance(status, str):
            raise ValueError("status must be a string or null")
        if status in {"BLOCKED", "FAILED", "CANCELLED"}:
            blocked.add(task_id)
    indegree = {task_id: 0 for task_id in by_id}
    children = defaultdict(list)
    for task_id, node in by_id.items():
        for dep in node["depends_on"]:
            if dep not in by_id:
                errors.append("MISSING_DEPENDENCY")
                blocked.add(task_id)
                continue
            indegree[task_id] += 1
            children[dep].append(task_id)
            if dep in blocked:
                blocked.add(task_id)
    ready = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    order = []
    while ready:
        current = ready.popleft()
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(by_id):
        errors.append("CYCLE")
    # Propagate blockers through all descendants, including after topological discovery.
    queue = deque(blocked)
    while queue:
        for child in children[queue.popleft()]:
            if child not in blocked:
                blocked.add(child)
                queue.append(child)
    if errors:
        order = []
    return {"valid": not errors, "errors": sorted(set(errors)), "order": order,
            "blocked": sorted(blocked), "parallel_execution_enabled": False}
