# Dashboard Review Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the verified review findings on the CouncilFlow run dashboard, and make the dashboard look good. The council workflow itself is not changed by any task here.

**Status (2026-11-20):**
- Task 1: complete. Baseline recorded: 26 Python tests and 22 Node tests pass.
- Task 14: applied to `styles.css` in the working tree, not yet committed. Node and Python suites pass. Not yet checked in a browser.
- Tasks 2 to 5: not started.
- Tasks 6 to 13: not started. Tasks 8 to 13 are cosmetic and optional under owner direction.
- Working tree: `styles.css` modified and the plan file untracked. Nothing has been committed.

**Architecture:** The dashboard is a read-only static view made of `.agents/skills/council-flow/dashboard/{index.html,styles.css,run-reader.js,app.js}` and the publisher `.agents/skills/council-flow/scripts/dashboard.py`. Fixes stay inside those files and their tests. No new runtime, service, or dependency.

**Tech Stack:** Python 3 (stdlib, pytest for the Python tests), Node.js built-in `node --test` for the browser-logic tests, plain HTML/CSS/JS.

**Spec:** None. This plan follows the 2026-11-20 review of branch `codex/councilflow-review-followup` (HEAD `e2cb336`) and the antislop audit of the dashboard. Findings are listed in the Review Focus section below.

## Global Constraints

- Do not change any frozen Gate 3 record under `docs/gate3/` or any file under `dist/` unless a task says so.
- Do not add dependencies. Python stays stdlib-only. Node tests use `node --test`.
- Dashboard UI text must not contain an em dash (R-02).
- Do not modify `.councilflow/runs/` evidence.
- Preserve unrelated local edits. Commit only the files a task names.

## Review Focus

1. A `plan.publish` packet with no `plan_ref` makes `run-reader.js` read `reference.path` on `undefined`. Expected: the run shows a recorded `missing_plan` or `invalid_plan_reference` issue, not an exception. Pinned by Task 2.
2. `app.js` calls `showFiles(run.files)` on the embedded path without `await` or `.catch()`. Expected: any reader failure shows an incomplete run, not a stuck loading message. Pinned by Task 3.
3. `publish_run` creates the run directory before the symlink and containment check. Expected: a symlinked or escaping task directory is refused before anything is created. Pinned by Task 4.
4. `pytest` is not installed in the review environment, so the three Python test files have no recorded result. Expected: a recorded pass or fail for each. Covered by Task 1.
5. The `.button` control is 42px tall, below the 44px tap target in R-03. Expected: every enabled button is at least 44px on touch layouts. Pinned by Task 5.

## Task 1: Record a clean Python test baseline

**Files:**
- Test: `demo/dashboard/tests/test_publisher.py`, `tests/test_release.py`, `tests/test_skill_files.py`

**Interfaces:**
- Consumes: none
- Produces: a recorded baseline result, written to `docs/superpowers/plans/2026-11-20-dashboard-baseline.txt`

- [ ] **Step 1: Install pytest into the user Python environment**

Run: `python -m pip install pytest`
Expected: `Successfully installed pytest-...`

- [ ] **Step 2: Run the three Python test files**

Run: `python -m pytest demo/dashboard/tests/test_publisher.py tests/test_release.py tests/test_skill_files.py -q`
Expected: all tests pass. If any fail, record the test names and the error text in the baseline file. Do not fix them in this task.

- [ ] **Step 3: Record the baseline and commit**

Write the exact command, the pass and fail counts, and any failure text into the baseline file.

```bash
git add docs/superpowers/plans/2026-11-20-dashboard-baseline.txt
git commit -m "docs: record dashboard python test baseline"
```

## Task 2: Handle a missing plan reference without throwing

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/run-reader.js:279-291`
- Test: `demo/dashboard/tests/run-reader.test.cjs`

**Interfaces:**
- Consumes: `buildSnapshot(input)` as it exists
- Produces: unchanged `buildSnapshot` signature. A `plan.publish` with no `plan_ref` adds an issue with code `missing_plan_reference`, and the snapshot has `valid: false`.

- [ ] **Step 1: Write the failing test**

Add a test to `run-reader.test.cjs` that builds a valid `plan.publish` packet whose payload has no `plan_ref`, plus one selected plan file, and asserts that `buildSnapshot` returns without throwing, that `issues` contains an entry with `code === "missing_plan_reference"`, and that `valid === false`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/run-reader.test.cjs`
Expected: FAIL with `TypeError` reading `path` of `undefined`.

- [ ] **Step 3: Guard the reference in `run-reader.js`**

Before the `plans.find` call at line 281, if `reference` is not an object with a string `path`, record `missing_plan_reference` and skip the plan lookup. Keep the existing branch order for the other issue codes.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/run-reader.test.cjs`
Expected: PASS, including the new test. All previously passing tests still pass.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/run-reader.js demo/dashboard/tests/run-reader.test.cjs
git commit -m "fix: report missing plan reference instead of throwing"
```

## Task 3: Surface errors from the embedded-run path

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/app.js:379`
- Test: `demo/dashboard/tests/auto-connection.test.cjs`

**Interfaces:**
- Consumes: `showFiles(items, loadingMessage)` as it exists
- Produces: on failure, the embedded path calls `showIncompleteRead(error)` and clears the loading message.

- [ ] **Step 1: Write the failing test**

In `auto-connection.test.cjs`, add a case where the embedded `councilflow-run-data` contains `files` whose reader call throws. Assert the loading message is cleared and the connection state shows "Dashboard data is invalid" or the incomplete-run state, not "Reading current run packets".

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/auto-connection.test.cjs`
Expected: FAIL, the loading message stays visible.

- [ ] **Step 3: Handle the promise**

Change the call at line 379 to `showFiles(run.files).catch(showIncompleteRead)`. Keep the existing `setConnection` call after it.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/auto-connection.test.cjs`
Expected: PASS, all cases.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/app.js demo/dashboard/tests/auto-connection.test.cjs
git commit -m "fix: handle reader failures on the embedded run path"
```

## Task 4: Validate the task directory before creating it

**Files:**
- Modify: `.agents/skills/council-flow/scripts/dashboard.py:189-198`
- Test: `demo/dashboard/tests/test_publisher.py`

**Interfaces:**
- Consumes: `publish_run(root, task_id, *, open_browser, opener)` as it exists
- Produces: unchanged signature. A task directory that does not exist is no longer created when the path is unsafe.

- [ ] **Step 1: Write the failing test**

Add a test that creates a symlink or junction at `.councilflow/runs/<task>` pointing outside the root, calls `publish_run`, and asserts it raises `ValueError` and that no directory was created at the target.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest demo/dashboard/tests/test_publisher.py -q -k symlink`
Expected: FAIL, or the test is skipped on this platform. Record which.

- [ ] **Step 3: Reorder the checks**

Move the `mkdir` call after the `is_symlink` and `is_relative_to` checks. When the directory does not exist yet, check its parent instead.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest demo/dashboard/tests/test_publisher.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/scripts/dashboard.py demo/dashboard/tests/test_publisher.py
git commit -m "fix: validate run directory before creating it"
```

## Task 5: Raise the button tap target to 44px

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/styles.css:101-108` (the `.button` rule)
- Test: none. Verify by measurement in Task 7.

**Interfaces:**
- Consumes: none
- Produces: `.button` has `min-height: 44px`.

- [ ] **Step 1: Change the rule**

Set `min-height: 44px` on the base `.button` rule (`styles.css:102`), so every width meets R-03, including 561px to 820px. Remove the redundant `.button` override inside the 560px query (`styles.css:275`).

- [ ] **Step 2: Verify the value**

Run: `grep -n "min-height: 44px" .agents/skills/council-flow/dashboard/styles.css`
Expected: one match inside the `.button` rule.

- [ ] **Step 3: Commit**

```bash
git add .agents/skills/council-flow/dashboard/styles.css
git commit -m "fix: meet 44px tap target on dashboard buttons"
```

## Task 6: Decide the auto-refresh mechanism (owner decision)

**Files:**
- Modify (after decision): `.agents/skills/council-flow/scripts/dashboard.py:182`

**Interfaces:**
- Consumes: none
- Produces: either the meta refresh is kept with a recorded reason, or it is removed and `test_publisher.py` is updated to expect its absence.

- [ ] **Step 1: Ask the owner**

Ask whether the 2-second `<meta http-equiv="refresh">` in the published snapshot is intended. The embedded run path already polls through the page itself. The meta tag reloads the whole page every 2 seconds.

- [ ] **Step 2: Apply the answer**

If kept: add a one-line comment at the insertion site stating the reason. If removed: delete the line at `dashboard.py:182`, update `_inline` so its guard no longer checks for `http-equiv`, and update `auto-connection.test.cjs` where it asserts the refresh.

- [ ] **Step 3: Run the tests and commit**

Run: `python -m pytest demo/dashboard/tests/test_publisher.py -q` and `node --test demo/dashboard/tests/auto-connection.test.cjs`
Expected: PASS.

```bash
git add .agents/skills/council-flow/scripts/dashboard.py demo/dashboard/tests/
git commit -m "fix: resolve dashboard auto-refresh mechanism"
```

## Task 7: Record the click-through and the palette reason (antislop evidence)

**Files:**
- Create: `docs/superpowers/plans/2026-11-20-dashboard-delivery-gate.md`

**Interfaces:**
- Consumes: the rendered dashboard from `dashboard.py publish --task-id <id>`
- Produces: a PASS/FAIL report that satisfies the antislop Delivery Gate (R-35, R-29, R-31)

- [ ] **Step 1: Run the dashboard**

Run: `python .agents/skills/council-flow/scripts/dashboard.py publish --root . --task-id <an existing run id>` and open the printed `dashboard.html` in a browser.

- [ ] **Step 2: Click every control**

Click each of: Open run folder, Choose message files, Refresh, the wordmark link, and the empty-state buttons. Record the observed result for each, and check the console for errors. Repeat at a phone width and in the reduced-motion setting.

- [ ] **Step 3: Write the palette reason**

In the report, state in one line why each core color and each role hue exists (R-29, R-31). If a hue has no reason, record it as a FAIL and propose merging it.

- [ ] **Step 4: Write the report and commit**

Write the report with one line per control and one line per decision, each PASS backed by the observation. Any FAIL blocks delivery.

Also write one line for the border radius values (R-11): why 9px controls, 15px panels, and the 10 to 16px values exist, or merge them to a three-value scale.

```bash
git add docs/superpowers/plans/2026-11-20-dashboard-delivery-gate.md
git commit -m "docs: record dashboard delivery gate evidence"
```

## Optional tasks (8 to 13): cosmetic, owner direction

The owner has said the dashboard is a viewing surface only and does not affect council behavior, so the antislop gates are advisory here. Tasks 8 to 13 are optional. Execute a task only if the owner says so. Task 11 removes the "Run board" label, which the owner may want to keep.

## Task 8: Replace the sparkle logo with the text name (R-23, R-04)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/index.html:13-16` (the `.wordmark` link)
- Test: `demo/dashboard/tests/antislop-markup.test.cjs` (create)

**Interfaces:**
- Consumes: none
- Produces: the `.wordmark` link contains only the text "CouncilFlow". No `<svg>` and no `.mark` span.

- [ ] **Step 1: Write the failing test**

Create `demo/dashboard/tests/antislop-markup.test.cjs`. Read `index.html` with `fs.readFileSync`, extract the `<a class="wordmark"` ... `</a>` block with a regex, and assert it does not contain `<svg` and that its text content is `CouncilFlow`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: FAIL, the wordmark contains an `<svg>`.

- [ ] **Step 3: Remove the mark**

Delete the `<span class="mark" ...>...</span>` element from the wordmark link. Keep the `<span>CouncilFlow</span>`. Remove the now-unused `.mark` and `.mark svg` rules from `styles.css:82-83`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/index.html .agents/skills/council-flow/dashboard/styles.css demo/dashboard/tests/antislop-markup.test.cjs
git commit -m "fix: replace unconfirmed sparkle logo with text name"
```

## Task 9: Give every enabled link a pointer cursor (R-39)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/styles.css` (base layer, after the `button:focus-visible` rule at line 47)
- Test: `demo/dashboard/tests/antislop-markup.test.cjs`

**Interfaces:**
- Consumes: the test file from Task 8
- Produces: a base rule `a[href], button, summary, select, label[for], [role="button"], [role="tab"], [role="switch"] { cursor: pointer; }` and `:disabled` set to `not-allowed`.

- [ ] **Step 1: Write the failing test**

Add a test that reads `styles.css` and asserts it contains a selector list including `a[href]` with `cursor: pointer`, and a `:disabled` rule with `cursor: not-allowed`.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: FAIL on the new assertion. The Task 8 test still passes.

- [ ] **Step 3: Add the base rule**

Add the selector list above after line 50. Keep `.button` and `.button:disabled` as they are.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: PASS, both cases.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/styles.css demo/dashboard/tests/antislop-markup.test.cjs
git commit -m "fix: set pointer cursor on enabled links and controls"
```

## Task 10: Move raw hex values into design tokens (quality lock)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/styles.css` (the `:root` block at lines 1-34, and each rule that uses a raw hex)
- Test: `demo/dashboard/tests/antislop-markup.test.cjs`

**Interfaces:**
- Consumes: the test file from Task 8
- Produces: every color value outside the `:root` block uses a `var(--...)` token. New tokens get names that describe their role, for example `--surface-sunken`, `--line-strong`, `--warn-surface`.

- [ ] **Step 1: Write the failing test**

Add a test that removes the `:root { ... }` block from `styles.css`, then asserts no `#[0-9a-fA-F]{3,8}\b` match remains.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: FAIL, with the raw hex values listed in the failure message.

- [ ] **Step 3: Add tokens and replace the values**

For each raw value (`#1b1e24`, `#3b3e45`, `#454850`, `#826638`, `#292316`, `#f2d68f`, `#347b68`, `#92e7d0`, `#101216`, `#40444c`, `#444750`, `#565a64`, `#dce1e0`, and any others the test lists), add a role-named token in `:root` and replace the use. Keep the colors the same, so the look does not change.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/styles.css demo/dashboard/tests/antislop-markup.test.cjs
git commit -m "refactor: move dashboard colors into named tokens"
```

## Task 11: Remove the decorative eyebrow label and shorten the intro (frontend-design, impeccable)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/index.html:31-33` (the `run-label` paragraph and the intro copy)
- Test: `demo/dashboard/tests/antislop-markup.test.cjs`

**Interfaces:**
- Consumes: the test file from Task 8
- Produces: no element with class `run-label`. The `h1` stays as the first heading. The `.lede` is kept.

- [ ] **Step 1: Write the failing test**

Add a test that reads `index.html` and asserts it has no `class="run-label"` element and that the `h1` appears before any `section` for workflow content.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: FAIL, the `run-label` element is present.

- [ ] **Step 3: Remove the eyebrow**

Delete the `<p class="run-label">Run board</p>` line and its `.run-label` rule (`styles.css:129`).

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/index.html .agents/skills/council-flow/dashboard/styles.css demo/dashboard/tests/antislop-markup.test.cjs
git commit -m "refactor: remove decorative eyebrow label above dashboard heading"
```

## Task 12: Cap the empty-state height and put the workflow above the fold (impeccable, Operate mode)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/styles.css:148-160` (the `.empty-state` rule)
- Test: `demo/dashboard/tests/antislop-markup.test.cjs`

**Interfaces:**
- Consumes: the test file from Task 8
- Produces: `.empty-state` has `min-height` no greater than 220px. The `.board` workflow panel is the first panel after the intro in DOM order.

- [ ] **Step 1: Write the failing test**

Add a test that reads `styles.css`, extracts the `.empty-state` rule, and asserts `min-height` is at most 220px.

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: FAIL, the value is 310px.

- [ ] **Step 3: Reduce the height**

Change `min-height: 310px` to `min-height: 220px` on `.empty-state`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test demo/dashboard/tests/antislop-markup.test.cjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/council-flow/dashboard/styles.css demo/dashboard/tests/antislop-markup.test.cjs
git commit -m "refactor: reduce empty-state height on run board"
```

## Task 13: Write the typography and palette rationale (frontend-design, impeccable)

**Files:**
- Create: `docs/superpowers/plans/2026-11-20-dashboard-design-rationale.md`

**Interfaces:**
- Consumes: the tokens in `styles.css:1-34`
- Produces: one line per decision for the font stack, the canvas color, the accent, and each role hue, with the reason it exists. This satisfies R-06 and R-31.

- [ ] **Step 1: Write the rationale file**

For each decision write one line in the form `Decision: <value> — <reason tied to the run-board job>`. Cover `Candara, "Segoe UI"`, `--canvas`, `--accent`, and each of `--planner`, `--manager`, `--worker`, `--tester`, `--reviewer`. If a value has no reason, write `FAIL` and propose a merge.

- [ ] **Step 2: Verify every token is covered**

Run: `grep -o -- "--[a-z-]*:" .agents/skills/council-flow/dashboard/styles.css | sort -u`
Expected: every token name in `:root` appears in the rationale file.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-11-20-dashboard-design-rationale.md
git commit -m "docs: record dashboard typography and palette rationale"
```

## Task 14: Restyle the dashboard for visual appeal (applied, pending browser check)

**Files:**
- Modify: `.agents/skills/council-flow/dashboard/styles.css` (`:root` palette, `.intro`, `h1`, `.progress-track span`, `.role-tile` states)

**Interfaces:**
- Consumes: the element IDs and classes listed in `demo/dashboard/tests/auto-connection.test.cjs`, which must not change
- Produces: a new palette and motion treatment inside `styles.css` only. The publisher inlines this one file, so no other file changes.

- [x] **Step 1: Confirm the hooks the tests read are untouched**

Element IDs, `empty-state`, `board`, `.wordmark:hover`, and `.wordmark:active` are unchanged.

- [x] **Step 2: Apply the restyle**

Palette moved to deep violet with mint, cyan, and lime accents. The H1 has a text gradient, the intro has a soft glow and a single load animation, the progress bar has a gradient fill, and active role tiles have a colored ring with a hover lift.

- [x] **Step 3: Run the suites**

Run: `node --test demo/dashboard/tests/run-reader.test.cjs demo/dashboard/tests/auto-connection.test.cjs` and `python -m pytest demo/dashboard/tests/test_publisher.py tests/test_release.py tests/test_skill_files.py -q`
Expected: 22 Node tests pass and 26 Python tests pass. Recorded in this session.

- [ ] **Step 4: Check in a browser**

Open the published `dashboard.html` at desktop and phone widths, with reduced motion on and off. Record what looks wrong, then iterate on that. Not yet done.

- [ ] **Step 5: Commit after the owner approves the look**

```bash
git add .agents/skills/council-flow/dashboard/styles.css
git commit -m "style: refresh run dashboard palette and motion"
```

## Execution Order and Dependencies

- Task 1: complete.
- Task 14: applied. Commit after the browser check in Step 4.
- Tasks 2, 3, 4, and 5 are independent and are the required fixes. Run them first.
- Task 6 waits for the owner's answer on the meta refresh.
- Task 7 runs last, after the others are committed. It records the click-through and palette rationale.
- Tasks 8 to 13 are optional cosmetic work. Run them only if the owner asks.

