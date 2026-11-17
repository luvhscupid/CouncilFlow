# Mission Control visual system

Refinement of the existing optional observer, authorized by the Owner's visual-redesign request on 2026-11-17. Operate mode: make recorded responsibility, final acceptance and evidence immediately legible. The interface remains a local observer with zero production dependencies. Data rules, contracts, fixtures, provenance and execution authority are unchanged.

## Color and depth

Midnight navy `#090f1c` is the workspace; `#111c2d` and `#19283e` form two working elevations. Rules use `#293b54`, primary ink `#edf4ff`, secondary text `#a6b8d0`. Electric blue `#79b5ff` and cyan `#78dfef` identify acceptance and current recorded responsibility. Violet `#b6a4ff` is reserved for Worker identity and intermediate-state marks. Green, amber and red supplement explicit status text and symbols.

Gradients have narrow jobs: blue-to-cyan final-acceptance segments and the import action; low-opacity blue ambient light across the overview; a restrained violet tint in the recorded-active role. No blur/glass, neon halo, decorative charts, pulse loops or simulated event stream. Shadows have a downward offset and soft falloff. Panels use 12–16px corners; controls and status labels use smaller radii. All colors are CSS tokens with a complete light theme.

The Owner explicitly requested controlled violet and subtle gradients in this pass. These choices supersede the previous DESIGN.md prohibition and conflicting general taste-skill palette preferences; they do not change data or security policy.

## Typography and icons

Local Segoe UI Variable / Segoe UI avoids font downloads and preserves the offline runtime. Main heading 28–34px, section headings 18–20px, body 14–15px, most metadata 12–13px. Cascadia Code / Consolas is reserved for IDs, timestamps, command evidence and hashes. Tabular numbers support comparison. Imported text wraps without truncating criterion wording.

One authored SVG stroke family identifies roles and navigation. Planner uses a plan/candidate cube, Manager a delegation tree, Worker code brackets, Tester a flask, Reviewer a verification shield and Owner a person. The same glyph appears in role cards, workflow and events. Glyphs are fixed application paths and aria-hidden; imported data never becomes SVG, HTML or a URL.

## Fluid composition

The main column has no maximum width. A 228px navigation rail (202px at intermediate desktop widths) gives way to scrollable navigation below 1100px. Gutters remain symmetrical. At 2048px, main occupies the remaining 1820px; no unused right column is reserved.

The overview groups project identity/status, the acceptance fraction and segmented bar, recorded operation/timing and the actual nine-step handoff sequence. The fraction remains acceptance of original criteria for the selected candidate, never phase completion. Repeated Manager/Planner occurrences are preserved and never inferred to have passed.

Blockers use compact parallel notices on desktop. Five role summaries remain equally readable responsibilities; a stronger surface and border identify the last recorded active role without implying five persistent agents. Model and attempt information stay visible when collapsed. The acceptance ledger and console share the next row. At wide sizes verification uses two columns and resources three, reducing unused panel space.

At 1024px roles form three columns; at 768px two; on phones they stack with the recorded-active responsibility first. Current operation precedes acceptance on phones. The nine-step workflow becomes three columns on phones, showing every handoff rather than hiding it offscreen. Evidence and resource panels stack. Long names, unknown metrics, empty projects and failed runs keep the same system.

## Interaction and motion

Native buttons, selects, details and dialog preserve keyboard behavior. Hover lifts a role summary 2px and strengthens its border. Expansion animates already-visible content briefly; a chevron communicates state. Progress animates once only when the imported/selected candidate state changes. There is no clock-driven activity or decorative autoplay. Reduced motion disables CSS animation and scrolling, cancels in-flight progress animation immediately, and prevents new progress animation. Import shows a disabled/loading state while reading a selected file.

Focus uses a high-contrast cyan outline. Evidence details contain keyboard focus, close with Escape and restore focus. Theme switching updates browser theme-color. Unknown models and metrics retain Not reported; DEMO DATA stays explicit. A status dot is a static recorded-state marker, never a live indicator.

## Verification and design skills

Applied frontend-design for hierarchy and ledger/console composition; ui-ux-pro-max search for information hierarchy and non-color status cues; taste-skill for consistent edges, restraint and screenshot critique; Impeccable Operate/polish/craft guidance plus its context launcher and detector; product-design:audit for before/after screenshot review; Web Interface Guidelines for semantics, focus and content handling; Playwright CLI for rendered testing. Marketing hero/photography/generative-option workflows were not applicable to this bounded dashboard refinement. No skill hook was installed.

See [the redesign QA record](evidence/redesign/README.md) for exact tests, browser evidence, skill limits, contrast checks and remaining uncertainty. This document describes presentation only and has no normative CouncilFlow workflow authority.
