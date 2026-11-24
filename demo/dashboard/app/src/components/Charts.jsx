import React, { useMemo, useState } from "react";
import { ROLE_NAMES } from "../data/council-model.js";
import { duration, tokens } from "../lib/format.js";

/* Horizontal bars. Each row: { key, label, value, display, tone } */
export function BarRows({ rows, label, emptyText, unit = "" }) {
  const [active, setActive] = useState(null);
  const max = Math.max(1, ...rows.map(row => row.value || 0));
  if (!rows.length || rows.every(row => !row.value)) return <p className="muted">{emptyText}</p>;
  const current = rows.find(row => row.key === active);
  return (
    <div className="bars">
      <ul className="bar-rows" aria-label={label}>
        {rows.map(row => (
          <li key={row.key} className={active === row.key ? "is-active" : ""}
            onMouseEnter={() => setActive(row.key)} onMouseLeave={() => setActive(null)}>
            <span className="bar-label">{row.label}</span>
            <span className="bar-track" aria-hidden="true">
              <span className={`bar-fill ${row.tone || ""}`} style={{ width: `${((row.value || 0) / max) * 100}%` }} />
            </span>
            <span className="bar-value num">{row.display !== undefined ? row.display : `${row.value}${unit}`}</span>
          </li>
        ))}
      </ul>
      {current && current.note ? <p className="readout">{current.note}</p> : null}
    </div>
  );
}

export function holdIntervals(model) {
  const timed = model.packets.filter(packet => packet.time !== null);
  const intervals = [];
  for (let index = 1; index < timed.length; index += 1) {
    const previous = timed[index - 1];
    const next = timed[index];
    if (next.time < previous.time) continue;
    intervals.push({ id: `${previous.id}-${next.id}`, role: previous.to, start: previous.time, end: next.time, from: previous, to: next });
  }
  return intervals;
}

export function HoldTimeline({ model }) {
  const intervals = useMemo(() => holdIntervals(model), [model]);
  const [active, setActive] = useState(null);
  if (!intervals.length) {
    return <p className="muted">Needs at least two packets with file write times. Folder imports in some browsers and hand-made packets may not carry them.</p>;
  }
  const start = intervals[0].start;
  const end = intervals[intervals.length - 1].end;
  const total = Math.max(1, end - start);
  const current = intervals.find(item => item.id === active);
  return (
    <div className="hold">
      <div className="hold-track" role="list" aria-label="Who held the work between packets">
        {intervals.map(item => (
          <span key={item.id} role="listitem" tabIndex={0}
            className={`hold-seg role-bg-${item.role}${active === item.id ? " is-active" : ""}`}
            style={{ left: `${((item.start - start) / total) * 100}%`, width: `${Math.max(0.6, ((item.end - item.start) / total) * 100)}%` }}
            aria-label={`${ROLE_NAMES[item.role]} held the work for ${duration(item.end - item.start)}, from ${item.from.id} to ${item.to.id}`}
            onMouseEnter={() => setActive(item.id)} onMouseLeave={() => setActive(null)}
            onFocus={() => setActive(item.id)} onBlur={() => setActive(null)} />
        ))}
      </div>
      <div className="hold-axis num"><span>0</span><span>{duration(total)}</span></div>
      <p className="readout" aria-live="polite">
        {current ? `${ROLE_NAMES[current.role]} held the work for ${duration(current.end - current.start)}: after ${current.from.id} (${current.from.type}) until ${current.to.id} (${current.to.type}).`
          : "Each band is the time between two packet files, colored by the role the earlier packet was addressed to."}
      </p>
    </div>
  );
}

export function TokenStack({ totals }) {
  const parts = [
    { key: "input", label: "Input", value: totals.input.value, tone: "tone-a" },
    { key: "cached", label: "Cached input", value: totals.cachedInput.value, tone: "tone-b" },
    { key: "creation", label: "Cache creation", value: totals.cacheCreation.value, tone: "tone-c" },
    { key: "output", label: "Output", value: totals.output.value, tone: "tone-d" }
  ];
  const known = parts.filter(part => typeof part.value === "number" && part.value > 0);
  const sum = known.reduce((total, part) => total + part.value, 0);
  return (
    <div className="token-stack">
      <div className="stack-bar" aria-hidden="true">
        {known.map(part => <span key={part.key} className={`stack-seg ${part.tone}`} style={{ width: `${(part.value / Math.max(1, sum)) * 100}%` }} />)}
      </div>
      <dl className="stack-legend">
        {parts.map(part => (
          <div key={part.key}>
            <dt><span className={`swatch ${part.tone}`} aria-hidden="true" />{part.label}</dt>
            <dd className="num">{tokens(part.value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
