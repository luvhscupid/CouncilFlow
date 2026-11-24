import { useEffect, useRef, useState, useSyncExternalStore } from "react";

const motionQuery = typeof window !== "undefined" && window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;

function subscribeMotion(callback) {
  if (!motionQuery) return () => {};
  motionQuery.addEventListener("change", callback);
  return () => motionQuery.removeEventListener("change", callback);
}

export function useSystemReducedMotion() {
  return useSyncExternalStore(subscribeMotion, () => Boolean(motionQuery && motionQuery.matches), () => false);
}

/* Ease a number toward its target. Jumps straight there when motion is reduced. */
export function useAnimatedNumber(target, { duration = 900, reduced = false } = {}) {
  const [value, setValue] = useState(reduced ? target : 0);
  const fromRef = useRef(reduced ? target : 0);
  useEffect(() => {
    if (reduced || typeof window.requestAnimationFrame !== "function") {
      fromRef.current = target;
      setValue(target);
      return undefined;
    }
    const from = fromRef.current;
    const start = performance.now();
    let frame = 0;
    const step = now => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const next = from + (target - from) * eased;
      fromRef.current = next;
      setValue(next);
      if (t < 1) frame = window.requestAnimationFrame(step);
    };
    frame = window.requestAnimationFrame(step);
    return () => window.cancelAnimationFrame(frame);
  }, [target, duration, reduced]);
  return value;
}

export function useNow(intervalMs = 1000, enabled = true) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!enabled) return undefined;
    const timer = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(timer);
  }, [intervalMs, enabled]);
  return now;
}

export function useEscape(handler, active) {
  useEffect(() => {
    if (!active) return undefined;
    const onKey = event => { if (event.key === "Escape") handler(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handler, active]);
}
