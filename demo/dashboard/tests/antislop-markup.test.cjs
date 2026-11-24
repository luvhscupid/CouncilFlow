const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const dashboardRoot = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard");
const sourceRoot = path.resolve(__dirname, "../app/src");
const css = fs.readFileSync(path.join(dashboardRoot, "styles.css"), "utf8");

function sources(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(directory, entry.name);
    return entry.isDirectory() ? sources(full) : [full];
  });
}

test("the base button rule meets the 44px touch target at every width", () => {
  const rule = css.match(/\n\.button \{([\s\S]*?)\n\}/);
  assert.ok(rule, "a base .button rule must exist");
  const minHeight = rule[1].match(/min-height:\s*(\d+)px/);
  assert.ok(minHeight && Number(minHeight[1]) >= 44, "base .button min-height must be at least 44px");
  assert.match(css, /\.button:active:not\(:disabled\)/);
});

test("the wordmark uses the plain CouncilFlow name", () => {
  const app = fs.readFileSync(path.join(sourceRoot, "App.jsx"), "utf8");
  const wordmark = app.match(/<a className="wordmark"[\s\S]*?<\/a>/);
  assert.ok(wordmark, "the wordmark link must exist");
  assert.doesNotMatch(wordmark[0], /<svg\b|<Icon\b/);
  assert.match(wordmark[0], />\s*<span>CouncilFlow<\/span>\s*<\/a>/);
  assert.match(css, /\.wordmark:hover/);
  assert.match(css, /\.wordmark:active/);
});

test("interactive controls expose pointer and disabled cursors", () => {
  assert.match(css, /a\[href\][\s\S]*?button[\s\S]*?cursor:\s*pointer/);
  assert.match(css, /:disabled[^{]*\{[^}]*cursor:\s*not-allowed/);
});

test("colors outside the root block use design tokens", () => {
  const withoutRoot = css.replace(/:root\s*\{[\s\S]*?\n\}/, "");
  assert.doesNotMatch(withoutRoot, /#[0-9a-fA-F]{3,8}\b/);
  assert.doesNotMatch(withoutRoot, /\brgba?\(/);
  for (const file of sources(sourceRoot)) {
    assert.doesNotMatch(fs.readFileSync(file, "utf8"), /#[0-9a-fA-F]{6}\b|\brgba?\(/, `${path.basename(file)} must use CSS tokens for color`);
  }
});

test("motion respects reduced-motion preferences and the in-app setting", () => {
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /\.is-reduced \*/);
  const chamber = fs.readFileSync(path.join(sourceRoot, "components/Chamber.jsx"), "utf8");
  assert.match(chamber, /latest && !reduced/, "the traveling packet must not render when motion is reduced");
});

test("dashboard copy has no em dash", () => {
  const files = [path.join(dashboardRoot, "index.html"), path.join(dashboardRoot, "app.js"), path.join(dashboardRoot, "styles.css"), ...sources(sourceRoot)];
  for (const file of files) assert.ok(!fs.readFileSync(file, "utf8").includes("—"), `${path.basename(file)} contains an em dash`);
});

test("the board offers no controls that act on the workflow", () => {
  const text = sources(sourceRoot).map(file => fs.readFileSync(file, "utf8")).join("\n");
  assert.doesNotMatch(text, />\s*(Approve|Dispatch|Retry|Run agent|Assign)\s*</i);
  assert.doesNotMatch(text, /\bfetch\(|XMLHttpRequest|WebSocket/);
});
