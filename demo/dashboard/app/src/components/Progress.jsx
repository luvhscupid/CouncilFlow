import React, { useState } from "react";
import Icon from "./Icon.jsx";
import { useAnimatedNumber } from "../lib/hooks.js";
import { clock, duration, plural } from "../lib/format.js";

const STATUS_TEXT = {
  done: "Recorded", current: "Next expected", active: "In progress", pending: "Not reached",
  gap: "Packet not found", skipped: "Skipped after the failure", failed: "Failed", blocked: "Blocked", rework: "Sent back for rework"
};

export function LifecycleRibbon({ lifecycle, freshIds, reduced, size = "large" }) {
  const empty = lifecycle.done === 0 && !lifecycle.steps.some(step => step.packetId);
  return (
    <div className={`ribbon ribbon-${size}${empty ? " is-indeterminate" : ""}`} role="img"
      aria-label={empty ? "No workflow steps recorded yet" : `${lifecycle.done} of ${lifecycle.total} workflow steps recorded`}>
      {lifecycle.steps.map(step => (
        <span key={step.key}
          className={`ribbon-seg seg-${step.status} role-bg-${step.role}${freshIds && step.packetId && freshIds.has(step.packetId) ? " is-fresh" : ""}${reduced ? "" : " can-animate"}`}
          title={`${step.label}: ${STATUS_TEXT[step.status]}`} />
      ))}
    </div>
  );
}

export default function ProgressPanel({ model, freshIds, reduced, now, onOpenPacket }) {
  const [expanded, setExpanded] = useState(false);
  const { lifecycle, acceptance, timing, run } = model;
  const stepPercent = Math.round((lifecycle.done / lifecycle.total) * 100);
  const verifiedPercent = acceptance.total ? Math.round((acceptance.passed / acceptance.total) * 100) : 0;
  const shownSteps = useAnimatedNumber(stepPercent, { reduced });
  const shownVerified = useAnimatedNumber(verifiedPercent, { reduced });
  const roleInstance = new Map(model.packets.map(packet => [packet.id, packet.fromInstance]));
  const running = run.hasPackets && !lifecycle.complete && !lifecycle.halted;
  const elapsed = timing.available
    ? running && timing.first !== null ? Math.max(0, now - timing.first) : timing.span
    : null;

  let headline;
  if (!run.hasPackets) headline = "Waiting for the first packet";
  else if (lifecycle.complete && acceptance.verified && acceptance.passed === acceptance.total) headline = "Accepted and verified";
  else if (lifecycle.halted) headline = `${lifecycle.halted.label}: ${STATUS_TEXT[lifecycle.halted.status].toLowerCase()}`;
  else if (lifecycle.current) headline = `Next: ${lifecycle.current.label.toLowerCase()}`;
  else headline = run.disposition;

  return (
    <section className="panel progress-panel" aria-labelledby="progress-title">
      <header className="panel-head">
        <div>
          <h2 id="progress-title">Progress</h2>
          <p className="panel-sub">{headline}</p>
        </div>
        <div className="elapsed" title={timing.available ? "Measured from packet file write times, not from authenticated event times." : undefined}>
          <Icon name="clock" size={16} />
          <span className="num">{elapsed !== null ? duration(elapsed) : "No times"}</span>
          <span className="elapsed-note">{timing.available ? (running ? "since first packet" : "first to last packet") : "file times unavailable"}</span>
        </div>
      </header>

      <div className="meter-block">
        <div className="meter-figure">
          <span className="meter-number num">{Math.round(shownSteps)}<small>%</small></span>
          <span className="meter-label">
            <strong>{lifecycle.done} of {lifecycle.total}</strong> workflow steps recorded
            <span className="provenance is-recorded">Counted from packets</span>
          </span>
        </div>
        <LifecycleRibbon lifecycle={lifecycle} freshIds={freshIds} reduced={reduced} />
        {lifecycle.gaps ? <p className="meter-warning"><Icon name="alert" size={14} /> {lifecycle.gaps === 1 ? "1 earlier step has" : `${lifecycle.gaps} earlier steps have`} no packet in this folder.</p> : null}
      </div>

      <div className="meter-block is-acceptance">
        <div className="meter-figure">
          <span className={`meter-number num${acceptance.verified ? "" : " is-muted"}`}>
            {acceptance.verified ? <>{Math.round(shownVerified)}<small>%</small></> : <span className="meter-dash">Not yet</span>}
          </span>
          <span className="meter-label">
            {acceptance.total
              ? <><strong>{acceptance.passed} of {acceptance.total}</strong> acceptance criteria verified</>
              : <>Acceptance criteria are not available</>}
            <span className={`provenance ${acceptance.verified ? "is-verified" : "is-pending"}`}>
              {acceptance.verified ? "Verified by the Planner's final check" : "Counts only after a complete final check"}
            </span>
          </span>
        </div>
        <div className={`acceptance-bar${acceptance.verified ? "" : " is-waiting"}`} role="progressbar"
          aria-label="Acceptance criteria verified by the final check" aria-valuemin={0}
          aria-valuemax={acceptance.total} aria-valuenow={acceptance.passed}>
          <span style={{ width: `${acceptance.verified ? shownVerified : 0}%` }} />
        </div>
        {acceptance.criteria.length ? (
          <ul className="criteria-chips" aria-label="Acceptance criteria">
            {acceptance.criteria.map(item => (
              <li key={item.id} className={`chip chip-${item.status}`} title={item.text}>
                <span className="chip-mark" aria-hidden="true" />{item.id}
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <button type="button" className="disclosure" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>
        {expanded ? "Hide step breakdown" : "Show step breakdown"}
      </button>
      {expanded ? (
        <ol className="step-list">
          {lifecycle.steps.map(step => (
            <li key={step.key} className={`step step-${step.status}`}>
              <span className={`step-dot role-bg-${step.role}`} aria-hidden="true" />
              <span className="step-label">{step.label}</span>
              <span className="step-who">{step.packetId ? roleInstance.get(step.packetId) : ""}</span>
              <span className="step-status">{STATUS_TEXT[step.status]}</span>
              <span className="step-time num">{step.modified ? clock(Date.parse(step.modified)) : ""}</span>
              {step.packetId ? (
                <button type="button" className="link-button" onClick={() => onOpenPacket(step.packetId)}>{step.packetId}</button>
              ) : <span />}
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
