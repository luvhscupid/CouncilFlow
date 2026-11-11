# Codex format and capability inspection

Date: 2026-11-11. Scope: `/workspace/CouncilFlow` only. This research did not inspect credentials, user configuration, old projects, or existing skill installations.

## Observed locally

- `codex --version`: `codex-cli 0.167.0-alpha.4` (exit 0).
- `codex --help`: native CLI available; lists `exec`, `app-server`, `debug`, and `agents` (exit 0).
- `codex exec --help`: supports `--ephemeral`, `--json`, `--ignore-user-config`, `--cd`, and stdin prompt (exit 0). Availability does not establish authenticated inference.
- `codex app-server --help`: supports stdio transport and schema generation (exit 0). No server was started by this research agent.
- `codex debug prompt-input --help`: renders model-visible prompt input JSON, accepts a prompt (exit 0). No prompt rendering or actual workflow invocation was attempted by this research agent.
- This agent itself was created through the native collaboration API as `/root/format_research`; it is a real independent documentation-research session, not a simulated CouncilFlow role.

## Current official format

Source: https://developers.openai.com/codex/skills/

- Repository skill discovery scans `.agents/skills` from current working directory to repository root.
- Each skill has `SKILL.md` with required YAML frontmatter `name` and `description`.
- Explicit activation: include `$skill-name` in a Codex CLI/IDE prompt; `/skills` and `$` selector also expose available skills. ChatGPT's mention UI differs.
- Optional `agents/openai.yaml` supports `interface.display_name`, `interface.short_description`, `interface.default_prompt`, and `policy.allow_implicit_invocation`. Setting the latter false preserves explicit invocation.
- Skill changes usually reload automatically; restart if updates do not appear.

Source: https://developers.openai.com/codex/subagents/

- Current standalone project agent definition location: `.codex/agents/*.toml`.
- Every standalone custom agent file must define string keys `name`, `description`, and `developer_instructions`.
- `model` and `model_reasoning_effort` are optional. Omit them to avoid selecting unavailable models and inherit current configuration.
- Custom agents inherit parent permissions, provider, and MCP servers; files cannot override these security boundaries.
- The Manager is the parent; four standalone role files suffice. No new config registration is required by this standalone format.
- Older config-layer declarations (`[agents.<name>]` with `config_file`) are also documented, but not needed for the standalone deliverable.

The companion `*-official-extracts.md` files contain excerpts fetched from these URLs during this run. Documentation evidence is distinct from live discovery/invocation evidence; neither CLI help nor TOML parsing establishes successful agent loading or execution.

## Remaining runtime proof

Actual `council-flow` discovery, explicit invocation, custom-agent loading, and the demo workflow require separate observed evidence after product creation. This research grants none of those a pass. No global configuration or permission policy was changed.

## Additional containment diagnostic

No `codex exec` or `codex debug prompt-input` was launched by this research agent.

Official reference https://developers.openai.com/codex/config-reference/ documents these local CLI keys:

- `log_dir`: directory for Codex logs (explicit value also enables plaintext TUI log).
- `sqlite_home`: directory for SQLite-backed state used by agent jobs/resumable state.
- `history.persistence = "none"`: disables history.jsonl transcript saving.
- `cli_auth_credentials_store = "ephemeral"`: uses in-memory credential cache, but may affect authenticated startup and is not a substitute for authorized provider configuration.

These keys are command-line `-c` overrides and do not require editing global configuration. The reference explicitly warns local paths do not relocate managed cloud storage/logs when used as managed cloud overrides.

Official source inspected in memory: https://raw.githubusercontent.com/openai/codex/main/codex-rs/cli/src/main.rs (`run_debug_prompt_input_command`). Current upstream code sets `ephemeral: Some(true)` and calls `build_prompt_input` with `state_db: None`. It also initializes `ConfigBuilder`, `AuthManager::shared_from_config`, `CodexHomeUserInstructionsProvider`, and the skills extension. This source inspection supports the command's prompt-rendering purpose and ephemeral intent; it does not prove the installed binary will perform no filesystem writes outside the repository or skip existing user skills/instructions. Upstream main is not asserted to match the installed alpha binary exactly.

No documented combination of the above keys establishes complete containment of all Codex-home files without repurposing CODEX_HOME. Because the governing developer instruction prohibits repurposing that environment variable, a fully repository-contained separate CLI invocation remains unverified. Native session skill discovery and collaboration APIs can still be exercised independently. This diagnostic is not a passing runtime discovery/invocation test.

## Native discovery and invocation diagnostic follow-up

The Manager reported a successful process-local mount namespace experiment: global root read-only, repository writable, and a repository-owned temporary Codex-home directory mounted over the unchanged normal home path. No CODEX_HOME environment-variable assignment or credential copying was needed. This resolves the earlier unverified containment approach through actual filesystem isolation; see the Manager's runtime evidence for the exact command/results.

`debug prompt-input` exposing only bundled skills does not establish that `$council-flow` is unsupported: rendering context is not the same as submitting an actual skill turn. Upstream repository-root resolution is handled through filesystem accessors, and different debug/host/executor paths can expose different catalogs. No definitive cause is assigned solely from that symptom.

Official app-server documentation: https://developers.openai.com/codex/app-server/

Stable handshake/request example:

```json
{"id":0,"method":"initialize","params":{"clientInfo":{"name":"councilflow_validation","title":"CouncilFlow validation","version":"1.0"}}}
{"method":"initialized","params":{}}
{"id":2,"method":"skills/list","params":{"cwds":["/workspace/CouncilFlow"],"forceReload":true}}
```

The list response has `result.data[]`, each with `cwd`, `skills`, and `errors`; each skill includes `name`, `path`, `enabled`, and `scope`. A repo-scoped enabled result for council-flow establishes native discovery more directly than prompt rendering.

After a real `thread/start`, documented explicit invocation submits a `turn/start` with both text and a structured skill item:

```json
{"id":101,"method":"turn/start","params":{"threadId":"<actual returned thread id>","input":[{"type":"text","text":"$council-flow Complete the offline receipt calculator demonstration."},{"type":"skill","name":"council-flow","path":"/workspace/CouncilFlow/.agents/skills/council-flow/SKILL.md"}]}}
```

The documentation recommends the structured item so the server injects full skill instructions. Without it, the model can resolve the text marker itself. No thread id in this example is represented as an actual runtime identifier.

Exact installed protocol schemas can be generated with the CLI's documented `codex app-server generate-json-schema --out <repository-directory>` command; this avoids relying on moving upstream types. Upstream `SkillsListParams.json` currently documents `cwds` and `forceReload`; the website also discusses optional `perCwdExtraUserRoots`, so installed schema should decide optional fields. Extra root injection would not prove default repository discovery and should not be conflated with it.

This follow-up is documentation guidance. The research agent did not launch app-server, prompt-input, or inference.
