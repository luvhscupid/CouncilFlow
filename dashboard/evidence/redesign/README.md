# Visual refinement QA — 2026-11-17

Windows-local Edge verification of the visual refinement from dashboard commit `2a42e6e`, on `feat/dashboard-observability-mvp-20261117`. The initial tree was clean. This is not a live CouncilFlow role invocation or Codex Cloud evidence. No source projection, contract, fixture, security policy or production dependency changed.

## Executed checks

- `node --test dashboard/tests/projection.test.mjs`: all 12 tests passed.
- Playwright CLI 0.1.24, `tests/browser-smoke.cjs`: 44 assertions passed. The existing 40 checks were retained, plus current icon-design verification and additional long-title widths. Browser HTTP caching was disabled to ensure the actual current source was exercised.
- Playwright CLI, `tests/redesign-visual.cjs`: 80 assertions passed. Both themes at 320, 375, 768, 1024, 1440, 1920 and 2048px; full-width main layout; 28px minimum main heading; 44px minimum button/select heights; empty/failed scenario provenance; drawer focus containment/restoration; active-role priority on phones; event-driven progress motion and reduced-motion suppression; empty filters and visible import-error recovery; no browser runtime errors.
- Browser-derived palette contrast: the eight text/status tokens against the three base surfaces all exceed 4.5:1; worst light pair 5.35:1, worst dark pair 6.89:1. Primary-action gradient endpoints exceed 5.88:1 in light and 7.74:1 in dark. These are token/surface tests, not exhaustive pixel-level contrast certification.
- Impeccable context launcher and detector executed. Final `design-scan.json` is `[]`. The gradient button now has an explicit readable fallback; mobile operation text has an inset. Source reviewed against the current [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md).
- The original 239-test Python regression result remains historical evidence from the MVP implementation. It was not rerun for this presentation-only pass; the projection/parser source, package builder and CouncilFlow skill remain unchanged.

The visual suite initially found an in-flight Web Animation continuing after reduced motion changed. The implementation now cancels existing progress animations on both preference change and render, and skips new animation under reduced motion. The negative check now passes. Early screenshots served stale browser-cache content; those were rejected and recaptured after disabling cache and asserting the new SVG role icons exist.

## Screenshot-led audit

1. **Wide overview — improved.** [Before](before-2048.png) and [after](after-2048.png) at 2048px. Current main width is 1820px, exactly the space remaining after the navigation rail; no unused right column. A contained midnight overview separates final acceptance from recorded operation. Cyan acceptance segments and role glyphs give hierarchy without simulating telemetry.
2. **Role workspace and console — healthy.** [Dark desktop](dark-1440.png). Role-specific SVG identities repeat in the workflow and console. Model/attempt metadata is available when collapsed. Activity has readable timestamps, severity text, a consistent timeline and expandable details. No control is decorative.
3. **Phone/tablet composition — improved.** [Phone](dark-375.png) and [light tablet](light-768.png). Phones show all nine workflow steps in a three-column ordered sequence; active responsibility is first. Tablet panels stack and roles use two columns. The navigation rail can scroll locally, without document overflow.
4. **Evidence inspection — healthy.** [Drawer](evidence-drawer.png). Candidate history and original evidence remain available, with keyboard focus contained and restored. Imported references/commands remain inert text.
5. **Light, empty and failed states — healthy in smoke coverage.** [Light desktop](light-1440.png), [empty](dark-empty.png), [failed](dark-failed.png), [import error](import-error.png). Distinct text/symbols supplement color; Not assessable and Not reported remain honest. Import failures preserve the previous run and retain the existing explain-and-recover message. Their behavior is covered by the browser suite.

Screenshots were captured from the actual local page and inspected. Full-page captures may show the bounded event console viewport; its remaining events are reached by scrolling or its existing pagination control. Historical MVP screenshots outside this directory are preserved.

## Skill application and limits

Read and applied frontend-design, ui-ux-pro-max, taste-skill, Impeccable, product-design:audit, web-design-guidelines and playwright-cli. ui-ux-pro-max's actual hierarchy query returned non-color status and heading-order guidance. Impeccable's context, polish/craft guidance and mechanical scan were used. Taste's marketing one-section-per-screen/photography gate does not fit this dashboard and was not claimed; the Owner's explicit violet/gradient direction takes precedence over its default restrictions. No skill hooks, image-generation service or production library was installed.

Impeccable noted legacy metadata in the existing PRODUCT.md; it was left unchanged because refreshing that record is outside this visual pass. A later optional init pass can update the skill metadata.

Edge/Chromium only. Screen-reader behavior, other browser engines and full WCAG conformance remain unverified. Imported provenance is not authenticated. No live telemetry, model attribution, real token accounting, host hooks, external execution, merge, deployment, push or publication occurred.

Reproduce: run the static server documented in ../../README.md, open the CLI session, then execute both browser scripts with `run-code --filename=...`. Logs beside this file contain the actual checks and layout measurements. Reload after local edits; the tests explicitly disable HTTP caching.
