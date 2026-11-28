# Adaptive mode schemas (adaptive-1)

Optional extension, non-normative until Owner-approved, batch adr-batch-s2-s11.
Standalone JSON artifacts; referenced from messages only as artifact refs
`{artifact_id, path, sha256, kind}`. No message type, field, role or route is added.

## slice-plan (author: Manager)

| Field | Type / rule |
| --- | --- |
| schema_version | `"adaptive-1"` |
| author_role | `"manager"` (Manager is sole owner of the slice plan) |
| plan_id | nonempty string |
| plan_revision | positive integer (not boolean) |
| mode | `"adaptive"` or `"default"`; `default` means the existing planner.md / planner_contract.py path and requires `slices: []` |
| slices | list of slice objects |

Slice: `slice_id` (unique nonempty string), `title` (nonempty string), `depends_on`
(list of existing slice_ids, acyclic), `assignment` `{role: worker|tester|reviewer,
instance_hint?: nonempty string}` (wire names only; display aliases such as
"Software Engineer" are invalid), `model_routing` (string, advisory),
`execution_status` (`pending|in_progress|blocked|done`), `pinned_ledger_version`
(positive integer).

## slice-readiness (author: Planner)

| Field | Type / rule |
| --- | --- |
| schema_version | `"adaptive-1"` |
| author_role | `"planner"` |
| plan_id, slice_id, reason | nonempty strings |
| state | `READY`, `NEEDS_INFORMATION`, `BLOCKED` (PROCEED_WITH_ASSUMPTIONS is added by step S8) |
| ledger_version | positive integer |
| task_instructions | optional list of nonempty strings (Planner-authored) |

## Coherence

`check_coherence(plan, readinesses)`: each readiness has the plan's `plan_id`, names an
existing slice, and its `ledger_version` equals that slice's `pinned_ledger_version`.
