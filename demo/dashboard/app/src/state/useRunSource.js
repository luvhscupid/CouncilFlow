import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import loader from "../data/run-loader.js";
import { buildModel } from "../data/council-model.js";
import { read, write } from "../lib/storage.js";

const FOLLOW_KEY = "councilflow.follow";
const FOLLOW_INTERVAL_MS = 3000;

function readEmbedded() {
  const element = document.getElementById("councilflow-run-data");
  if (!element) return { present: false };
  try {
    const run = JSON.parse(element.textContent);
    if (run && Array.isArray(run.files)) return { present: true, run };
    return { present: true, error: "The embedded run data has no file list." };
  } catch {
    return { present: true, error: "The embedded run data is not valid JSON." };
  }
}

function safeModel(input, reader, extraIssue) {
  try {
    const model = buildModel(input, reader);
    if (extraIssue) {
      model.issues = [...model.issues, { code: "read_error", detail: extraIssue }];
      model.run.valid = false;
      model.acceptance = { ...model.acceptance, passed: 0, verified: false, criteria: model.acceptance.criteria.map(item => ({ ...item, status: "unchecked", evidenceCount: 0 })) };
    }
    return model;
  } catch (error) {
    const model = buildModel({ files: [] }, { buildSnapshot: () => ({ valid: false, issues: [], taskId: null, planId: null, stages: [], criteria: [], progress: { passed: 0, total: 0, recorded: false }, activity: [], current: null, disposition: "Waiting for a run" }), validateMessage: () => false, orderMessages: () => [] });
    model.issues = [{ code: "reader_error", detail: error && error.message ? error.message : "The run reader failed." }];
    if (extraIssue) model.issues.push({ code: "read_error", detail: extraIssue });
    return model;
  }
}

export function useRunSource() {
  const reader = typeof window !== "undefined" ? window.CouncilFlowRunReader : null;
  const embedded = useMemo(readEmbedded, []);
  const [source, setSource] = useState(() => embedded.present && embedded.run
    ? { mode: "embedded", files: embedded.run.files, context: embedded.run, readError: null }
    : { mode: "empty", files: null, context: {}, readError: embedded.error || null });
  const [connection, setConnection] = useState(() => embedded.present && embedded.run
    ? { tone: "live", label: `Published snapshot of ${embedded.run.taskId || "the active task"}` }
    : embedded.error ? { tone: "warning", label: "Dashboard data is invalid" } : { tone: "idle", label: "No run open" });
  const [loading, setLoading] = useState("");
  const [lastRead, setLastRead] = useState(() => Date.now());
  const watcherRef = useRef(null);
  const [watching, setWatching] = useState(false);
  const [follow, setFollowState] = useState(() => read(FOLLOW_KEY, true));

  const model = useMemo(() => {
    if (!reader) return safeModel({ files: [] }, { buildSnapshot() { throw new Error("The CouncilFlow run reader did not load."); } });
    if (!source.files) return null;
    return safeModel({ ...source.context, files: source.files }, reader, source.readError);
  }, [reader, source]);

  const finished = Boolean(model && model.lifecycle.complete);
  const followActive = source.mode === "embedded" && follow && !finished;

  useEffect(() => {
    if (!followActive) return undefined;
    const timer = window.setTimeout(() => {
      write("councilflow.scroll", window.scrollY, "session");
      window.location.reload();
    }, FOLLOW_INTERVAL_MS);
    return () => window.clearTimeout(timer);
  }, [followActive, source]);

  useEffect(() => {
    const scroll = read("councilflow.scroll", null, "session");
    if (typeof scroll === "number") {
      write("councilflow.scroll", null, "session");
      window.requestAnimationFrame(() => window.scrollTo(0, scroll));
    }
  }, []);

  useEffect(() => () => { if (watcherRef.current) watcherRef.current.stop(); }, []);

  const setFollow = useCallback(value => {
    setFollowState(value);
    write(FOLLOW_KEY, value);
  }, []);

  const subtle = typeof window !== "undefined" && window.crypto && window.crypto.subtle ? window.crypto.subtle : null;

  const showFailure = useCallback((error, label) => {
    setSource(previous => ({ ...previous, mode: previous.mode === "empty" ? "files" : previous.mode, files: previous.files || [], readError: error && error.message ? error.message : "Selected run data could not be read completely." }));
    setConnection({ tone: "warning", label });
  }, []);

  const openFolder = useCallback(async fallbackInput => {
    if (typeof window.showDirectoryPicker !== "function") {
      if (fallbackInput) fallbackInput.click();
      return;
    }
    let directory;
    try {
      directory = await window.showDirectoryPicker({ mode: "read" });
    } catch (error) {
      if (error && error.name !== "AbortError") setConnection({ tone: "warning", label: "Folder could not be opened" });
      return;
    }
    if (watcherRef.current) watcherRef.current.stop();
    setFollow(false);
    setLoading("Reading the selected run folder");
    const watcher = loader.watchDirectory(directory, {
      subtle,
      onFiles(files) {
        setSource({ mode: "folder", files, context: {}, readError: null });
        setLastRead(Date.now());
        setConnection({ tone: "live", label: `Watching ${directory.name || "the selected folder"}` });
      },
      onError(error) {
        setWatching(false);
        showFailure(error, "Folder reading paused");
      }
    });
    watcherRef.current = watcher;
    const ok = await watcher.scan();
    setLoading("");
    if (ok) {
      watcher.start();
      setWatching(true);
    }
  }, [showFailure, setFollow, subtle]);

  const importFiles = useCallback(async (fileList, fromFolder) => {
    if (!fileList || !fileList.length) return;
    if (watcherRef.current) watcherRef.current.stop();
    setWatching(false);
    setFollow(false);
    setLoading(fromFolder ? "Reading the selected run folder" : "Reading the selected message files");
    try {
      const files = await loader.filesFromList(fileList, { subtle });
      setSource({ mode: "files", files, context: {}, readError: null });
      setLastRead(Date.now());
      setConnection({ tone: "snapshot", label: fromFolder ? "Folder snapshot loaded" : "File snapshot loaded" });
    } catch (error) {
      showFailure(error, "Selected run data is incomplete");
    } finally {
      setLoading("");
    }
  }, [showFailure, setFollow, subtle]);

  const toggleWatch = useCallback(async () => {
    const watcher = watcherRef.current;
    if (!watcher) return;
    if (watcher.watching) {
      watcher.stop();
      setWatching(false);
      setConnection({ tone: "snapshot", label: "Watching paused" });
    } else if (await watcher.scan()) {
      watcher.start();
      setWatching(true);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (source.mode === "embedded") {
      write("councilflow.scroll", window.scrollY, "session");
      window.location.reload();
    } else if (watcherRef.current) {
      await watcherRef.current.scan();
    }
  }, [source.mode]);

  return {
    model, mode: source.mode, connection, loading, lastRead, watching,
    follow, followActive, finished, setFollow,
    openFolder, importFiles, toggleWatch, refresh,
    generatedAt: source.context && source.context.generatedAt ? Date.parse(source.context.generatedAt) : null
  };
}
