const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { buildSnapshot } = require("../run-reader.js");

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

function fixture() {
  const taskId = "live-task";
  const plan = {
    plan_id: "live-plan", plan_revision: 1, task_id: taskId,
    acceptance: [{ id: "LIVE-01", text: "Uses the current task's packet data." }]
  };
  const planText = JSON.stringify(plan);
  const planHash = crypto.createHash("sha256").update(planText).digest("hex");
  const publication = {
    protocol: "council-flow", version: "1.0", message_id: "publish-live",
    message_type: "plan.publish", plan_id: "live-plan", plan_revision: 1,
    task_id: taskId, attempt_id: "attempt-1",
    sender: { role: "planner", instance_id: "planner" },
    recipient: { role: "manager", instance_id: "manager" }, in_reply_to: null,
    payload: {
      objective: "Test live bootstrap", scope: ["Current run"], acceptance_ids: ["LIVE-01"],
      plan_ref: { artifact_id: "live-plan-file", path: "plan.json", sha256: planHash, kind: "plan" }
    },
    evidence_refs: []
  };
  return {
    taskId,
    files: [
      { name: "plan.json", path: "plan.json", data: plan, isMessageFile: false, sha256: planHash },
      { name: "plan-publish.json", path: "messages/plan-publish.json", data: publication, isMessageFile: true }
    ]
  };
}

test("embedded task packets render as an automatic connection without a folder picker", async () => {
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
  elements["councilflow-run-data"].textContent = JSON.stringify(fixture());
  const refreshMeta = new Element("refresh-meta");
  const frames = [];
  let reloads = 0;
  const document = {
    getElementById(id) { return elements[id] || (elements[id] = new Element(id)); },
    createElement(tag) { return new Element(tag); },
    createElementNS(_namespace, tag) { return new Element(tag); },
    querySelector(selector) { return selector.includes("http-equiv") ? refreshMeta : null; }
  };
  const window = {
    CouncilFlowRunReader: { buildSnapshot },
    location: { reload() { reloads += 1; } },
    setInterval() { return 1; },
    clearInterval() {},
    requestAnimationFrame(callback) { frames.push(callback); }
  };
  const appPath = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard/app.js");
  vm.runInNewContext(fs.readFileSync(appPath, "utf8"), { document, window, crypto: null, console });

  assert.equal(elements["loading-state"].hidden, false);
  assert.match(elements["loading-state"].textContent, /Reading.*packets/i);
  assert.equal(frames.length, 1);
  frames.shift()();
  await new Promise(resolve => setImmediate(resolve));

  assert.equal(elements["loading-state"].hidden, true);
  assert.equal(elements.board.hidden, false);
  assert.equal(elements["empty-state"].hidden, true);
  assert.equal(elements["run-summary"].textContent, "Task live-task");
  assert.match(elements["connection-state"].lastElementChild.textContent, /Connected to live-task/);
  assert.equal(typeof elements["choose-folder"].listeners.click, "function");
  elements["refresh-run"].listeners.click({ currentTarget: elements["refresh-run"] });
  assert.equal(reloads, 1);
  elements["choose-folder"].listeners.click();
  assert.equal(refreshMeta.removed, true);
  assert.equal(elements["folder-fallback"].clicked, true);
});

test("dashboard copy uses an honest placeholder without an em dash", () => {
  const dashboardRoot = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard");
  const sources = ["index.html", "app.js", "styles.css"].map(name => fs.readFileSync(path.join(dashboardRoot, name), "utf8"));
  assert.match(sources[0], /id="loading-state"[^>]*role="status"[^>]*aria-live="polite"/);
  assert.ok(sources.every(source => !source.includes("—")));
  assert.match(sources[2], /\.button:active:not\(:disabled\)/);
  assert.match(sources[2], /\.wordmark:hover/);
  assert.match(sources[2], /\.wordmark:active/);
});

test("manual file import reports what it is reading before rendering", async () => {
  const ids = [
    "connection-state", "folder-fallback", "file-picker", "choose-folder", "choose-files",
    "refresh-run", "empty-state", "board", "run-summary", "run-health", "current-activity",
    "acceptance-count", "acceptance-progress", "progress-fill", "progress-label", "progress-honesty",
    "acceptance-caption", "role-list", "criteria-list", "activity-count", "activity-list", "record-alert",
    "loading-state"
  ];
  const elements = Object.fromEntries(ids.map(id => [id, new Element(id)]));
  elements["connection-state"].append(new Element("dot"), new Element("label"));
  const frames = [];
  const document = {
    getElementById(id) { return elements[id] || (elements[id] = new Element(id)); },
    createElement(tag) { return new Element(tag); },
    createElementNS(_namespace, tag) { return new Element(tag); },
    querySelector() { return null; }
  };
  const window = {
    CouncilFlowRunReader: { buildSnapshot },
    setInterval() { return 1; },
    clearInterval() {},
    requestAnimationFrame(callback) { frames.push(callback); },
    async showDirectoryPicker() {
      return {
        async *entries() {
          yield ["packet.json", {
            kind: "file",
            async getFile() { return { name: "packet.json", size: 9, text: async () => "{bad json" }; }
          }];
        }
      };
    }
  };
  const appPath = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard/app.js");
  vm.runInNewContext(fs.readFileSync(appPath, "utf8"), { document, window, crypto: null, console });
  elements["file-picker"].files = [{ name: "packet.json", size: 9, text: async () => "{bad json" }];

  elements["file-picker"].listeners.change();

  assert.equal(elements["loading-state"].hidden, false);
  assert.equal(elements["loading-state"].textContent, "Reading selected message files");
  frames.shift()();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(elements["loading-state"].hidden, false);
  assert.equal(elements["loading-state"].textContent, "Reading selected run packets");
  frames.shift()();
  await new Promise(resolve => setImmediate(resolve));

  assert.equal(elements["loading-state"].hidden, true);
  assert.equal(elements.board.hidden, false);
  assert.equal(elements["record-alert"].hidden, false);

  elements["choose-folder"].listeners.click();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(elements["loading-state"].hidden, false);
  assert.match(elements["loading-state"].textContent, /Reading.*packets/i);
  frames.shift()();
  await new Promise(resolve => setImmediate(resolve));

  assert.equal(elements["loading-state"].hidden, true);
  assert.equal(elements["record-alert"].hidden, false);
});

function mountDashboard(directoryHandle) {
  const ids = [
    "connection-state", "folder-fallback", "file-picker", "choose-folder", "choose-files",
    "empty-open-folder", "empty-open-files", "file-access-help", "refresh-run", "empty-state", "board",
    "run-summary", "run-health", "current-activity", "acceptance-count", "acceptance-progress",
    "progress-fill", "progress-label", "progress-honesty", "acceptance-caption", "role-list",
    "criteria-list", "activity-count", "activity-list", "record-alert", "loading-state"
  ];
  const elements = Object.fromEntries(ids.map(id => [id, new Element(id)]));
  elements["connection-state"].append(new Element("dot"), new Element("label"));
  const refreshMeta = new Element("refresh-meta");
  const intervals = [];
  const window = {
    CouncilFlowRunReader: { buildSnapshot },
    crypto: null,
    requestAnimationFrame(callback) { queueMicrotask(callback); },
    setInterval(callback, milliseconds) {
      const interval = { callback, milliseconds, cleared: false };
      intervals.push(interval);
      return interval;
    },
    clearInterval(interval) { interval.cleared = true; },
    async showDirectoryPicker() { return directoryHandle; }
  };
  const document = {
    getElementById(id) { return elements[id] || (elements[id] = new Element(id)); },
    createElement(tag) { return new Element(tag); },
    createElementNS(_namespace, tag) { return new Element(tag); },
    querySelector() { return refreshMeta; }
  };
  const appPath = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard/app.js");
  vm.runInNewContext(fs.readFileSync(appPath, "utf8"), { document, window, crypto: null, console });
  return { elements, intervals, refreshMeta };
}

function fileHandle(file) {
  return { kind: "file", async getFile() { return file; } };
}

function makeFile(name, size = 2, text = "{}") {
  return { name, size, async text() { return text; } };
}

function directoryHandle(entries) {
  return {
    kind: "directory",
    async *entries() { yield* entries(); }
  };
}

async function waitFor(predicate, message) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (predicate()) return;
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.fail(message);
}

async function chooseFolder(app) {
  app.elements["choose-folder"].listeners.click();
  await waitFor(() => /Watching selected folder|Folder access paused/.test(app.elements["connection-state"].lastElementChild.textContent),
    "folder picker did not finish its first scan");
}

test("an oversized JSON file stops before reading it and shows an incomplete run", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    yield ["oversized.json", fileHandle({
      name: "oversized.json", size: 65537,
      async text() { reads += 1; return "{}"; }
    })];
  });
  const app = mountDashboard(folder);
  await chooseFolder(app);
  assert.equal(reads, 0);
  assert.match(app.elements["record-alert"].textContent, /oversized\.json.*65,?536|65,?536.*oversized\.json/i);
  assert.equal(app.elements["run-health"].textContent, "Incomplete records");
  assert.equal(app.elements["acceptance-count"].textContent, "Incomplete");
});

test("more than 1,024 JSON files stops traversal and shows an incomplete run", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    for (let index = 0; index < 1025; index += 1) {
      const name = `packet-${index}.json`;
      yield [name, fileHandle({ name, size: 2, async text() { reads += 1; return "{}"; } })];
    }
  });
  const app = mountDashboard(folder);
  await chooseFolder(app);
  assert.equal(reads, 1024);
  assert.match(app.elements["record-alert"].textContent, /1,?024.*JSON|JSON.*1,?024/i);
  assert.equal(app.elements["run-health"].textContent, "Incomplete records");
  assert.equal(app.elements["acceptance-count"].textContent, "Incomplete");
});

test("directory depth above 16 stops traversal and shows an incomplete run", async () => {
  let fileReads = 0;
  function nested(depth) {
    return directoryHandle(async function* () {
      if (depth < 17) yield [`level-${depth}`, nested(depth + 1)];
      else yield ["packet.json", fileHandle({ name: "packet.json", size: 2, async text() { fileReads += 1; return "{}"; } })];
    });
  }
  const app = mountDashboard(nested(0));
  await chooseFolder(app);
  assert.equal(fileReads, 0);
  assert.match(app.elements["record-alert"].textContent, /depth.*16|16.*depth/i);
  assert.equal(app.elements["run-health"].textContent, "Incomplete records");
  assert.equal(app.elements["acceptance-count"].textContent, "Incomplete");
});

test("aggregate JSON input above 16 MiB stops before reading the excess file", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    for (let index = 0; index < 257; index += 1) {
      const name = `packet-${index}.json`;
      yield [name, fileHandle({ name, size: 65536, async text() { reads += 1; return "{}"; } })];
    }
  });
  const app = mountDashboard(folder);
  await chooseFolder(app);
  assert.equal(reads, 256);
  assert.match(app.elements["record-alert"].textContent, /16 ?MiB|16,?777,?216/i);
  assert.equal(app.elements["run-health"].textContent, "Incomplete records");
  assert.equal(app.elements["acceptance-count"].textContent, "Incomplete");
});

test("a second refresh tick does not overlap the active directory scan", async () => {
  let scans = 0;
  let releaseScan;
  let markSlowScan;
  const slowScanStarted = new Promise(resolve => { markSlowScan = resolve; });
  const slowScanGate = new Promise(resolve => { releaseScan = resolve; });
  const folder = directoryHandle(async function* () {
    scans += 1;
    if (scans === 2) {
      markSlowScan();
      await slowScanGate;
    }
    yield ["packet.json", fileHandle(makeFile("packet.json"))];
  });
  const app = mountDashboard(folder);
  await chooseFolder(app);
  assert.equal(app.intervals.length, 1);
  const firstRefresh = app.intervals[0].callback();
  await slowScanStarted;
  await app.intervals[0].callback();
  assert.equal(scans, 2);
  releaseScan();
  await firstRefresh;
});

test("the folder watch can pause and resume on the same selected directory", async () => {
  const folder = directoryHandle(async function* () {
    yield ["packet.json", fileHandle(makeFile("packet.json"))];
  });
  const app = mountDashboard({
    kind: "directory",
    async *entries() { for await (const entry of folder.entries()) yield entry; }
  });
  await chooseFolder(app);
  assert.equal(app.intervals.length, 1);
  const control = app.elements["refresh-run"];
  control.listeners.click({ currentTarget: control });
  assert.equal(app.intervals[0].cleared, true);
  assert.equal(control.textContent, "Refresh");
  control.listeners.click({ currentTarget: control });
  await waitFor(() => app.intervals.length === 2, "folder watch did not resume");
  assert.equal(control.textContent, "Pause watching");
});
