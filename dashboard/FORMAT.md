# Presentation projection version 1

The authoritative executable validation is `parseSnapshot` in projection.mjs. This closed view format is independent of CouncilFlow packets. Start with fixtures/review.json; do not submit native packets directly or rename them into this format. Prepare sanitized records manually or in a separately authorized adapter. The viewer cannot certify source completeness or authenticate the producer.

| Field | Meaning / constraints |
|---|---|
| view_schema | Exactly `councilflow-dashboard-view/1` |
| synthetic | Required boolean, true for any demonstration run |
| run_id, title | Stable identifier and sanitized display title (500 characters max) |
| status | queued, active, waiting-for-Owner, blocked, failed, completed, cancelled, interrupted, unknown |
| phase | Owner, Planner, Manager, Worker, Tester, Reviewer, Unknown |
| active_attempt | Existing attempt ID; nullable/absent only without attempts |
| source | label (required), original_criteria_ref (nullable opaque identity; never followed) |
| started_at, last_observed_at | Optional UTC ISO timestamps, valid chronology; missing duration remains unknown |
| criteria | Original, unique `{id, text}` entries; never derived from number of messages |
| attempts | Unique `{id, candidate, label, results}` entries |
| attempts[].results | Unique `{criterion_id, stage, evidence_ids}` entries, bound to that attempt |
| roles | Up to five unique CouncilFlow `{role,state,model,assignment,last_activity,attempt_id,tokens}` entries; nullable optional display fields |
| activity | Unique `{id,at,role,category,tone,label,detail,provenance,attempt_id}` entries, retained in source order and displayed newest record first |
| evidence | Unique `{id,kind,attempt_id,candidate,criterion_id,outcome,provenance,summary,reference,command,exit_code,stdout_sha256,compared_stdout_sha256,compared_exit_code}` |
| metrics | Optional `{tokens,files_changed,tests_passed,tests_failed,messages,token_scope}`; absent/null values stay unknown |
| blockers | Optional `{kind,text}` list; kind is blocker, failed check, missing evidence, or Owner decision |

Identifiers match `[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}`. Default text cap is 1,000 characters, original criterion text and evidence summaries 2,000. Candidates and attempt labels cap at 200. Counts are nonnegative safe integers; exit codes are signed safe integers. No additional properties are accepted. Never put prompts, secrets, raw logs or private file contents in allowed text fields.

Role state: not observed, active, waiting, stopped, failed, unknown. Missing roles render as not observed. No independent process is inferred. Event role may also be Unattributed. Categories: handoff, implementation, verification, decision, system. Tones: info, success, warning, failure. All events need an explicit provenance label.

Criterion stages: Not started, Worker reported, Tester passed, Tester failed, Reviewer checked, Planner accepted, Planner rejected. These labels alone are claims. Version 1 counts a Planner accepted result only when its evidence references contain the complete passing chain and no known contradictory record exists for that criterion/attempt. Missing results are Not started; no acceptance migrates between attempts.

Evidence kinds: contract, source-fidelity, worker, tester, reviewer, rerun, planner. Outcomes: passed, failed, unverified, accepted, rejected. Every evidence item binds an existing criterion and exact attempt/candidate. SHA-256 values are 64 lowercase hexadecimal characters. A counted rerun must match the linked Tester command, exit 0 and stdout hash; its compared fields must agree. The viewer does not execute the command or verify the original stdout bytes. The source reference, structural/fidelity records and execution summaries remain producer assertions.

The six provenance names are exactly Host-observed, Structurally validated, Execution evidence, Agent-reported, Derived, Synthetic demonstration. A non-synthetic run cannot contain synthetic events. To demonstrate an import with illustrative records, keep synthetic=true; never relabel demo data as real observations.

The version intentionally contains no executable URLs, embedded HTML, role controls, permission decisions, inferred cost, ETA or automatic artifact loading. Reference paths may be displayed literally, including hostile-looking paths; they cannot trigger filesystem traversal because they are never dereferenced. UTF-8 decoding replacement characters are rendered literally rather than treated as evidence of correct source fidelity.
