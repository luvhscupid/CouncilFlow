const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const dashboardRoot = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard");
const css = fs.readFileSync(path.join(dashboardRoot, "styles.css"), "utf8");

test("the base button rule meets the 44px touch target at every width", () => {
  const rule = css.match(/\n\.button \{([\s\S]*?)\n\}/);
  assert.ok(rule, "a base .button rule must exist");
  const minHeight = rule[1].match(/min-height:\s*(\d+)px/);
  assert.ok(minHeight, "the base .button rule must set min-height in px");
  assert.ok(Number(minHeight[1]) >= 44, `base .button min-height is ${minHeight[1]}px, needs at least 44px`);
});

test("the wordmark uses the plain CouncilFlow name", () => {
  const html = fs.readFileSync(path.join(dashboardRoot, "index.html"), "utf8");
  const wordmark = html.match(/<a class="wordmark"[\s\S]*?<\/a>/);
  assert.ok(wordmark, "the wordmark link must exist");
  assert.doesNotMatch(wordmark[0], /<svg\b/i);
  assert.match(wordmark[0], />\s*<span>CouncilFlow<\/span>\s*<\/a>/);
});

test("interactive controls expose pointer and disabled cursors", () => {
  assert.match(css, /a\[href\][\s\S]*?button[\s\S]*?cursor:\s*pointer/);
  assert.match(css, /:disabled[^{]*\{[^}]*cursor:\s*not-allowed/);
});

test("colors outside the root block use design tokens", () => {
  const withoutRoot = css.replace(/:root\s*\{[\s\S]*?\n\}/, "");
  assert.doesNotMatch(withoutRoot, /#[0-9a-fA-F]{3,8}\\b/);
});

test("the decorative eyebrow is removed while the intro remains first", () => {
  const html = fs.readFileSync(path.join(dashboardRoot, "index.html"), "utf8");
  assert.doesNotMatch(html, /class="run-label"/);
  assert.ok(html.indexOf('<h1 id="page-title"') < html.indexOf('<section id="empty-state"'));
});

test("the empty state has a bounded height", () => {
  const rule = css.match(/\.empty-state\s*\{([\s\S]*?)\n\}/);
  assert.ok(rule, "an .empty-state rule must exist");
  const minHeight = rule[1].match(/min-height:\s*(\d+)px/);
  assert.ok(minHeight, "the empty state must set min-height in px");
  assert.ok(Number(minHeight[1]) <= 220, `empty state min-height is ${minHeight[1]}px`);
});
