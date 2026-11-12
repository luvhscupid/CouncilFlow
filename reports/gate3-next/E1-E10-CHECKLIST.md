# Gate 3 preparation checklist

This file prepares evidence capture; **the frozen Gate 3 experiment was not executed in this mission**. It does not define or alter acceptance. The controlling sources are:

- `docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md` — SHA-256 `e97053e51723ff40b7a328a10c3c5f759289869d2cc9dfb55dc3c1869bb2b523`
- `docs/gate3/CouncilFlow-Gate3-v0.2/02-GATE3-v0.2-FROZEN.md` — SHA-256 `99812898178506eaf88afbc5b31005bf4772f775fef7e46bc633289815167be2`
- `docs/gate3/CouncilFlow-Gate3-v0.2/06-COUNCIL-APPROVED-ERRATUM-C3.md` — SHA-256 `4655f3425ed8a312c28b2324e8d5b6730d568bf5ab3aa8c4e2439d9d4d438d6e`

Use the exact E1-E10 definitions and wording in the frozen sources, applying C3 only to E4. Do not paraphrase the criteria into an alternate acceptance source.

## Evidence capture fields

For every E criterion, record its exact frozen text/source location, observation artifact identity and hash, actual native session/thread identity when exposed, command/tool and exact arguments when applicable, raw result, actor provenance limitations, and one status. Allowed statuses: `PASS`, `FAIL`, `BLOCKED`, `UNVERIFIED`. For each non-pass status, select exactly one primary class: `AUTH`, `HOST_CAPABILITY_MISSING`, `WORKFLOW_BEHAVIOR`, or `EVIDENCE_INSUFFICIENT`. Explain any secondary context in prose without changing the primary class.

Special handling required by the frozen procedure:

- E3: if distinct native spawning is not established, stop the observation and return the evidence; make no spontaneous implementation changes.
- E7: count zero Owner courier interventions; keep this separate from legitimate authorization decisions.
- E8: `NOT_COMPARABLE` is not a pass. Preserve the Tester declaration and Reviewer execution details and compare exit plus CRLF-to-LF-only normalized stdout SHA-256.
- E10: compare the prompt against the actual Owner-saved fixture, never a generated substitute.

## Current preparation record (not Gate 3 outcomes)

| Criterion | Preparation status | Primary class | Evidence / limitation |
|---|---|---|---|
| E1 | BLOCKED | HOST_CAPABILITY_MISSING | This mission did not capture the frozen procedure's host-observed activation/picker evidence. |
| E2 | BLOCKED | HOST_CAPABILITY_MISSING | This mission did not run a frozen activation-trigger observation. |
| E3 | UNVERIFIED | EVIDENCE_INSUFFICIENT | NOT EXECUTED as the frozen experiment; distinct role sessions in this mission do not count. |
| E4 | BLOCKED | HOST_CAPABILITY_MISSING | Loaded native TOML identity is not host-observed. C3 applies only as specified by the frozen erratum. |
| E5 | UNVERIFIED | EVIDENCE_INSUFFICIENT | NOT EXECUTED in a Gate 3 Tester session. |
| E6 | UNVERIFIED | EVIDENCE_INSUFFICIENT | NOT EXECUTED in the frozen observation. |
| E7 | UNVERIFIED | EVIDENCE_INSUFFICIENT | No frozen-procedure Owner courier log exists. |
| E8 | UNVERIFIED | EVIDENCE_INSUFFICIENT | The mission's separate command rerun is not an E8 observation. |
| E9 | UNVERIFIED | EVIDENCE_INSUFFICIENT | No frozen-procedure Owner-interface observation exists. |
| E10 | BLOCKED | EVIDENCE_INSUFFICIENT | No authentic Owner-saved task fixture was supplied. The draft in this folder is explicitly unapproved. |

These are preparation labels only. No E1-E10 criterion passed or failed in this mission.

## Readiness verdict (not an E1-E10 result)

**BLOCKED_WITH_EXACT_PREREQUISITES**

- The authentic Owner-saved fixture does not exist yet. `OWNER-TASK-DRAFT.txt` is explicitly unapproved; the Owner must personally review, accept, and save that exact text outside the installed skill before it can be used as the E10 comparison source.
- This mission did not capture host-observed successful native `$council-flow` invocation or skill-attributed delegation for E1/E2. A local CLI login and separate role sessions in this mission do not establish those frozen observations.
- The host did not expose effective loaded custom-agent TOML identity for E4. Visible role labels or these mission's agent-type selections are not proof of loaded configuration.
- The Owner must open a new authenticated local Codex session at the prepared disposable workspace and submit exactly one initial instruction: `$council-flow` followed by the personally accepted, saved fixture text. Do not paste the skill or add a spawn instruction. The Owner performs zero courier interventions after submission.

Only after those prerequisites are genuinely established may the separate frozen observation begin. This preparation label is not a Gate 3 PASS and does not change any E1-E10 status.
