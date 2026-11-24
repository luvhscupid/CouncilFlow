/* Read CouncilFlow run files chosen in the browser, inside fixed bounds.
   No rendering here: callers get plain entries in the shape the publisher embeds. */
"use strict";

const MAX_JSON_BYTES = 65536;
const MAX_JSON_FILES = 1024;
const MAX_DIRECTORY_DEPTH = 16;
const MAX_TOTAL_JSON_BYTES = 16 * 1024 * 1024;

function createReadState() { return { files: 0, bytes: 0 }; }

function reserveFile(state, path) {
  if (state.files + 1 > MAX_JSON_FILES) {
    throw new Error(`${path}: selected input exceeds ${MAX_JSON_FILES.toLocaleString("en-US")} JSON files.`);
  }
  state.files += 1;
}

function validateFileSize(file, path, state) {
  if (!Number.isSafeInteger(file.size) || file.size < 0) {
    throw new Error(`${path}: JSON file size is unavailable.`);
  }
  if (file.size > MAX_JSON_BYTES) {
    throw new Error(`${path}: JSON file exceeds ${MAX_JSON_BYTES.toLocaleString("en-US")} bytes.`);
  }
  if (state.bytes + file.size > MAX_TOTAL_JSON_BYTES) {
    throw new Error(`${path}: selected JSON input exceeds 16 MiB (${MAX_TOTAL_JSON_BYTES.toLocaleString("en-US")} bytes).`);
  }
  state.bytes += file.size;
}

function parseJson(text, path) {
  try { return { data: JSON.parse(String(text).replace(/^﻿/, "")), error: null }; }
  catch { return { data: null, error: `${path}: could not read valid JSON.` }; }
}

async function digest(file, subtle) {
  if (!subtle || typeof file.arrayBuffer !== "function") return null;
  const hash = await subtle.digest("SHA-256", await file.arrayBuffer());
  return [...new Uint8Array(hash)].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function modifiedTime(file) {
  return Number.isFinite(file.lastModified) && file.lastModified > 0 ? new Date(file.lastModified).toISOString() : null;
}

async function loadFile(file, path, state, options = {}) {
  if (!options.reserved) reserveFile(state, path);
  validateFileSize(file, path, state);
  const parsed = parseJson(await file.text(), path);
  const normalized = path.replace(/\\/g, "/");
  const isMessageFile = normalized.split("/").includes("messages") || /(?:message|packet)[^/]*\.json$/i.test(normalized);
  return {
    name: file.name, path: normalized, data: parsed.data, error: parsed.error, isMessageFile,
    sha256: await digest(file, options.subtle), modified: modifiedTime(file)
  };
}

async function filesFromDirectory(directory, state, options = {}, prefix = "", depth = 0) {
  if (depth > MAX_DIRECTORY_DEPTH) {
    throw new Error(`${prefix || "Selected folder"}: directory depth exceeds ${MAX_DIRECTORY_DEPTH}.`);
  }
  const items = [];
  for await (const [name, handle] of directory.entries()) {
    const path = prefix ? `${prefix}/${name}` : name;
    if (handle.kind === "directory") items.push(...await filesFromDirectory(handle, state, options, path, depth + 1));
    else if (name.toLowerCase().endsWith(".json")) {
      reserveFile(state, path);
      items.push(await loadFile(await handle.getFile(), path, state, { ...options, reserved: true }));
    }
  }
  return items;
}

async function filesFromList(fileList, options = {}) {
  const state = createReadState();
  const items = [];
  for (const file of [...fileList]) {
    if (!String(file.name).toLowerCase().endsWith(".json")) continue;
    items.push(await loadFile(file, file.webkitRelativePath || file.name, state, options));
  }
  return items;
}

/* Poll a directory handle without overlapping scans. Returns a controller. */
function watchDirectory(directory, { intervalMs = 2000, onFiles, onError, subtle, timers } = {}) {
  const clock = timers || { setInterval, clearInterval };
  let timer = null;
  let scanning = false;
  async function scan() {
    if (scanning) return false;
    scanning = true;
    try {
      const files = await filesFromDirectory(directory, createReadState(), { subtle });
      if (onFiles) onFiles(files);
      return true;
    } catch (error) {
      stop();
      if (onError) onError(error);
      return false;
    } finally {
      scanning = false;
    }
  }
  function start() {
    if (!timer) timer = clock.setInterval(scan, intervalMs);
  }
  function stop() {
    if (timer) clock.clearInterval(timer);
    timer = null;
  }
  return { scan, start, stop, get watching() { return timer !== null; } };
}

module.exports = {
  MAX_JSON_BYTES, MAX_JSON_FILES, MAX_DIRECTORY_DEPTH, MAX_TOTAL_JSON_BYTES,
  createReadState, loadFile, filesFromDirectory, filesFromList, watchDirectory, parseJson
};
