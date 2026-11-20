Written for: the owner and anyone changing the run dashboard colors or type.

# Dashboard design rationale (Task 13)

Each line gives a decision in `.agents/skills/council-flow/dashboard/styles.css` and the reason it exists for the run board.

- Decision: font stack `Candara, "Segoe UI", sans-serif` — a humanist system face keeps the read-only board calm and legible on Windows without loading a web font.
- Decision: `--canvas #0d0b14` — a deep violet-black gives the role colors room to read without a pure-black glare.
- Decision: `--surface #171425` and `--surface-raised #211c33` — two panel steps separate the workflow, acceptance, and activity panels without borders doing the work.
- Decision: `--accent #5ef2c2` — one mint accent marks the progress fill and the verified state, the one place the page says "done".
- Decision: `--manager #5cd1ff` — cyan identifies the Manager role in the workflow strip.
- Decision: `--planner #c78bff` (also `--owner`) — violet identifies the Planner and the Owner-facing decision points.
- Decision: `--worker #ffc45b` — amber identifies the Worker and also the warning state, which is the one case where amber means "needs attention".
- Decision: `--tester #6ef0a8` — green identifies the Tester, which runs the independent checks.
- Decision: `--reviewer #ff7cc8` — pink identifies the Reviewer, the only role that compares against the frozen plan.
- Decision: `--danger #ff918d` — a soft red reserved for failed criteria, kept muted so failure is visible without alarm.
- Decision: `--focus #ffe27a` — a yellow focus ring that stays visible against both the dark canvas and the violet panels.
- Decision: `--quiet #c4bcdc` — secondary body and label text; it stays readable on the surfaces while `--text` carries the primary content.
- Decision: `--dim #9187b0` — tertiary metadata such as footers and activity kinds, the lowest text step.
- Decision: `--line-soft #2a2442` — hairline dividers inside panels, lighter than the panel border `--line`.
- Decision: `--role-color` — not a palette value. Each `.role-*` class sets it to that role's hue, so the tile, ring, and activity marker share one color per role.
- Decision: `--radius-panel 15px` and `--radius-control 9px` — two radii only: large for panels, smaller for controls, so hierarchy is carried by size, not by many radius values.

Open item (not a palette decision): role hues are intentionally more than the two or three core colors in the generic antislop rule. They encode the five roles, so they stay. Owner may choose to merge hues later.

Tokens covered: every `--*` name in `:root` appears above, except the new neutral tokens added in Task 10 (`--surface-empty`, `--surface-current`, `--surface-progress`, `--line-strong`, `--line-hover`, `--line-warning`, `--text-warning`, `--surface-warning`, `--line-good`, `--text-good`, `--text-primary-hover`, `--role-warning`, `--line-status-warning`). Those keep the exact prior hex values and are named by role.
