const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
  constructor(id = "") {
    this.id = id;
    this.children = [];
    this.dataset = {};
    this.style = {};
    this.listeners = {};
    this.attributes = {};
    this.hidden = false;
    this.textContent = "";
    this.className = "";
    this.disabled = false;
  }
  get lastElementChild() { return this.children[this.children.length - 1] || null; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(type, listener) { this.listeners[type] = listener; }
  remove() { this.removed = true; }
  click() { this.clicked = true; }
}

function craftedSnapshot(issues) {
  return {
    valid: false, issues, taskId: "crafted-task", planId: "crafted-plan", stages: [], criteria: [],
    activity: [], current: null, progress: { passed: 0, total: 0, recorded: false },
    disposition: "Run in progress", sourceNotice: ""
  };
}

async function renderIssues(issues) {
  const ids = [
    "connection-state", "folder-fallback", "file-picker", "choose-folder", "choose-files",
    "refresh-run", "empty-state", "board", "run-summary", "run-health", "current-activity",
    "acceptance-count", "acceptance-progress", "progress-fill", "progress-label", "progress-honesty",
    "acceptance-caption", "role-list", "criteria-list", "activity-count", "activity-list", "record-alert",
    "loading-state"
  ];
  const elements = Object.fromEntries(ids.map(id => [id, new Element(id)]));
  elements["record-alert"].hidden = true;
  elements["connection-state"].append(new Element("dot"), new Element("label"));
  elements["councilflow-run-data"] = new Element("councilflow-run-data");
  elements["councilflow-run-data"].textContent = JSON.stringify({
    taskId: "crafted-task",
    files: [{ name: "packet.json", path: "messages/packet.json", data: {}, isMessageFile: true }]
  });
  const frames = [];
  const document = {
    getElementById(id) { return elements[id] || (elements[id] = new Element(id)); },
    createElement(tag) { return new Element(tag); },
    createElementNS(_namespace, tag) { return new Element(tag); },
    querySelector() { return null; }
  };
  const window = {
    CouncilFlowRunReader: { buildSnapshot() { return craftedSnapshot(issues.map(issue => ({ ...issue }))); } },
    location: { reload() {} },
    setInterval() { return 1; },
    clearInterval() {},
    requestAnimationFrame(callback) { frames.push(callback); }
  };
  const appPath = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard/app.js");
  vm.runInNewContext(fs.readFileSync(appPath, "utf8"), { document, window, crypto: null, console });
  while (frames.length) frames.shift()();
  await new Promise(resolve => setImmediate(resolve));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(elements.board.hidden, false, "crafted snapshot must render");
  return elements["record-alert"];
}

test("every issue appears on its own line after the count line, in order", async () => {
  const issues = [
    { detail: "first.json: could not read valid JSON." },
    { code: "missing_parent", detail: "M2 refers to M1" },
    { code: "orphan_message", detail: "M3 has no causal predecessor." },
    { code: "causal_cycle", detail: "Packet reply references contain a cycle." },
    { code: "mixed_runs", detail: "Choose packet files from one task and plan at a time." }
  ];
  const alert = await renderIssues(issues);
  assert.equal(alert.hidden, false);
  const lines = alert.textContent.split("\n");
  assert.equal(lines.length, issues.length + 1);
  assert.equal(lines[0], "5 record issues:");
  issues.forEach((issue, index) => assert.equal(lines[index + 1], `- ${issue.detail}`));
});

test("a single issue keeps the singular count wording", async () => {
  const alert = await renderIssues([{ detail: "Only problem." }]);
  assert.deepEqual(alert.textContent.split("\n"), ["1 record issue:", "- Only problem."]);
});

test("bare-id issues render as plain-language sentences that keep the exact id", async () => {
  const alert = await renderIssues([
    { code: "duplicate_message_id", detail: "msg-7" },
    { code: "missing_criterion_evidence", detail: "AC2" }
  ]);
  const lines = alert.textContent.split("\n");
  assert.equal(lines.length, 3);
  for (const [line, id] of [[lines[1], "msg-7"], [lines[2], "AC2"]]) {
    assert.ok(line.includes(id), `${line} must contain ${id}`);
    assert.notEqual(line, `- ${id}`);
    assert.ok(line.replace(/^- /, "").length > id.length + 10, `${line} must be a sentence`);
  }
  assert.match(lines[1], /same id/i);
  assert.match(lines[2], /criterion AC2/);
});

test("sentence details, codeless issues, unmapped codes and fallback texts stay unchanged", async () => {
  const alert = await renderIssues([
    { detail: "packet.json: could not read valid JSON." },
    { code: "some_future_code", detail: "future-id-3" },
    { code: "unsupported_contract", detail: "Unknown packet" },
    { code: "invalid_identity", detail: "Packet identity or type is invalid." },
    { code: "unsupported_contract", detail: "msg-9" },
    { code: "invalid_identity", detail: "msg-10" }
  ]);
  const lines = alert.textContent.split("\n");
  assert.equal(lines.length, 7);
  assert.equal(lines[1], "- packet.json: could not read valid JSON.");
  assert.equal(lines[2], "- future-id-3");
  assert.equal(lines[3], "- Unknown packet");
  assert.equal(lines[4], "- Packet identity or type is invalid.");
  for (const [line, id] of [[lines[5], "msg-9"], [lines[6], "msg-10"]]) {
    assert.ok(line.includes(id), `${line} must contain ${id}`);
    assert.notEqual(line, `- ${id}`);
    assert.ok(line.replace(/^- /, "").length > id.length + 10, `${line} must be a sentence`);
  }
});

test("more than 20 issues shows the first 20 and a count of the rest", async () => {
  const issues = Array.from({ length: 25 }, (_, index) => ({ detail: `Issue number ${index + 1}.` }));
  const alert = await renderIssues(issues);
  const lines = alert.textContent.split("\n");
  assert.equal(lines.length, 22);
  assert.equal(lines[0], "25 record issues:");
  for (let index = 0; index < 20; index += 1) assert.equal(lines[index + 1], `- Issue number ${index + 1}.`);
  assert.equal(lines[21], "5 more not shown.");
  assert.ok(!alert.textContent.includes("Issue number 21."));
});

test("exactly 20 issues shows no 'more not shown' line", async () => {
  const issues = Array.from({ length: 20 }, (_, index) => ({ detail: `Issue ${index + 1}.` }));
  const alert = await renderIssues(issues);
  const lines = alert.textContent.split("\n");
  assert.equal(lines.length, 21);
  assert.ok(!/more not shown/.test(alert.textContent));
});

test("zero issues hides the alert with empty text", async () => {
  const alert = await renderIssues([]);
  assert.equal(alert.hidden, true);
  assert.equal(alert.textContent, "");
});

test("the record alert style keeps line breaks and app.js has no em dash", () => {
  const dashboardRoot = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard");
  const styles = fs.readFileSync(path.join(dashboardRoot, "styles.css"), "utf8");
  assert.match(styles, /\.record-alert \{[^}]*white-space: pre-line;[^}]*\}/);
  const app = fs.readFileSync(path.join(dashboardRoot, "app.js"), "utf8");
  assert.ok(!app.includes("\u2014"));
});
