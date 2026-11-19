# P2 model override capability handoff

**Disposition:** `NATIVE_OVERRIDE_ARGUMENT_DOCUMENTED; CAPABILITY_QUERY_UNSUPPORTED; EFFECTIVE_ROUTE_UNVERIFIED; NO_ADAPTER`

This note records the narrow behavior available to this execution environment. The native collaboration tool accepts a per-delegation `model` option. Its declared argument shape is `spawn_agent({ task_name, message, fork_turns, model })`; when `model` is supplied, `fork_turns` must be `"none"`. The tool metadata documents that argument restriction, but does not document capability discovery, supported-model enumeration, route identity, effective model attestation, usage or billing evidence, or a stable error taxonomy.

The generic Codex CLI `--model <MODEL>` option is also documented, but that option alone cannot prove a role-specific capability or which model actually handled a task. A request value and an effective route are distinct facts.

## Contract for any future adapter

1. Keep preference, requested override, capability evidence, and observed effective route as separate fields. Missing capability or route evidence remains `UNKNOWN`/`UNVERIFIED`; the default is inherited host routing.
2. Discover capability only through a documented host API whose returned identity/version and error behavior can be bound to a task record. Do not infer availability from a successful request, UI label, generic CLI option, or caller claim.
3. Record request errors as request failures, never as evidence that a model is unsupported or that the host selected a fallback. Preserve unknown error semantics as unknown.
4. Do not configure host defaults, select a model, or make provider calls as part of this handoff. A future adapter needs its own scoped implementation plan, host/version evidence, error contract, offline fixtures, independent tests, and a separately authorized native qualification card with explicit call/spend bounds and stop control.
5. Until that contract is met, `resolve_role` continues to inherit the host and returns no effective model or verified route claim.

## Evidence and limits

Observed for this plan on 2026-11-19: the `collaboration.spawn_agent` schema accepts optional `model`; its tool description requires `fork_turns="none"` with a model override. Codex CLI help exposes a generic model option. No capability query or effective-route evidence is documented in the available interfaces. Claude CLI is absent. No model override or native model request was run. The actual route, fallback behavior, error semantics, usage, and spend remain unverified.
