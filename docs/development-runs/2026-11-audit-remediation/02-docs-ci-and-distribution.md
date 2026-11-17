# Slice 02 | Consistent documentation, CI and distribution hygiene

**Status:** PROPOSED; NOT AUTHORIZED. Requires Slice 01 results and fresh Owner approval.  
**Targets:** AR-04, AR-05, AR-07, AR-09, AR-12. Do not silently expand into runtime work.

## Tasks

1. Correct `AGENTS.md` and `CLAUDE.md` so Claude plugin support is described exactly at its *recorded* maturity: plugin exists; one bounded smoke run recorded; wider compatibility and full Codex activation are not certified. Verify current files first.
2. Make CI run for the intended protected release branch (including push-to-`main`) and relevant PRs. Confirm the actual maintained suite list in `RELEASE.md`; include `demo/gate3-demo` if still maintained. Protect both release package formats and SHA sidecars, with non-mutating tests.
3. Assess Linux/macOS compatibility as a **separate scope decision**: don't promise all-platform support based on Windows tests. Add matrix jobs only if useful and consistent with supported platforms.
4. Remove ambiguity in Manager persistence of Claude subagent `job.report`: Manager may persist verbatim messages with provenance, never invent or edit the subagent's assertions. Resolve using the frozen authority chain and exact host mechanics, not assumptions.
5. Make old `docs/gate3/current-implementation-gaps.md` visibly historical by linking its baseline SHA and current authority. Do **not** rewrite original findings as if they were current.
6. Licensing is an **Owner gate**. A repository with no LICENSE and a plugin marked UNLICENSED must not be automatically assigned MIT, Apache-2.0 or another license. Present options and implement only the Owner's chosen grant.

## Acceptance gate

- [ ] New user-facing host descriptions agree with current `README.md` and `RELEASE.md` without upgrading unverified results.
- [ ] Intended CI triggers and all selected test/build jobs are actually configured; successful checks and artifacts are observable.
- [ ] CI tests don't mutate tracked release artifacts; both packages are checked.
- [ ] Report authorship provenance and exact allowed Manager persistence are unambiguous.
- [ ] Historical artifacts are preserved.
- [ ] License chosen by Owner or explicitly remains UNLICENSED; no inferred permission grant.

## Run record

- Status: NOT AUTHORIZED
- Starting SHA / branch:
- Owner decisions (CI supported OSes; license; publishing):
- Files changed:
- CI and package evidence:
- Remaining gaps:
- Commit / push / PR / merge:
- Owner decision / next action:
