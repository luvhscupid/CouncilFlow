# Automatic Codebase Memory lifecycle

Manager performs this lifecycle before Planner for every `$council-flow` request,
and again after implementation or rework once Worker has stopped edits. The Owner
supplies the coding goal only. Codebase Memory is a native tool capability within
the existing workflow; it adds no role, helper, manifest, or memory database.

## 1. Inspect local content before MCP discovery

Read repository instructions and inspect the authorized root with ordinary file
listing/search and relevant source reads. Use the actual project tree rather
than a file-extension guess: documentation or assets can be meaningful source.
An empty directory or one containing only CouncilFlow installation files makes
**zero MCP calls**, including project listing and index status. CouncilFlow
installation files are `.agents/skills/council-flow/` and the four
`.codex/agents/council-*.toml` definitions; VCS metadata and generated caches do
not by themselves constitute a project. Continue normal project creation.
After meaningful source exists, apply the remaining steps when indexing is
useful. Do not create an index merely for an empty installation.

## 2. Discover the actual capability and bind the project

For relevant existing-project work, Manager automatically inspects the MCP tools
actually exposed by Codex. A configured server is not proof of availability:
absent tools, failed startup/handshake, and unreachable servers take the direct
inspection fallback below. Read the supported input/output schemas before calls;
use observed names and interfaces rather than guessing arguments.

Only the Codebase Memory MCP namespace qualifies. For example, Codex app's
`mcp__codex_app__list_projects` lists app projects and is not this capability.
When the actual server exposes `list_projects`, use its observed project `name`
only when the resolved `root_path` equals the authorized repository root exactly.
A parent path alone never establishes project identity. For a task within a
subdirectory, resolve the authorized repository root from local source/native
metadata; a nested repository has its own identity. If the API cannot establish
the exact root, use direct inspection; never choose a similarly named sibling or
assume the folder name is the server project name. Use the exact absolute root
as project identity only if the exposed interface supports it.

For an existing index, inspect the actual `index_status` or equivalent supported
status. For a missing index, use the exposed indexing operation (such as
`index_repository`, only when present) on the authorized root when useful for the
task. Small or unsupported scopes can use direct inspection with that reason
reported. Record the actual project identity and returned generation/status;
an indexing request alone does not prove a completed or current index.

## 3. Establish freshness before graph reliance

On returning, debugging, patching, or upgrading, inspect current source changes
and use the server's exposed status/change-detection capabilities to establish
whether the index covers that source. Use `detect_changes` only according to its
actual semantics; a Git-impact result or clean Git diff alone does not prove
index freshness, including untracked files. Refresh stale information through
the supported indexing/update operation before using remembered relationships.
Check the resulting status/generation and relevant coverage after completion.

If freshness is pending, stale, unknown, unsupported, or a refresh fails, inspect
the affected source and dependencies directly. Report the limitation; do not
present the stale graph as verified knowledge or build a replacement hash system.

## 4. Retrieve bounded context and pass it to fresh agents

Choose task-relevant scope and the installed Codebase Memory skill's evidence
tier where available. Use exposed graph tools for exact symbols, files,
dependencies, and architecture: for example `search_graph`, `trace_path`,
`get_code_snippet`, or `get_architecture` only when actually present. Bound result
sizes and trace depth, follow relevant result pages, and avoid full-project dumps
or repeated identical queries while project generation and scope are unchanged.

Once evidence paths are known, use `check_index_coverage` once for all those paths
when exposed; include relevant scopes for negative or exhaustive claims. Read
critical source directly. Follow partial, skipped, excluded, stale, pending, or
unknown coverage with direct reads/search of the reported ranges and dependencies.
If coverage tooling is unavailable, directly check every material source claim
and disclose the limit. A clean coverage response is not proof of completeness.

Manager supplies fresh Planner, Worker, Tester, and Reviewer sessions only the
bounded findings each needs: exact project/root and source revision or working
tree state, index generation/freshness, paths, qualified symbols, relevant edges,
query scope and pagination, coverage gaps, source reads already performed, and
unresolved uncertainty. Reuse these findings while still current. Put text in
existing task `instructions` or referenced evidence artifacts through
`evidence_refs`; keep the closed communication schema unchanged. Do not assume
children inherit MCP access. A child without tools uses the supplied evidence
and reads the referenced source, especially coverage gaps, without claiming a
live MCP call.

## 5. Synchronize resulting source and preserve verification

After Worker stops edits, Manager checks resulting source changes and the exact
project's actual index status. Reuse a confirmed current generation when no
relevant source changed. Otherwise Manager creates or updates the index through
the available supported indexing/update operation, then checks status and relevant
coverage. Repeat after fresh-Worker rework and after a new project gains
meaningful source. Do not refresh in parallel with implementation edits or treat
a request, successful tool exit, or old generation as proof of source coverage.
If the API cannot establish synchronization, report that limit and use direct
source inspection for the resulting candidate.

Keep Planner, Manager, Worker, independent Tester, Reviewer, and final Planner
responsibilities and frozen acceptance unchanged. Graph findings are navigation
and context evidence, not correctness proof or permission authority. Independent
tests, Reviewer comparison/rerun, and Planner acceptance remain required.
Index creation/refresh stays within the Owner-authorized project and inherited
native permissions. Do not install, replace, or reconfigure a server, change
global settings, delete other indexes, or use unrelated mutating MCP operations.

## Direct inspection fallback and reporting

When the capability is missing, configured but unreachable, stale, incomplete, or
cannot express the required operation, continue ordinary CouncilFlow using local
search, source reads, and existing independent checks. No mandatory manual
initialization or extra Owner command is required. Report which tools were
actually available/called, the exact project/status, source fallback, and gaps.
Live MCP integration is UNVERIFIED when it cannot be observed. Static instruction
tests do not prove automatic activation, live graph behavior, or role independence.
