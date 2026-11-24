(function () {
  "use strict";

  const $ = id => document.getElementById(id);
  const folderInput = $("folder-fallback");
  const fileInput = $("file-picker");
  const loadingState = $("loading-state");
  const reader = window.CouncilFlowRunReader;
  let directoryHandle = null;
  let importedFiles = null;
  let watchTimer = null;
  let autoConnected = false;
  let autoRefreshMeta = null;
  let directoryScanInProgress = false;
  let folderReadFailed = false;
  let lastSnapshot = null;
  const MAX_JSON_BYTES = 65536;
  const MAX_JSON_FILES = 1024;
  const MAX_DIRECTORY_DEPTH = 16;
  const MAX_TOTAL_JSON_BYTES = 16 * 1024 * 1024;
  const MAX_VISIBLE_ISSUES = 20;
  const ISSUE_PHRASES = {
    duplicate_message_id: id => `Two messages use the same id: ${id}.`,
    cross_run_parent: id => `Message ${id} replies to a message from a different task, plan or plan revision.`,
    cross_attempt_parent: id => `Message ${id} replies to a message from a different attempt.`,
    unsupported_contract: id => `Message ${id} uses an unsupported protocol or version.`,
    invalid_identity: id => `Message ${id} has an invalid id, type, plan, task, attempt or plan revision.`,
    invalid_envelope: id => `Message ${id} has an invalid sender, recipient, reply link, payload or evidence list.`,
    invalid_route: id => `Message ${id} was sent between roles that should not exchange this message type.`,
    invalid_plan_publication: id => `Plan publication ${id} is not a valid Planner publication with acceptance ids.`,
    invalid_assignment: id => `Assignment ${id} is missing its acceptance ids or instructions.`,
    invalid_report: id => `Report ${id} is missing its acceptance ids or has an unknown status.`,
    invalid_final_check: id => `Final check ${id} is missing its results or acceptance ids, or has an unknown status.`,
    invalid_decision: id => `Decision ${id} is missing its report ids or has an unknown disposition.`,
    missing_criterion_evidence: id => `No evidence was recorded for criterion ${id}.`,
    report_without_matching_assignment: id => `Report ${id} does not match any assignment.`,
    final_check_without_progress: id => `Final check ${id} has no matching progress record.`
  };
  const ISSUE_FALLBACK_DETAILS = {
    unsupported_contract: "Unknown packet",
    invalid_identity: "Packet identity or type is invalid."
  };

  function formatIssueLine(issue) {
    const detail = issue && issue.detail !== undefined ? String(issue.detail) : "";
    const code = issue && issue.code;
    if (!code || !Object.prototype.hasOwnProperty.call(ISSUE_PHRASES, code)) return detail;
    if (Object.prototype.hasOwnProperty.call(ISSUE_FALLBACK_DETAILS, code) && detail === ISSUE_FALLBACK_DETAILS[code]) return detail;
    return ISSUE_PHRASES[code](detail);
  }

  function setConnection(label, state) {
    const element = $("connection-state");
    element.lastElementChild.textContent = label;
    element.dataset.state = state;
  }

  function setLoading(message) {
    loadingState.textContent = message;
    loadingState.hidden = !message;
  }

  function nextPaint() {
    return new Promise(resolve => {
      if (typeof window.requestAnimationFrame === "function") window.requestAnimationFrame(resolve);
      else window.setTimeout(resolve, 0);
    });
  }

  function createIcon(role) {
    const paths = {
      planner: '<path d="M5 4.5h10l4 4v11H5z"/><path d="M15 4.5v4h4M8 12h8M8 15.5h5"/>',
      manager: '<circle cx="12" cy="12" r="2.5"/><path d="M12 9.5V4M9.5 12H4m10.5 0H20M12 14.5V20M12 4l-2 2m2-2 2 2M4 12l2-2m-2 2 2 2m14-2-2-2m2 2-2 2m-6 8-2-2m2 2 2-2"/>',
      worker: '<path d="m14.5 6.5 3-3 3 3-3 3M4 20l8.7-8.7M11.5 6.5a5 5 0 0 0 6 6l-7.8 7.8a2.1 2.1 0 0 1-3-3l7.8-7.8"/>',
      tester: '<path d="m8 3 8 0M10 3v5l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/><path d="M8 14h8M10 17h4"/>',
      reviewer: '<circle cx="9" cy="9" r="5"/><path d="m13 13 5.5 5.5M7 9l1.5 1.5L11 7.8"/>'
    };
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = paths[role] || paths.planner;
    return svg;
  }

  function renderStages(stages) {
    const list = $("role-list");
    list.replaceChildren();
    for (const stage of stages) {
      const item = document.createElement("li");
      item.className = `role-step role-${stage.role} tone-${stage.tone}`;
      const tile = document.createElement("div");
      tile.className = "role-tile";
      tile.append(createIcon(stage.role));
      const name = document.createElement("span");
      name.className = "role-name";
      name.textContent = stage.label;
      const state = document.createElement("span");
      state.className = "role-state";
      state.textContent = stage.state;
      item.append(tile, name, state);
      list.append(item);
    }
  }

  function renderCriteria(snapshot) {
    const list = $("criteria-list");
    list.replaceChildren();
    if (!snapshot.criteria.length) {
      const note = document.createElement("li");
      note.className = "criteria-empty";
      note.textContent = "Original acceptance details are not available in this run folder.";
      list.append(note);
      return;
    }
    for (const criterion of snapshot.criteria) {
      const item = document.createElement("li");
      item.className = `criterion criterion-${criterion.status}`;
      const icon = document.createElement("span");
      icon.className = "criterion-state";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = criterion.status === "passed" ? "✓" : criterion.status === "failed" ? "×" : criterion.status === "blocked" ? "!" : "·";
      const body = document.createElement("span");
      body.className = "criterion-copy";
      const title = document.createElement("strong");
      title.textContent = criterion.id;
      const description = document.createElement("span");
      description.textContent = criterion.text;
      body.append(title, description);
      const status = document.createElement("span");
      status.className = "criterion-label";
      status.textContent = criterion.status === "unchecked" ? "Not checked" : `${criterion.status} · ${criterion.evidenceCount} refs`;
      item.append(icon, body, status);
      list.append(item);
    }
  }

  function renderActivity(snapshot) {
    const list = $("activity-list");
    list.replaceChildren();
    $("activity-count").textContent = snapshot.activity.length === 1 ? "1 recorded event" : `${snapshot.activity.length} recorded events`;
    for (const event of snapshot.activity.slice().reverse()) {
      const item = document.createElement("li");
      item.className = "activity-item";
      const marker = document.createElement("span");
      marker.className = `activity-marker role-${event.role}`;
      marker.setAttribute("aria-hidden", "true");
      const copy = document.createElement("span");
      copy.className = "activity-copy";
      copy.textContent = event.label;
      const type = document.createElement("span");
      type.className = "activity-kind";
      type.textContent = event.type;
      item.append(marker, copy, type);
      list.append(item);
    }
    if (!snapshot.activity.length) {
      const item = document.createElement("li");
      item.className = "activity-empty";
      item.textContent = "No workflow packets are available yet.";
      list.append(item);
    }
  }

  function renderSnapshot(snapshot) {
    $("empty-state").hidden = true;
    $("board").hidden = false;
    $("run-summary").textContent = snapshot.taskId ? `Task ${snapshot.taskId}` : "No run identity found";
    $("run-health").textContent = snapshot.valid ? "Records linked" : "Incomplete records";
    $("run-health").className = `status-badge ${snapshot.valid ? "status-good" : "status-warning"}`;
    $("current-activity").textContent = snapshot.current ? snapshot.current.label : "Waiting for the first packet";
    $("acceptance-count").textContent = !snapshot.valid
      ? "Incomplete"
      : snapshot.progress.total
      ? `${snapshot.progress.passed} / ${snapshot.progress.total}`
      : "Not recorded";
    const bar = $("acceptance-progress");
    bar.setAttribute("aria-valuemax", String(snapshot.progress.total));
    bar.setAttribute("aria-valuenow", String(snapshot.progress.passed));
    const percent = snapshot.progress.total ? Math.round((snapshot.progress.passed / snapshot.progress.total) * 100) : 0;
    $("progress-fill").style.width = `${percent}%`;
    $("progress-label").textContent = snapshot.progress.recorded ? `${percent}% recorded by the final check` : "No complete final check recorded";
    $("progress-honesty").textContent = snapshot.valid ? "Packet record · not authenticated" : "Incomplete packet record";
    $("acceptance-caption").textContent = snapshot.progress.recorded ? "Planner final check · informational record" : "Acceptance progress from the selected packets";
    renderStages(snapshot.stages);
    renderCriteria(snapshot);
    renderActivity(snapshot);
    const alert = $("record-alert");
    if (snapshot.issues.length) {
      alert.hidden = false;
      const issues = snapshot.issues;
      const lines = [`${issues.length} record issue${issues.length === 1 ? "" : "s"}:`];
      for (const issue of issues.slice(0, MAX_VISIBLE_ISSUES)) lines.push(`- ${formatIssueLine(issue)}`);
      if (issues.length > MAX_VISIBLE_ISSUES) lines.push(`${issues.length - MAX_VISIBLE_ISSUES} more not shown.`);
      alert.textContent = lines.join("\n");
    } else {
      alert.hidden = true;
      alert.textContent = "";
    }
  }

  function parseJson(text, path) {
    try { return { data: JSON.parse(text.replace(/^\uFEFF/, "")), error: null }; }
    catch { return { data: null, error: `${path}: could not read valid JSON.` }; }
  }

  async function digest(file) {
    if (!window.crypto || !window.crypto.subtle) return null;
    const hash = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
    return [...new Uint8Array(hash)].map(byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function createReadState() { return { files: 0, bytes: 0 }; }

  function reserveFile(state, path) {
    if (state.files + 1 > MAX_JSON_FILES) {
      throw new Error(`${path}: selected input exceeds ${MAX_JSON_FILES} JSON files.`);
    }
    state.files += 1;
  }

  function validateFileSize(file, path, state) {
    if (!Number.isSafeInteger(file.size) || file.size < 0) {
      throw new Error(`${path}: JSON file size is unavailable.`);
    }
    if (file.size > MAX_JSON_BYTES) {
      throw new Error(`${path}: JSON file exceeds ${MAX_JSON_BYTES.toLocaleString()} bytes.`);
    }
    if (state.bytes + file.size > MAX_TOTAL_JSON_BYTES) {
      throw new Error(`${path}: selected JSON input exceeds 16 MiB (${MAX_TOTAL_JSON_BYTES.toLocaleString()} bytes).`);
    }
    state.bytes += file.size;
  }

  async function loadFile(file, path, state, countReserved = false) {
    if (!countReserved) reserveFile(state, path);
    validateFileSize(file, path, state);
    const parsed = parseJson(await file.text(), path);
    const normalized = path.replace(/\\/g, "/");
    const isMessageFile = normalized.split("/").includes("messages") || /(?:message|packet)[^/]*\.json$/i.test(normalized);
    return { name: file.name, path: normalized, data: parsed.data, error: parsed.error, isMessageFile, sha256: await digest(file) };
  }

  async function filesFromHandle(directory, prefix, state, depth = 0) {
    if (depth > MAX_DIRECTORY_DEPTH) {
      throw new Error(`${prefix || "Selected folder"}: directory depth exceeds ${MAX_DIRECTORY_DEPTH}.`);
    }
    const items = [];
    for await (const [name, handle] of directory.entries()) {
      const path = prefix ? `${prefix}/${name}` : name;
      if (handle.kind === "directory") items.push(...await filesFromHandle(handle, path, state, depth + 1));
      else if (name.toLowerCase().endsWith(".json")) {
        reserveFile(state, path);
        items.push(await loadFile(await handle.getFile(), path, state, true));
      }
    }
    return items;
  }

  async function showFiles(items, loadingMessage = "Reading current run packets") {
    if (loadingMessage) {
      setLoading(loadingMessage);
      await nextPaint();
    }
    try {
      const parsed = items.filter(item => item.name.toLowerCase().endsWith(".json"));
      const snapshot = reader.buildSnapshot(parsed.map(item => ({ ...item, data: item.data })));
      const readErrors = parsed.filter(item => item.error).map(item => ({ detail: item.error }));
      snapshot.issues.push(...readErrors);
      if (readErrors.length) snapshot.valid = false;
      lastSnapshot = snapshot;
      renderSnapshot(snapshot);
      $("refresh-run").disabled = false;
    } finally {
      if (loadingMessage) setLoading("");
    }
  }

  function showIncompleteRead(error) {
    const empty = {
      valid: false, issues: [], taskId: null, planId: null, stages: [], criteria: [], activity: [], current: null,
      progress: { passed: 0, total: 0, recorded: false }, disposition: "Run in progress", sourceNotice: ""
    };
    const snapshot = lastSnapshot
      ? { ...lastSnapshot, progress: { ...lastSnapshot.progress }, criteria: lastSnapshot.criteria.map(item => ({ ...item })), issues: [...lastSnapshot.issues] }
      : empty;
    snapshot.valid = false;
    snapshot.progress.passed = 0;
    snapshot.progress.recorded = false;
    snapshot.criteria = snapshot.criteria.map(item => ({ ...item, status: "unchecked", evidenceCount: 0 }));
    const detail = error && error.message ? error.message : "Selected run data could not be read completely.";
    snapshot.issues = [...snapshot.issues, { detail }];
    lastSnapshot = snapshot;
    renderSnapshot(snapshot);
  }

  async function refreshDirectory() {
    if (!directoryHandle || directoryScanInProgress) return;
    directoryScanInProgress = true;
    try {
      const initialRead = importedFiles === null;
      if (initialRead) setLoading("Reading selected run folder");
      const items = await filesFromHandle(directoryHandle, "", createReadState());
      importedFiles = items;
      folderReadFailed = false;
      await showFiles(items, initialRead ? "Reading selected run packets" : null);
      setConnection("Watching selected folder", "watching");
    } catch (error) {
      folderReadFailed = true;
      setLoading("");
      stopWatching();
      setConnection("Folder access paused", "warning");
      showIncompleteRead(error);
    } finally {
      directoryScanInProgress = false;
    }
  }

  function stopWatching() {
    if (watchTimer) window.clearInterval(watchTimer);
    watchTimer = null;
    $("refresh-run").textContent = "Refresh";
  }

  function pauseAutoRefreshForManualImport() {
    autoConnected = false;
    if (autoRefreshMeta) autoRefreshMeta.remove();
    autoRefreshMeta = null;
  }

  async function openFolder() {
    if (typeof window.showDirectoryPicker !== "function") {
      folderInput.click();
      return;
    }
    try {
      directoryHandle = await window.showDirectoryPicker({ mode: "read" });
      importedFiles = null;
      folderReadFailed = false;
      stopWatching();
      await refreshDirectory();
      if (!folderReadFailed) {
        watchTimer = window.setInterval(refreshDirectory, 2000);
        $("refresh-run").textContent = "Pause watching";
      }
      $("refresh-run").disabled = false;
      if (!folderReadFailed) setConnection("Watching selected folder", "watching");
    } catch (error) {
      if (error && error.name !== "AbortError") {
        setConnection("Folder could not be opened", "warning");
        const help = $("file-access-help");
        help.textContent = "Folder access was unavailable. Choose the run's JSON messages manually instead.";
      }
    }
  }

  function selectedFilePath(file) { return file.webkitRelativePath || file.name; }

  async function importFiles(fileList, fromFolder) {
    stopWatching();
    directoryHandle = null;
    const files = [...fileList];
    if (!files.length) return;
    setLoading(fromFolder ? "Reading selected run folder" : "Reading selected message files");
    await nextPaint();
    try {
      const state = createReadState();
      const items = [];
      for (const file of files) {
        if (!file.name.toLowerCase().endsWith(".json")) continue;
        items.push(await loadFile(file, selectedFilePath(file), state));
      }
      importedFiles = items;
      await showFiles(items, "Reading selected run packets");
      setConnection(fromFolder ? "Folder snapshot loaded" : "File snapshot loaded", "snapshot");
    } catch (error) {
      showIncompleteRead(error);
      setConnection("Selected run data is incomplete", "warning");
    } finally {
      setLoading("");
    }
  }

  $("choose-folder").addEventListener("click", () => { pauseAutoRefreshForManualImport(); openFolder(); });
  $("empty-open-folder").addEventListener("click", () => { pauseAutoRefreshForManualImport(); openFolder(); });
  $("choose-files").addEventListener("click", () => { pauseAutoRefreshForManualImport(); fileInput.click(); });
  $("empty-open-files").addEventListener("click", () => { pauseAutoRefreshForManualImport(); fileInput.click(); });
  folderInput.addEventListener("change", () => importFiles(folderInput.files, true));
  fileInput.addEventListener("change", () => importFiles(fileInput.files, false));
  $("refresh-run").addEventListener("click", async event => {
    if (autoConnected) {
      window.location.reload();
    } else if (directoryHandle && watchTimer) {
      stopWatching();
      event.currentTarget.textContent = "Refresh";
      setConnection("Watching paused", "snapshot");
    } else if (directoryHandle) {
      await refreshDirectory();
      if (!folderReadFailed) {
        watchTimer = window.setInterval(refreshDirectory, 2000);
        event.currentTarget.textContent = "Pause watching";
      }
    } else if (importedFiles) {
      folderInput.click();
    }
  });
  const embeddedRun = $("councilflow-run-data");
  if (embeddedRun) {
    setLoading("Reading current run packets");
    try {
      const run = JSON.parse(embeddedRun.textContent);
      if (run && Array.isArray(run.files)) {
        autoConnected = true;
        autoRefreshMeta = document.querySelector('meta[http-equiv="refresh"]');
        importedFiles = run.files;
        $("refresh-run").textContent = "Refresh now";
        $("refresh-run").disabled = false;
        showFiles(run.files).catch(error => {
          showIncompleteRead(error);
          setConnection("Embedded run data is incomplete", "warning");
        });
        setConnection(`Connected to ${run.taskId || "active run"} · use Refresh to reload`, "watching");
      } else {
        setLoading("");
        setConnection("Dashboard data is invalid", "warning");
      }
    } catch {
      setLoading("");
      setConnection("Dashboard data is invalid", "warning");
    }
  } else {
    setConnection("Waiting for a run", "idle");
  }
})();
