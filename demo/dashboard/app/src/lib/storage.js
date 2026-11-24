/* Browser storage can be missing or throw (private windows, file:// policies). */
function area(kind) {
  try { return kind === "session" ? window.sessionStorage : window.localStorage; }
  catch { return null; }
}

export function read(key, fallback, kind = "local") {
  try {
    const store = area(kind);
    const raw = store ? store.getItem(key) : null;
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function write(key, value, kind = "local") {
  try {
    const store = area(kind);
    if (store) store.setItem(key, JSON.stringify(value));
  } catch {
    /* Preferences are a convenience; the board works without them. */
  }
}
