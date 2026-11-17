# CouncilFlow Mission control

Optional offline, read-only observer for the existing CouncilFlow skill. No live connection, hooks, agent dispatch, approvals, host configuration changes, persistent backend, paid API, or production dependency. The canonical skill and release builder are unchanged; this directory is not added to the skill ZIP.

## Run locally

From the repository root, using Python 3:

```powershell
python -m http.server 4173 --bind 127.0.0.1 --directory dashboard
```

Open **http://127.0.0.1:4173/** in a modern browser. Stop the temporary static-file server with Ctrl+C. No npm install or build is needed. Serve only this directory, not private host records. Opening index.html with file:// is not supported because browser module policies differ.

## Explore and import

The initial scenario is synthetic and visibly labeled **DEMO DATA**. Scenario selection includes review, failure, interrupted state, empty project, and a long-title/1,000-event stress example. No timer generates events, changes progress, or animates agent activity.

Choose **Import run JSON**, then select a sanitized JSON projection using `view_schema: "councilflow-dashboard-view/1"`. The files in `fixtures/` are importable examples. Imported data stays in browser memory; reload clears it. Switching back to an imported run restores that exact snapshot. Failed imports preserve the prior run. There is no automatic host-log conversion or transcript scraping.

Use the candidate selector to inspect historical attempts. The acceptance fraction and evidence/console follow the selected candidate; the run phase and role desk remain the latest imported snapshot. Expand role cards and events, filter role/category, and open a criterion, verification row or resource metric for details. Escape closes the evidence drawer and restores focus. The theme button toggles local light/dark rendering without persistence.

## Presentation format and trust

See [FORMAT.md](FORMAT.md) and `projection.mjs`. This is a separate presentation format, not the council-flow 1.0 wire contract. `parseSnapshot(text)` validates the closed format; `project(snapshot, attemptId, now)` rebuilds display progress from its preserved criteria, attempts and evidence. Rebuilding never edits the original records. The pure projection accepts an explicit time for reproducible freshness tests.

All six provenance labels are supported: Host-observed, Structurally validated, Execution evidence, Agent-reported, Derived, Synthetic demonstration. **These are supplied assertions, not authenticated observations by this viewer.** In a non-demo import, inspect the original authoritative records independently. Hash equality cannot establish semantic correctness; role names cannot establish native host identity. Even a complete imported acceptance chain is not an independent CouncilFlow verification run.

Final acceptance requires unique original criterion IDs, an original-criteria reference, the selected candidate/attempt, passed contract and source-fidelity records, Worker evidence, Tester execution, Reviewer comparison, a matching command/exit/stdout-hash rerun and an accepted Planner decision. Known failed/rejected/unverified evidence for that criterion/attempt suppresses acceptance even if omitted from the result's references. Intermediate stages never increase acceptance. No original criteria means **Not assessable**. Earlier acceptance is not inherited by a new attempt.

Elapsed duration ends at the last observed timestamp. A missing timestamp or observation older than 15 minutes produces a **stale heuristic**, not a crash diagnosis. Recorded active does not imply current process activity. Model IDs and counters are displayed only as supplied. Missing metrics show **Not reported**. Token counters need a scope/attribution note; per-role counts are never automatically summed, and no cost or ETA is invented.

## Limits and input safety

- UTF-8 JSON, at most 2 MiB, nesting at most 16, 200 original criteria, 50 attempts, 2,000 evidence records, 5,000 events and 100 blockers. Timeline rendering pages 50 events at a time.
- Unknown versions/fields, duplicate keys (including escaped duplicates), duplicate identities, invalid enums/timestamps/counters, unknown references and cross-candidate evidence fail closed.
- Imported strings use textContent, never HTML/Markdown. A restrictive CSP disables network connections and arbitrary script execution. References, commands and path-like strings stay inert; the viewer never follows them, resolves symlinks, opens artifacts or executes commands. Explicit file import reads only the selected file's bytes. Input JSON must already be sanitized; the viewer cannot discover secrets hidden in an allowed caption.
- Snapshot provenance and source completeness cannot be authenticated. Original criterion references are opaque labels, not fidelity proofs. No live host adapter, real billing, validated per-role telemetry, or automatic native message projection has been demonstrated.
- Tested on Windows-local Edge/Chromium; Firefox, Safari, assistive-technology behavior and full WCAG conformance remain unverified. Automated keyboard/focus and reduced-motion smoke tests are narrower than an accessibility certification.
- No screenshot or runtime evidence here is Codex Cloud evidence. Fixture counters, candidate names, test summaries and evidence hashes are synthetic.

## Tests

```powershell
node --test dashboard/tests/projection.test.mjs
python -m unittest discover -s tests -v
```

UI smoke checks require Playwright CLI and local Edge; they are development tools, not runtime dependencies. With the static server running:

```powershell
npx --package @playwright/cli playwright-cli -s=council-dashboard open http://127.0.0.1:4173 --browser=msedge
npx --package @playwright/cli playwright-cli -s=council-dashboard run-code --filename=dashboard/tests/browser-smoke.cjs
npx --package @playwright/cli playwright-cli -s=council-dashboard close
```

This session used @playwright/cli 0.1.24 and the installed Edge. On this machine Node needed `NODE_OPTIONS=--use-system-ca` to trust the system CA when obtaining the CLI; certificate verification was not disabled. See [evidence/verification.md](evidence/verification.md) for observed results and screenshots. No screenshot tests are part of the canonical Python package suites.

## Remove

Stop the temporary static server, close its tab and remove `dashboard/` plus the associated optional docs if desired. Reload/close clears imported data; no browser storage or host settings were written. The dashboard is outside the release builder's source allowlist and CouncilFlow's skill directories. Neither installation nor removal requires editing the workflow, contracts, policies or native role configuration.
