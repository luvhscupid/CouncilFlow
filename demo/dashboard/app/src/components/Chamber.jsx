import React, { useMemo } from "react";
import Icon from "./Icon.jsx";

const W = 760;
const H = 650;
const C = { x: 380, y: 330 };
const RING = 205;
const ORBIT = 276;

function polar(angle, radius) {
  const r = (angle * Math.PI) / 180;
  return { x: C.x + radius * Math.cos(r), y: C.y + radius * Math.sin(r) };
}

export const POSITIONS = {
  manager: { ...C, r: 48, label: "below" },
  planner: { ...polar(-90, RING), r: 36, label: "right" },
  worker: { ...polar(0, RING), r: 36, label: "below" },
  tester: { ...polar(90, RING), r: 36, label: "right" },
  reviewer: { ...polar(180, RING), r: 36, label: "below" },
  owner: { ...polar(-141, ORBIT + 52), r: 30, label: "below" }
};

function edgeGeometry(from, to, bend) {
  const a = POSITIONS[from];
  const b = POSITIONS[to];
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const length = Math.hypot(dx, dy) || 1;
  const ux = dx / length;
  const uy = dy / length;
  const nx = -uy;
  const ny = ux;
  const start = { x: a.x + ux * (a.r + 8) + nx * bend * 0.35, y: a.y + uy * (a.r + 8) + ny * bend * 0.35 };
  const end = { x: b.x - ux * (b.r + 10) + nx * bend * 0.35, y: b.y - uy * (b.r + 10) + ny * bend * 0.35 };
  const mid = { x: (a.x + b.x) / 2 + nx * bend, y: (a.y + b.y) / 2 + ny * bend };
  return {
    d: `M${start.x.toFixed(1)} ${start.y.toFixed(1)} Q${mid.x.toFixed(1)} ${mid.y.toFixed(1)} ${end.x.toFixed(1)} ${end.y.toFixed(1)}`,
    label: { x: 0.25 * start.x + 0.5 * mid.x + 0.25 * end.x, y: 0.25 * start.y + 0.5 * mid.y + 0.25 * end.y }
  };
}

const GEOMETRY = {};
function geometry(route) {
  if (!GEOMETRY[route.id]) GEOMETRY[route.id] = edgeGeometry(route.from, route.to, 20);
  return GEOMETRY[route.id];
}

function arcPath(startAngle, endAngle, radius) {
  const a = polar(startAngle, radius);
  const b = polar(endAngle, radius);
  const large = endAngle - startAngle > 180 ? 1 : 0;
  return `M${a.x.toFixed(2)} ${a.y.toFixed(2)} A${radius} ${radius} 0 ${large} 1 ${b.x.toFixed(2)} ${b.y.toFixed(2)}`;
}

const BADGE = { completed: "check", failed: "cross", blocked: "alert" };

function Node({ role, onSelect, selected, reduced }) {
  const p = POSITIONS[role.role];
  const state = role.state.key;
  const busy = ["working", "testing", "reviewing", "planning"].includes(state);
  const badge = BADGE[state];
  const iconSize = role.role === "manager" ? 32 : 24;
  const side = p.label === "right";
  const lx = side ? p.r + 16 : 0;
  const ly = side ? -4 : p.r + 24;
  return (
    <g
      className={`node node-${role.role} state-${state}${selected ? " is-selected" : ""}`}
      transform={`translate(${p.x} ${p.y})`}
      role="button"
      tabIndex={0}
      aria-label={`${role.name}: ${role.state.label}. Open details.`}
      aria-pressed={selected}
      onClick={() => onSelect(role.role)}
      onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(role.role); } }}
    >
      <circle className="node-halo" r={p.r + 18} />
      <circle className="node-body" r={p.r} />
      <circle className="node-rim" r={p.r} />
      {busy ? <circle className={`node-orbit${reduced ? "" : " is-spinning"}`} r={p.r + 7} pathLength="100" /> : null}
      <g transform={`translate(${-iconSize / 2} ${-iconSize / 2})`} className="node-glyph">
        <Icon name={role.role} size={iconSize} />
      </g>
      {badge ? (
        <g className={`node-badge badge-${state}`} transform={`translate(${p.r * 0.72} ${-p.r * 0.72})`}>
          <circle r="11" />
          <g transform="translate(-7 -7)"><Icon name={badge} size={14} /></g>
        </g>
      ) : null}
      <text className="node-name" x={lx} y={ly} textAnchor={side ? "start" : "middle"}>{role.name}</text>
      <text className="node-state" x={lx} y={ly + 18} textAnchor={side ? "start" : "middle"}>{role.state.label}</text>
    </g>
  );
}

export default function Chamber({ model, selectedRole, onSelectRole, reduced, compact = false }) {
  const roles = useMemo(() => new Map(model.roles.map(role => [role.role, role])), [model.roles]);
  const maxCount = Math.max(1, ...model.routes.map(route => route.count));
  const steps = model.lifecycle.steps;
  const span = 360 / steps.length;
  const latest = model.latest;

  return (
    <figure className={`chamber${compact ? " is-compact" : ""}`} aria-labelledby="chamber-caption">
      <svg viewBox={`0 24 ${W} ${H - 24}`} className="chamber-svg" role="group" aria-label="CouncilFlow roles and the handoffs recorded between them">
        <defs>
          <radialGradient id="chamber-floor" cx="50%" cy="50%" r="50%">
            <stop offset="0%" className="floor-stop-in" />
            <stop offset="100%" className="floor-stop-out" />
          </radialGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          {model.routes.map(route => (
            <path key={route.id} id={`route-${route.id.replace(">", "-")}`} d={geometry(route).d} />
          ))}
        </defs>

        <circle cx={C.x} cy={C.y} r={ORBIT + 30} fill="url(#chamber-floor)" className="chamber-floor" />
        <circle cx={C.x} cy={C.y} r={RING} className="chamber-ring" />
        <circle cx={C.x} cy={C.y} r={RING - 70} className="chamber-ring is-inner" />

        <g className="orbit" aria-hidden="true">
          {steps.map((step, index) => {
            const start = -90 + index * span + 1.6;
            const end = -90 + (index + 1) * span - 1.6;
            return <path key={step.key} d={arcPath(start, end, ORBIT)} className={`orbit-seg seg-${step.status} role-stroke-${step.role}`} />;
          })}
          {steps.map((step, index) => {
            const mid = -90 + (index + 0.5) * span;
            const p = polar(mid, ORBIT + 20);
            return step.status === "current" || step.status === "active" ? (
              <circle key={step.key} cx={p.x} cy={p.y} r="4" className={`orbit-cursor${reduced ? "" : " is-pulsing"}`} />
            ) : null;
          })}
        </g>

        <g className="edges">
          {model.routes.map(route => {
            const id = `route-${route.id.replace(">", "-")}`;
            const weight = route.count ? 1.4 + (route.count / maxCount) * 3 : 1.2;
            return (
              <g key={route.id} className={`edge edge-from-${route.from}${route.count ? " has-traffic" : ""}${route.recorded ? "" : " is-unrecorded"}${route.latest ? " is-latest" : ""}`}>
                <use href={`#${id}`} className="edge-line" style={{ strokeWidth: weight }} />
                {route.count ? (
                  <g className="edge-count" transform={`translate(${geometry(route).label.x.toFixed(1)} ${geometry(route).label.y.toFixed(1)})`}>
                    <title>{`${route.count} ${route.label} packet${route.count === 1 ? "" : "s"}`}</title>
                    <circle r="9" />
                    <text dy="3.8" textAnchor="middle">{route.count}</text>
                  </g>
                ) : null}
              </g>
            );
          })}
          {latest && !reduced && !model.lifecycle.complete ? (
            <g className={`comet role-fill-${latest.from}`} filter="url(#glow)" aria-hidden="true">
              <circle r="5">
                <animateMotion dur="2.4s" repeatCount="indefinite" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.45 0 0.2 1">
                  <mpath href={`#route-${latest.from}-${latest.to}`} />
                </animateMotion>
              </circle>
              <circle r="2.5" className="comet-tail">
                <animateMotion dur="2.4s" begin="0.12s" repeatCount="indefinite" keyPoints="0;1" keyTimes="0;1" calcMode="spline" keySplines="0.45 0 0.2 1">
                  <mpath href={`#route-${latest.from}-${latest.to}`} />
                </animateMotion>
              </circle>
            </g>
          ) : null}
        </g>

        <g className="nodes">
          {["owner", "planner", "worker", "tester", "reviewer", "manager"].map(key => roles.get(key) ? (
            <Node key={key} role={roles.get(key)} onSelect={onSelectRole} selected={selectedRole === key} reduced={reduced} />
          ) : null)}
        </g>
      </svg>
      {compact ? null : (
        <ul className="role-strip" aria-label="Role states">
          {model.roles.map(role => (
            <li key={role.role}>
              <button type="button" className={`role-strip-item role-scope-${role.role}`} onClick={() => onSelectRole(role.role)}>
                <Icon name={role.role} size={16} />
                <span className="role-strip-name">{role.name}</span>
                <span className={`state-pill state-${role.state.key}`}>{role.state.label}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <figcaption id="chamber-caption" className="chamber-caption">
        {latest ? (
          <>
            <span className={`dot role-bg-${latest.from}`} aria-hidden="true" />
            <span>Latest handoff: <strong>{latest.title}</strong></span>
          </>
        ) : <span>No handoffs recorded yet.</span>}
        <span className="caption-legend">
          <span className="legend-line" aria-hidden="true" /> recorded route
          <span className="legend-line is-dashed" aria-hidden="true" /> outside packets
        </span>
      </figcaption>
    </figure>
  );
}
