import React, { useMemo, useState } from "react";
import Icon from "./Icon.jsx";
import { clock, relative, sentence } from "../lib/format.js";
import { ROLE_NAMES } from "../data/council-model.js";

const OUTCOME_TEXT = { passed: "Passed", failed: "Failed", blocked: "Blocked", active: "In progress", rework: "Rework", neutral: "Recorded" };

export function OutcomeBadge({ outcome }) {
  return <span className={`badge badge-${outcome}`}>{OUTCOME_TEXT[outcome] || "Recorded"}</span>;
}

export function RoleTag({ role, instance }) {
  return (
    <span className={`role-tag role-tint-${role}`}>
      <Icon name={role} size={14} />
      <span>{ROLE_NAMES[role] || sentence(role)}</span>
      {instance && instance !== role ? <span className="role-instance">{instance}</span> : null}
    </span>
  );
}

export default function ActivityFeed({ model, freshIds, onOpenPacket, now, limit, title = "Activity", showFilter = true }) {
  const [filter, setFilter] = useState("all");
  const roles = useMemo(() => [...new Set(model.packets.map(packet => packet.from))], [model.packets]);
  const items = model.packets.filter(packet => filter === "all" || packet.from === filter || packet.to === filter).slice().reverse();
  const shown = limit ? items.slice(0, limit) : items;

  return (
    <section className="panel activity-panel" aria-labelledby="activity-title">
      <header className="panel-head">
        <div>
          <h2 id="activity-title">{title}</h2>
          <p className="panel-sub">Newest first, ordered by each packet's reply link</p>
        </div>
        {showFilter && roles.length > 1 ? (
          <div className="segmented" role="group" aria-label="Filter activity by role">
            <button type="button" aria-pressed={filter === "all"} onClick={() => setFilter("all")}>All</button>
            {roles.map(role => (
              <button key={role} type="button" aria-pressed={filter === role} onClick={() => setFilter(role)}>{ROLE_NAMES[role]}</button>
            ))}
          </div>
        ) : null}
      </header>
      {shown.length ? (
        <ol className="feed">
          {shown.map(packet => (
            <li key={packet.id} className={`feed-item${freshIds && freshIds.has(packet.id) ? " is-fresh" : ""}`}>
              <span className={`feed-rail role-bg-${packet.from}`} aria-hidden="true" />
              <button type="button" className="feed-body" onClick={() => onOpenPacket(packet.id)}>
                <span className="feed-top">
                  <RoleTag role={packet.from} instance={packet.fromInstance} />
                  <Icon name="arrow" size={14} className="feed-arrow" />
                  <RoleTag role={packet.to} instance={packet.toInstance} />
                </span>
                <span className="feed-title"><span>{packet.title}</span><OutcomeBadge outcome={packet.outcome} /></span>
                {packet.detail.summary || packet.detail.objective ? (
                  <span className="feed-summary">{packet.detail.summary || packet.detail.objective}</span>
                ) : null}
                <span className="feed-meta">
                  <span className="mono">{packet.id}</span>
                  <span>{packet.type}</span>
                  <span>{packet.attempt}</span>
                  {packet.time !== null ? <span title={`File written ${new Date(packet.time).toLocaleString()}`}>{clock(packet.time)}{now ? `, ${relative(packet.time, now)}` : ""}</span> : <span>No file time</span>}
                </span>
              </button>
            </li>
          ))}
        </ol>
      ) : (
        <div className="empty-inline">
          <Icon name="layers" size={22} />
          <p>No valid packets yet. Activity appears here as the Manager saves each handoff.</p>
        </div>
      )}
      {limit && items.length > limit ? <p className="panel-foot">{items.length - limit} older packets in Executions.</p> : null}
    </section>
  );
}

/* Reader details can repeat the file path; show the short name once. */
function issueText(detail) {
  const short = String(detail).replace(/(?:[^\s:]*\/)?\.councilflow\/runs\/[^/\s]+\/(?:messages\/)?/g, "");
  return short.replace(/^([^\s:]+\.json): \1: /, "$1: ");
}

export function RecordHealth({ model, mode }) {
  const issues = model.issues;
  const fileCount = model.files.length;
  const shown = issues.slice(0, 20);
  return (
    <section className={`panel health-panel${model.run.valid ? " is-good" : " is-warning"}`} aria-labelledby="health-title">
      <header className="panel-head">
        <div>
          <h2 id="health-title">Record health</h2>
          <p className="panel-sub">{fileCount} files read{mode === "embedded" ? " by the publisher" : ""}</p>
        </div>
        <span className={`badge ${model.run.valid ? "badge-passed" : "badge-blocked"}`}>{model.run.valid ? "Records linked" : `${issues.length} issue${issues.length === 1 ? "" : "s"}`}</span>
      </header>
      {issues.length ? (
        <ul className="issue-list" role="status" aria-live="polite">
          {shown.map((issue, index) => (
            <li key={`${issue.code}-${index}`}>
              <Icon name="alert" size={14} />
              <span>{issueText(issue.detail)}{issue.code ? <span className="issue-code"> {issue.code}</span> : null}</span>
            </li>
          ))}
          {issues.length > shown.length ? <li className="issue-more">{issues.length - shown.length} more not shown.</li> : null}
        </ul>
      ) : (
        <p className="health-ok"><Icon name="shield" size={16} /> Every packet validated and links to the published plan.</p>
      )}
      <p className="trust-note">Packets are informational records. They do not authenticate who sent them or prove host activity.</p>
    </section>
  );
}
