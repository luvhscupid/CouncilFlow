export function plural(count, one, many = `${one}s`) {
  return `${count.toLocaleString("en-US")} ${count === 1 ? one : many}`;
}

export function duration(ms) {
  if (ms === null || ms === undefined || !Number.isFinite(ms)) return "Unknown";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return seconds % 60 ? `${minutes}m ${String(seconds % 60).padStart(2, "0")}s` : `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return minutes % 60 ? `${hours}h ${String(minutes % 60).padStart(2, "0")}m` : `${hours}h`;
  return `${Math.floor(hours / 24)}d ${hours % 24}h`;
}

export function clock(time) {
  if (time === null || time === undefined) return null;
  const date = new Date(time);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function dateTime(time) {
  if (time === null || time === undefined) return null;
  const date = new Date(time);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function relative(time, now) {
  if (time === null || time === undefined || !now) return null;
  const diff = Math.max(0, now - time);
  if (diff < 45000) return "just now";
  return `${duration(diff)} ago`;
}

export function shortHash(hash) {
  return typeof hash === "string" && hash.length > 12 ? `${hash.slice(0, 8)}…${hash.slice(-4)}` : hash || "";
}

export function tokens(value) {
  if (value === null || value === undefined) return "Not reported";
  if (value >= 1e6) return `${(value / 1e6).toFixed(value >= 1e7 ? 1 : 2)}M`;
  if (value >= 1e4) return `${(value / 1e3).toFixed(1)}k`;
  return value.toLocaleString("en-US");
}

export function sentence(value) {
  const text = String(value || "").replace(/[_.]/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}
