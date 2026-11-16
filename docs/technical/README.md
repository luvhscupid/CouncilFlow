# CouncilFlow technical documentation

This is the single index of technical documents in the repository. Start with the
[main README](../../README.md) if you are new to CouncilFlow.

Everything here describes the CouncilFlow workflow skill. CouncilFlow is not a
standalone AI application. Its roles are workflow responsibilities carried out with
the host's models, tools and native delegation.

## Documents

| Document | What it covers |
| --- | --- |
| [Host packages](host-packages.md) | The Codex and Claude Code packages, how each is built, and their verification status. |
| [Claude Code plugin](claude-code-plugin.md) | Loading the plugin, the `/councilflow:run` command, and how the Manager launches plugin agents. |
| [Structured communication](structured-communication.md) | The UTF-8 JSON message format, the validator commands, and their limits. |
| [Codebase Memory context](codebase-memory.md) | How the optional Codebase Memory tool is used for existing projects, and its fallbacks. |
| [Optional efficiency helpers](efficiency-helpers.md) | The opt-in recorder and digest helpers, and their unverified claims. |

## Where authoritative sources live

These technical pages explain the workflow. They do not replace the controlling sources:

- The [Gate 3 Owner Charter](../gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md), existing
  Owner decisions, and frozen specifications keep their authority.
- The normative references, policy and scripts live inside the installed skill at
  [`.agents/skills/council-flow/`](../../.agents/skills/council-flow/SKILL.md).
- [Research proposals](../research/README.md) are non-normative.
- Historical planning material is in [docs/CouncilFlow-Full-Plan](../CouncilFlow-Full-Plan/README.md),
  and the Gate 3 record is in [docs/gate3](../gate3/README.md).

## Release and evidence

- [RELEASE.md](../../RELEASE.md): package contents, portability and release checks.
- [Requirements traceability](https://github.com/luvhscupid/CouncilFlow/blob/9c59bc3d0f98a818b01ad14d0165d92b236105b0/reports/requirements-traceability.md) and
  [final report](https://github.com/luvhscupid/CouncilFlow/blob/9c59bc3d0f98a818b01ad14d0165d92b236105b0/reports/final.md): what has been observed and what remains unverified.
