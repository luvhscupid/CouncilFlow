import React, { useState } from "react";
import { ROLE_NAMES } from "../data/council-model.js";
import { clock } from "../lib/format.js";

const LANES = ["owner", "planner", "manager", "worker", "tester", "reviewer"];
const W = 1100;
const LEFT = 96;
const TOP = 60;
const ROW = 50;

export default function Sequence({ model, onOpenPacket, freshIds }) {
  const [hover, setHover] = useState(null);
  const lanes = LANES;
  const step = (W - LEFT - 40) / (lanes.length - 1);
  const x = role => LEFT + lanes.indexOf(role) * step;
  const rows = [];
  let attempt = null;
  for (const packet of model.packets) {
    if (packet.attempt !== attempt && packet.type !== "plan.publish") {
      attempt = packet.attempt;
      rows.push({ divider: attempt });
    }
    rows.push({ packet });
  }
  const height = TOP + rows.length * ROW + 24;
  const hovered = hover ? model.packets.find(packet => packet.id === hover) : null;

  if (!model.packets.length) {
    return <p className="muted">The sequence appears once the first packet is recorded.</p>;
  }

  return (
    <div className="sequence-wrap">
      <svg className="sequence" viewBox={`0 0 ${W} ${height}`} role="list" aria-label="Packets between roles in reply order">
        {lanes.map(role => (
          <g key={role} className={`lane role-stroke-${role}`} aria-hidden="true">
            <text x={x(role)} y={24} textAnchor="middle" className={`lane-name role-fill-${role}`}>{ROLE_NAMES[role]}</text>
            <line x1={x(role)} x2={x(role)} y1={36} y2={height - 8} className="lane-line" />
          </g>
        ))}
        {rows.map((row, index) => {
          const y = TOP + index * ROW + ROW / 2;
          if (row.divider) {
            return (
              <g key={`d-${row.divider}`} className="attempt-divider" aria-hidden="true">
                <line x1={12} x2={W - 12} y1={y} y2={y} />
                <text x={14} y={y - 6}>{row.divider}</text>
              </g>
            );
          }
          const packet = row.packet;
          const x1 = x(packet.from);
          const x2 = x(packet.to);
          const dir = x2 >= x1 ? 1 : -1;
          return (
            <g key={packet.id} role="listitem" tabIndex={0}
              className={`seq-row outcome-${packet.outcome}${hover === packet.id ? " is-hover" : ""}${freshIds && freshIds.has(packet.id) ? " is-fresh" : ""}`}
              aria-label={`${packet.title}, ${packet.id}`}
              onMouseEnter={() => setHover(packet.id)} onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(packet.id)} onBlur={() => setHover(null)}
              onClick={() => onOpenPacket(packet.id)}
              onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpenPacket(packet.id); } }}>
              <rect x={4} y={y - ROW / 2 + 3} width={W - 8} height={ROW - 6} rx={8} className="seq-hit" />
              <line x1={x1} x2={x2 - dir * 8} y1={y} y2={y} className={`seq-arrow role-stroke-${packet.from}`} />
              <path d={`M${x2} ${y} l${-dir * 10} -5 v10 z`} className={`role-fill-${packet.from}`} />
              <circle cx={x1} cy={y} r={4.5} className={`role-fill-${packet.from}`} />
              <text x={(x1 + x2) / 2} y={y - 8} textAnchor="middle" className="seq-label">{packet.type}</text>
              <text x={LEFT - 22} y={y + 4} textAnchor="end" className="seq-id">{packet.id.length > 7 ? `${packet.id.slice(0, 6)}…` : packet.id}</text>
            </g>
          );
        })}
      </svg>
      <p className="readout" aria-live="polite">
        {hovered ? `${hovered.title}. ${hovered.detail.summary || hovered.detail.objective || ""} ${hovered.time !== null ? `Written ${clock(hovered.time)}.` : ""}` : "Point at or focus a handoff to read it. Select it for the full packet."}
      </p>
    </div>
  );
}
