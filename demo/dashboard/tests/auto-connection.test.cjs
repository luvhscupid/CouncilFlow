const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const reader = require("../run-reader.js");
const loader = require("../app/src/data/run-loader.js");
const { buildModel } = require("../app/src/data/council-model.js");
const { scenario } = require("./fixtures/council-run.cjs");

const dashboardRoot = path.resolve(__dirname, "../../../.agents/skills/council-flow/dashboard");

function fileHandle(file) { return { kind: "file", async getFile() { return file; } }; }
function makeFile(name, size = 2, text = "{}", lastModified = Date.UTC(2026, 10, 24)) {
  return { name, size, lastModified, async text() { return text; } };
}
function directoryHandle(entries) { return { kind: "directory", async *entries() { yield* entries(); } }; }

/* Run reader bounds */

test("an oversized JSON file stops before reading it", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    yield ["oversized.json", fileHandle({ name: "oversized.json", size: 65537, async text() { reads += 1; return "{}"; } })];
  });
  await assert.rejects(loader.filesFromDirectory(folder, loader.createReadState()), /oversized\.json.*65,536/);
  assert.equal(reads, 0);
});

test("more than 1,024 JSON files stops traversal", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    for (let index = 0; index < 1025; index += 1) {
      const name = `packet-${index}.json`;
      yield [name, fileHandle({ name, size: 2, async text() { reads += 1; return "{}"; } })];
    }
  });
  await assert.rejects(loader.filesFromDirectory(folder, loader.createReadState()), /1,024 JSON files/);
  assert.equal(reads, 1024);
});

test("directory depth above 16 stops traversal", async () => {
  let reads = 0;
  function nested(depth) {
    return directoryHandle(async function* () {
      if (depth < 17) yield [`level-${depth}`, nested(depth + 1)];
      else yield ["packet.json", fileHandle({ name: "packet.json", size: 2, async text() { reads += 1; return "{}"; } })];
    });
  }
  await assert.rejects(loader.filesFromDirectory(nested(0), loader.createReadState()), /depth exceeds 16/);
  assert.equal(reads, 0);
});

test("aggregate JSON input above 16 MiB stops before reading the excess file", async () => {
  let reads = 0;
  const folder = directoryHandle(async function* () {
    for (let index = 0; index < 257; index += 1) {
      const name = `packet-${index}.json`;
      yield [name, fileHandle({ name, size: 65536, async text() { reads += 1; return "{}"; } })];
    }
  });
  await assert.rejects(loader.filesFromDirectory(folder, loader.createReadState()), /16 MiB/);
  assert.equal(reads, 256);
});

test("read files keep their path, parse errors and write time", async () => {
  const files = await loader.filesFromList([
    { ...makeFile("bad.json", 9, "{bad json"), webkitRelativePath: "run/messages/bad.json" },
    makeFile("notes.txt")
  ]);
  assert.equal(files.length, 1);
  assert.equal(files[0].path, "run/messages/bad.json");
  assert.equal(files[0].isMessageFile, true);
  assert.match(files[0].error, /could not read valid JSON/);
  assert.equal(files[0].modified, "2026-11-24T00:00:00.000Z");
});

test("a folder watch never overlaps scans and can pause and resume", async () => {
  let scans = 0;
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  const folder = directoryHandle(async function* () {
    scans += 1;
    if (scans === 1) await gate;
    yield ["packet.json", fileHandle(makeFile("packet.json"))];
  });
  const timers = { intervals: [], setInterval(fn, ms) { const t = { fn, ms, cleared: false }; this.intervals.push(t); return t; }, clearInterval(t) { t.cleared = true; } };
  const seen = [];
  const watcher = loader.watchDirectory(folder, { timers, onFiles: files => seen.push(files.length) });
  const first = watcher.scan();
  assert.equal(await watcher.scan(), false, "second scan must not start while the first runs");
  release();
  assert.equal(await first, true);
  watcher.start();
  assert.equal(watcher.watching, true);
  watcher.stop();
  assert.equal(timers.intervals[0].cleared, true);
  watcher.start();
  assert.equal(timers.intervals.length, 2);
  assert.deepEqual(seen, [1]);
});

test("a failing folder scan stops the watch and reports the error", async () => {
  const folder = directoryHandle(async function* () { yield ["big.json", fileHandle(makeFile("big.json", 70000))]; });
  let reported = null;
  const timers = { setInterval() { return 1; }, clearInterval() {} };
  const watcher = loader.watchDirectory(folder, { timers, onError: error => { reported = error.message; } });
  watcher.start();
  assert.equal(await watcher.scan(), false);
  assert.equal(watcher.watching, false);
  assert.match(reported, /big\.json/);
});

/* Council view model */

test("an empty run invents no activity, progress or model", () => {
  const model = buildModel({ files: [] }, reader);
  assert.equal(model.packets.length, 0);
  assert.equal(model.lifecycle.done, 0);
  assert.equal(model.acceptance.verified, false);
  assert.equal(model.timing.available, false);
  assert.equal(model.efficiency.available, false);
  assert.ok(model.roles.every(role => role.model.value === null));
  assert.ok(model.roles.every(role => ["idle", "planning"].includes(role.state.key)));
});

test("an active assignment shows the Worker working and the next step as current", () => {
  const model = buildModel(scenario("working"), reader);
  const worker = model.roles.find(role => role.role === "worker");
  assert.equal(worker.state.key, "working");
  assert.equal(worker.state.sourceId, "M002");
  assert.equal(worker.currentTask.instructions.length, 3);
  assert.equal(model.lifecycle.done, 2);
  assert.equal(model.lifecycle.current.key, "worker-report");
  assert.equal(model.latest.id, "M002");
  assert.ok(model.routes.find(route => route.id === "manager>worker").latest);
});

test("a failed Tester report halts the attempt and later steps are skipped, not missing", () => {
  const model = buildModel(scenario("sent_back"), reader);
  const statuses = Object.fromEntries(model.lifecycle.steps.map(step => [step.key, step.status]));
  assert.equal(statuses["tester-report"], "failed");
  assert.equal(statuses["reviewer-assign"], "skipped");
  assert.equal(statuses.decision, "rework");
  assert.equal(model.lifecycle.gaps, 0);
  assert.equal(model.roles.find(role => role.role === "tester").state.key, "failed");
  assert.equal(model.roles.find(role => role.role === "manager").state.label, "Preparing the rework");
});

test("rework starts a new attempt and progress counts only that attempt", () => {
  const model = buildModel(scenario("rework"), reader);
  assert.equal(model.run.currentAttempt, "attempt-2");
  assert.equal(model.attempts.length, 2);
  assert.equal(model.attempts[0].decision, "rework");
  assert.equal(model.roles.find(role => role.role === "tester").state.key, "testing");
  assert.deepEqual(model.roles.find(role => role.role === "worker").instances, ["worker-1", "worker-2"]);
  assert.equal(model.lifecycle.done, 4);
});

test("only a complete final check makes acceptance verified", () => {
  const reviewing = buildModel(scenario("reviewing"), reader);
  assert.equal(reviewing.acceptance.verified, false);
  assert.equal(reviewing.acceptance.passed, 0);
  const accepted = buildModel(scenario("accepted"), reader);
  assert.equal(accepted.run.valid, true);
  assert.equal(accepted.acceptance.verified, true);
  assert.equal(accepted.acceptance.passed, 3);
  assert.equal(accepted.lifecycle.complete, true);
  assert.ok(accepted.roles.filter(role => role.role !== "owner").every(role => role.state.key === "completed"));
  assert.deepEqual(accepted.plan.tasks.map(task => task.id), ["T1", "T2"]);
});

test("a record issue suppresses verified acceptance even with a passing chain", () => {
  const run = scenario("accepted");
  run.files.push({ name: "dashboard-validation.json", path: "dashboard-validation.json", data: {}, error: "M010.json: artifact_hash at evidence_refs." });
  const model = buildModel(run, reader);
  assert.equal(model.run.valid, false);
  assert.equal(model.acceptance.verified, false);
  assert.ok(model.issues.some(issue => issue.detail.includes("artifact_hash")));
});

test("times come from file write times and are absent when files carry none", () => {
  const model = buildModel(scenario("testing"), reader);
  assert.equal(model.timing.source, "file write times");
  assert.equal(model.timing.span, (3 + 11 + 2) * 60000);
  const worker = model.roles.find(role => role.role === "worker");
  assert.deepEqual(worker.handlingMs, [11 * 60000]);
  const bare = scenario("testing");
  bare.files.forEach(file => { delete file.modified; });
  const untimed = buildModel(bare, reader);
  assert.equal(untimed.timing.available, false);
  assert.equal(untimed.roles.find(role => role.role === "worker").handlingMs, null);
});

test("efficiency records are summarised only when supplied", () => {
  const record = (model, input, output) => ({
    schema_version: "1.0", run_id: "board-issues", task_class: null, harness: "codex", gateway: null,
    route: "codex/native-or-configured", upstream_model: model, repository_revision: null, elapsed_ms: 1000,
    usage_scope: "task", usage: { input, cached_input: null, cache_creation: null, output, reported_cost: null, availability: { input: "", cached_input: "not reported", cache_creation: "not reported", output: "", reported_cost: "not reported" } },
    attempt: 1, acceptance: { status: "unknown", evidence_ref: null, provenance: "unknown" }, source_kind: "test", notes: []
  });
  const run = { ...scenario("working"), efficiency: { source: "records.jsonl", records: [record("model-a", 100, 20), record("model-a", 50, null)], matched: 2, other_runs: 0, invalid: 0, error: null } };
  const model = buildModel(run, reader);
  assert.equal(model.efficiency.available, true);
  assert.equal(model.efficiency.totals.input.value, 150);
  assert.equal(model.efficiency.totals.output.value, 20);
  assert.equal(model.efficiency.totals.output.reported, 1);
  assert.equal(model.efficiency.totals.cost.value, null);
  assert.equal(model.efficiency.byModel[0].model, "model-a");
  const none = buildModel({ ...scenario("working"), efficiency: { source: "records.jsonl", records: [], other_runs: 3, invalid: 0, error: null } }, reader);
  assert.equal(none.efficiency.available, false);
  assert.match(none.efficiency.reason, /match this task/);
});

/* Bundle and template */

test("the committed app.js was built from the current dashboard sources", async () => {
  const { sourceDigest } = await import("../app/source-digest.mjs");
  const digest = sourceDigest(path.resolve(__dirname, "../app"));
  const bundle = fs.readFileSync(path.join(dashboardRoot, "app.js"), "utf8");
  assert.ok(bundle.startsWith(`/* CouncilFlow dashboard bundle. Source: demo/dashboard/app (sha256 ${digest}).`),
    "app.js is stale: run `npm run build` in demo/dashboard/app");
  assert.ok(!/<\/script/i.test(bundle), "the bundle must not close the inline script element");
});

test("the template keeps the publisher's inline points and an accessible loading status", () => {
  const html = fs.readFileSync(path.join(dashboardRoot, "index.html"), "utf8");
  assert.ok(html.includes('<link rel="stylesheet" href="styles.css">'));
  assert.ok(html.includes('<script src="run-reader.js"></script>\n    <script src="app.js"></script>'));
  assert.ok(html.includes('id="councilflow-root"'));
  const app = fs.readFileSync(path.resolve(__dirname, "../app/src/App.jsx"), "utf8");
  assert.match(app, /className="loading" role="status" aria-live="polite"/);
});
