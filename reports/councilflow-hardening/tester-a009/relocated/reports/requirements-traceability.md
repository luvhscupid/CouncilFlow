# CouncilFlow restoration requirements traceability

Source: current explicit Owner restoration instruction §§1–14 and the preserved
five-role workflow. No authoritative v0.2.1 schema exists in the inspected tracked
sources. `council-flow` version `1.0` is the Owner's skill-level fallback contract,
not the trusted ACP Supervisor. Original REST-P001 plan/hash is unchanged.

Layers below are separate: **S** specified, **I** implemented, **SV** statically
validated, **D** dynamically tested, **N** observed in actual native role activity,
**B/U** blocked or unverified. PASS applies only to the named observation, never
as an override of missing native activation. The original Planner's final map
and Manager closeout preserve these distinctions.
Skill-relative paths below begin at `.agents/skills/council-flow/`.

| Requirement / explicit source | Implementation | Actual verification and layer/status | Remaining limitation |
|---|---|---|---|
| C01 / §§3A,7,8: versioned JSON for all five AI roles and eight purposes | `references/message-contract.json`, `references/communication.md`, `scripts/contracts.py`; SKILL/all role instructions | S/I/SV PASS; D valid/invalid fixtures; N actual Planner/Manager/Worker/Tester/Reviewer JSON packets in `reports/restoration/messages/`, accepted order in `live-order.json` | Approval vocabulary is tested with labeled synthetic fixtures; no unnecessary actual Owner approval invented |
| C02 / §3B.1–5,11: strict protocol/version, fields/types, no duplicates/nonfinite/unknowns/bool integers | `loads`, `_object`, `validate_message`, referenced-plan guards | D PASS in 39 focused contract methods and independent suites; malformed sequence/bindings/optional fields/plan contexts B01–B07 fixed; final Tester rerun103 PASS | Controlled file/API boundaries, not opaque native transport |
| C03 / §3A–B.6–7,12: role/type/origin and Owner authority | `ROUTES`, closed payloads, expected sender/bindings, Owner provenance and oracle checks; YAML authority | SV/D PASS; actual externally observed native role bindings validate; spoofed role/Manager/Owner decisions and oracle substitution reject | Structural checks do not authenticate sender; actual origin and Owner facts are external inputs |
| C04 / §3A–B.8–9: IDs, causal refs, immutable plan/task/attempt/candidate/evidence | `validate_sequence`, `artifact`; original plan and actual packet files | D/N PASS for accepted actual causal round with root hashes; mutated predecessor/candidate/attempt/criteria/origin reject; original plan hash retained | Bootstrap and rejected interim packet are preserved separately, not migrated into successful history |
| Bounds / §3B.10: explicit sizes/nesting | constants and strict parsers | D PASS: 65536 UTF-8 bytes/message,16 containers,128 entries/container,8192 ordinary-string chars,128 ID chars,1024 path chars; context at most1024 messages | Limits validate supplied records; no persistent resource-enforcement runtime |
| C05 / §4: versioned YAML roles, Owner decisions, autonomy, context and retries | `policies/roles.yaml`, `parse_policy`, `validate_policy` | SV/D PASS: five AI roles plus human Owner, original order, only Worker implementation, independent verification/review; productive rework has no lifetime cap | Two-space mappings/JSON-compatible scalars and string lists only; unsupported YAML rejected; not a general parser |
| Retry/security policy / §4 | YAML resources/security; recovery.md | SV/D PASS: infrastructure retries3, crash recoveries2, both explicitly instruction-only; no OS grants, transport or sender-authentication claim | No runtime retry/crash accounting or security sandbox is implemented |
| C06 / §4 native format | `.codex/agents/council-*.toml`; YAML native mapping | SV PASS: four exact supported name/description/developer_instructions string definitions; current native CLI schemas/help inspected; N actual native delegation works | U: live selection/loading of the custom-role files; role-instruction fallback used |
| C07 / §§6–7: Owner prose, internal JSON/YAML/TOML/JSONL | SKILL, role refs/TOMLs, README/RELEASE | SV PASS; N Owner progress is natural language; separate Reviewer eight actual CLI interactions PASS, no blocking issue; release wording clarified | Internal records are developer artifacts, not an Owner authoring requirement |
| C08 / §§4,8–9: failed mandatory test causes rework | recovery.md, fresh `demo/structured-flow/`, REST-M011/M012 and REST-M014/M015 | N PASS: real initial sum failure and independent validator failures rejected; three fresh Workers across REST-A001/A002/A003; independent retests now pass | Earlier failed logs/snapshots retained; old receipt is regression, not counted as this fresh demo |
| C09 / §§3A,7–8: independent candidate-bound evidence and original Planner check | candidate/input refs, mandatory Tester oracle_ref, Reviewer observations, evidence-based decisions, original plan.check | D/N PASS on candidate003: distinct Tester/Reviewer, Manager REST-M018 acceptance and original Planner REST-PLAN-FINAL-001 all16-criteria map; passed results require explicit evidence | Structural validation cannot establish semantic truth or native sender authentication |
| C10 / §§1–2,8: no new platform/infrastructure | installed stdlib helper and native skill/agent files | SV PASS: stdlib-only imports; D relocated helper/policy/message/context checks PASS; no installation, database/server/provider/API key introduced | Native Codex remains required for actual AI roles |
| C11 / §§2,8,11: original functionality | unchanged receipt/CSV/starter and prior tests | D PASS: all45 previously passing checks retained; actual receipt Rp103,000; current sum4; final full run103 methods,0 unexpected failed suites,0 skips | Old two-test starter has one deliberate baseline failure and is excluded from passing counts |
| C12 / §8: genuine negative-control sensitivity | `tests/test_contracts.py`; two independent test modules; actual packet mutations | D PASS after B01–B07 repairs; 9 final mutations of actual context/events reject; actual partial Planner map rejected for omitted original criteria | Artificial mutations are not counted as new AI sessions; rejected packet remains preserved |
| Diagnostics / §5 | `validate_jsonl`, `events-prefix-001.jsonl`, `events.jsonl` | D/N PASS: twelve actual events validate against known role messages plus actual activation report; event-reference negatives reject | Optional bounded export ≤1MiB/1024 lines; not authoritative/crash-safe ledger; operators must keep secrets/private reasoning out |
| Fresh activation / §§9,12 | `reports/restoration/activation/REST-ACT-REPORT-001.json` and underlying attempt | N fresh corrected skill discovery PASS; real structured explicit input accepted, then native thread systemError/HTTP401; actual returned IDs saved | B/U: no completed invoked inference; custom-role selection unverified; no bypass or repeated identical attempt |
| Permanent traceability/release / §§10–12 | this map, current final.md, corrected dist ZIP/checksum, `restoration/package-verification.json` | I/SV/D/N PASS within correction scope: complete archive/source/safe-path checks, extracted103-test relocation, original Planner map, implementation commit3e23bd8 and final evidence commit at HEAD; all29 tested product files unchanged | Extracted tests used the immutable numbered release snapshot; final archive adds evidence/copy only. Cannot claim COUNCILFLOW_FULLY_VERIFIED from test counts |

## Evidence index and execution limits

- Original baseline: `reports/restoration/baseline/results.json` (45 passing;
  intentional starter separately2 tests/1 expected failure).
- Final independent execution: `reports/restoration/verification/release/suite-results.json`
  and `report.md` (103 tests, zero unexpected failures/skips). The native turn
  hit a usage limit after its complete controlled report was saved; Manager
  validated that genuine report and unchanged candidate on resume. See
  `resume-verification.json`; successful native final-response delivery is not claimed.
- Role/evidence control: `live-order.json`, `live-bindings.json`, native task paths
  in messages; original plan SHA256
  `4ee180ac24876633d62198fc71488ea82df291dcb25e83a657f900329e87f64b`.
- Usability: `reports/restoration/review/report.md` and `commands.json`, eight real
  interactions; artificial unauthorized packet is labeled as a negative control.
- A rejected actual interim Planner packet is retained with
  `planner-interim-rejection.json`; it is not in the accepted live order.
- Original Planner final map: `reports/restoration/planner-final/report.md` and
  `messages/REST-PLAN-FINAL-001.json`; all16 unchanged criteria have evidence.
  The final supplied sequence contains21 messages. Immutable inspected snapshots
  preserve hashes while current release copy reflects completed closeout.
- Communication-correction classification:
  **CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED**, not a new claim that the
  earlier native authentication failure has been repaired.
