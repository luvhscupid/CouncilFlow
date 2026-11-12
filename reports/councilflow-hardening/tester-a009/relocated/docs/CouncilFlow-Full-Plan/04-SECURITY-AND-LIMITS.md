# 04 — Security boundaries and non-negotiables

**The skill is NOT a security kernel.** JSON, YAML, TOML and markdown instructions do not authenticate agents or enforce OS isolation. Native Codex sandbox/permission controls determine effective actions; no model or Manager may grant capabilities to itself.

## Hard prohibitions

- No Windows ACL changes, `takeown`, `icacls`, UAC elevation, privilege bypass, disabling Defender or sandbox changes.
- No modification of existing ACP, Execution Kernel, Codex on Crack or unrelated projects.
- No global Codex configuration/skill overwrite without separate Owner authorization.
- No paid API, new provider, credential scraping, refresh-token extraction, unsafe auto-publishing, or network-required dependencies.
- No unauthorized external writes, deployments, purchases, data releases, or destructive modifications.
- No running untrusted Worker-authored code in a trusted controller context and then claiming isolation.
- No direct access to hidden tests or secret prompts by Worker.
- No claims of exact-once execution or crash proof without actual independently enforced state.

## Rework and approvals

Manager can authorize ordinary in-scope coding repair under initial Owner consent, subject to finite resources and progress. High-risk/out-of-scope actions, weakened mandatory criteria, security policy changes, subjective owner-decision gates and extra purchases require Owner approval. One writer/workspace, isolated parallelism only when available; no unsupported isolation guarantees.

## Known incomplete/unverified items

- Security Annex v1.0-A full original is missing; recovery note is secondary.
- Direct `$council-flow` invocation was blocked by CLI auth in the last report.
- Real custom-agent selection semantics and actual native subagent isolation in Cloud need proof.
- No SQLite Supervisor guarantees are imported into the new CouncilFlow skill; do not claim persisted CAS/idempotent/immutable state from JSONL alone.
- Host-specific environment permissions, model choice and billing must be observed, not assumed.

## Trust boundaries

Owner authority ≠ agent declarations. Planning criteria ≠ Worker self-tests. Tester independent evidence ≠ self-signed completion. Reviewer observation ≠ model imagination. Static parser compliance ≠ native activation. Native discovery ≠ full workflow execution.

On a genuine unsupported feature, finish independent work, label status `UNVERIFIED` or `BLOCKED`, preserve sources and report exact limitations. Never simulate success to meet a target metric.
