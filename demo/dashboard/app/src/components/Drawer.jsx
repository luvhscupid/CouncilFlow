import React, { useCallback, useEffect, useRef } from "react";
import Icon from "./Icon.jsx";
import { RoleTag, OutcomeBadge } from "./Activity.jsx";
import { clock, dateTime, duration, shortHash } from "../lib/format.js";
import { useEscape } from "../lib/hooks.js";

export function Drawer({ open, onClose, labelledBy, children, accent }) {
  const panelRef = useRef(null);
  const returnRef = useRef(null);
  const close = useCallback(() => onClose(), [onClose]);
  useEscape(close, open);
  useEffect(() => {
    if (!open) return undefined;
    returnRef.current = document.activeElement;
    const frame = window.requestAnimationFrame(() => { if (panelRef.current) panelRef.current.focus(); });
    return () => {
      window.cancelAnimationFrame(frame);
      const target = returnRef.current;
      if (target && typeof target.focus === "function") target.focus();
    };
  }, [open]);
  if (!open) return null;
  return (
    <div className="drawer-layer">
      <div className="drawer-scrim" onClick={close} aria-hidden="true" />
      <aside ref={panelRef} className={`drawer${accent ? ` accent-${accent}` : ""}`} role="dialog" aria-modal="true" aria-labelledby={labelledBy} tabIndex={-1}>
        <button type="button" className="icon-button drawer-close" onClick={close} aria-label="Close details">
          <Icon name="close" size={18} />
        </button>
        {children}
      </aside>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="drawer-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function Lines({ items, empty }) {
  if (!items || !items.length) return empty ? <p className="muted">{empty}</p> : null;
  return <ul className="plain-list">{items.map((item, index) => <li key={index}>{item}</li>)}</ul>;
}

export function AgentDetail({ role, model, onOpenPacket }) {
  const history = role.history.map(id => model.packets.find(packet => packet.id === id)).filter(Boolean).reverse();
  const handling = role.handlingMs;
  return (
    <div className={`detail role-scope-${role.role}`}>
      <header className="detail-head">
        <span className={`detail-glyph role-tint-${role.role}`}><Icon name={role.role} size={30} /></span>
        <div>
          <h2 id="drawer-title">{role.name}</h2>
          <p className="detail-sub">{role.duty}</p>
        </div>
      </header>
      <dl className="facts">
        <div><dt>Status</dt><dd><span className={`state-pill state-${role.state.key}`}>{role.state.label}</span></dd></div>
        <div><dt>Based on</dt><dd>{role.state.sourceId ? <button type="button" className="link-button" onClick={() => onOpenPacket(role.state.sourceId)}>{role.state.sourceId}</button> : "No packet yet"}</dd></div>
        <div><dt>Instances</dt><dd className="mono">{role.instances.length ? role.instances.join(", ") : "None recorded"}</dd></div>
        <div><dt>Packets</dt><dd>{role.sentCount} sent, {role.receivedCount} received</dd></div>
        <div><dt>Model</dt><dd className="muted">{role.model.value || role.model.reason}</dd></div>
        <div><dt>Time on assignment</dt><dd>{handling ? handling.map(duration).join(", ") : <span className="muted">{["worker", "tester", "reviewer"].includes(role.role) ? "Needs an assignment and report with file times" : "Not measured for this role"}</span>}</dd></div>
      </dl>
      {role.currentTask ? (
        <Section title="Current task">
          {role.currentTask.objective ? <p className="lead-text">{role.currentTask.objective}</p> : null}
          {role.currentTask.acceptanceIds.length ? <p className="muted">Covers {role.currentTask.acceptanceIds.join(", ")}</p> : null}
          {role.currentTask.instructions.length ? (
            <details className="instructions">
              <summary>{role.currentTask.instructions.length} instruction{role.currentTask.instructions.length === 1 ? "" : "s"} from {role.currentTask.packetId}</summary>
              <ol>{role.currentTask.instructions.map((item, index) => <li key={index}>{item}</li>)}</ol>
            </details>
          ) : null}
        </Section>
      ) : null}
      {role.responsibilities.length ? (
        <Section title="Responsibilities">
          <Lines items={role.responsibilities} />
          {role.writesCode !== null ? <p className="muted">{role.writesCode ? "May change application code." : "Never changes application code."}</p> : null}
        </Section>
      ) : null}
      <Section title="Activity history">
        {history.length ? (
          <ol className="mini-feed">
            {history.map(packet => (
              <li key={packet.id}>
                <button type="button" onClick={() => onOpenPacket(packet.id)}>
                  <span className={`dot role-bg-${packet.from}`} aria-hidden="true" />
                  <span className="mini-title">{packet.title}</span>
                  <span className="mini-meta mono">{packet.id}</span>
                  <span className="mini-meta">{packet.time !== null ? clock(packet.time) : ""}</span>
                </button>
              </li>
            ))}
          </ol>
        ) : <p className="muted">This role has not sent or received a packet in this run.</p>}
      </Section>
    </div>
  );
}

export function PacketDetail({ packet, onOpenPacket, onOpenRole }) {
  const d = packet.detail;
  return (
    <div className="detail">
      <header className="detail-head">
        <span className={`detail-glyph role-tint-${packet.from}`}><Icon name={packet.from} size={30} /></span>
        <div>
          <h2 id="drawer-title">{packet.title}</h2>
          <p className="detail-sub mono">{packet.id} · {packet.type}</p>
        </div>
      </header>
      <div className="route-line">
        <button type="button" className="tag-button" onClick={() => onOpenRole(packet.from)}><RoleTag role={packet.from} instance={packet.fromInstance} /></button>
        <Icon name="arrow" size={16} />
        <button type="button" className="tag-button" onClick={() => onOpenRole(packet.to)}><RoleTag role={packet.to} instance={packet.toInstance} /></button>
        <OutcomeBadge outcome={packet.outcome} />
      </div>
      <dl className="facts">
        <div><dt>Attempt</dt><dd className="mono">{packet.attempt}</dd></div>
        <div><dt>Replies to</dt><dd>{packet.inReplyTo ? <button type="button" className="link-button" onClick={() => onOpenPacket(packet.inReplyTo)}>{packet.inReplyTo}</button> : "Starts the run"}</dd></div>
        <div><dt>File</dt><dd className="mono">{packet.file || "Unknown"}</dd></div>
        <div><dt>File written</dt><dd>{packet.time !== null ? dateTime(packet.time) : <span className="muted">Not available</span>}</dd></div>
        <div><dt>SHA-256</dt><dd className="mono" title={packet.sha256 || ""}>{packet.sha256 ? shortHash(packet.sha256) : <span className="muted">Not computed</span>}</dd></div>
        {d.acceptanceIds.length ? <div><dt>Criteria</dt><dd>{d.acceptanceIds.join(", ")}</dd></div> : null}
      </dl>
      {d.objective || d.summary ? (
        <Section title={d.summary ? "Summary" : "Objective"}>
          <p className="lead-text">{d.summary || d.objective}</p>
          {d.summary && d.objective ? <p className="muted">Objective: {d.objective}</p> : null}
          {d.nextAction ? <p className="muted">Next action: {d.nextAction}</p> : null}
        </Section>
      ) : null}
      {d.instructions.length ? (
        <Section title="Instructions">
          <ol className="numbered">{d.instructions.map((item, index) => <li key={index}>{item}</li>)}</ol>
        </Section>
      ) : null}
      {d.scope.length ? <Section title="Scope"><Lines items={d.scope} /></Section> : null}
      {d.changedFiles.length ? <Section title="Changed files"><Lines items={d.changedFiles.map(file => <span className="mono">{file}</span>)} /></Section> : null}
      {d.checks.length ? (
        <Section title="Checks">
          <ul className="check-list">{d.checks.map((check, index) => <li key={index} className={`check-${check.status}`}><span>{check.name}</span><span>{check.status}</span></li>)}</ul>
        </Section>
      ) : null}
      {d.commands.length ? (
        <Section title="Deterministic commands">
          {d.commands.map((command, index) => (
            <div key={index} className="command">
              <code>{command.command}</code>
              <span className="muted">exit {command.exitCode === null ? "unknown" : command.exitCode}{command.stdoutSha256 ? `, stdout ${shortHash(command.stdoutSha256)}` : ""}</span>
            </div>
          ))}
        </Section>
      ) : null}
      {d.rerun ? (
        <Section title="Independent rerun">
          <p><span className={`badge ${d.rerun.status === "MATCH" ? "badge-passed" : "badge-failed"}`}>{d.rerun.status || "Unknown"}</span></p>
          <div className="command"><code>{d.rerun.command}</code></div>
          <p className="muted mono">Reviewer {shortHash(d.rerun.stdoutSha256)}, Tester {shortHash(d.rerun.testerStdoutSha256)}</p>
        </Section>
      ) : null}
      {d.results.length ? (
        <Section title="Criteria results">
          <ul className="check-list">{d.results.map(result => <li key={result.id} className={`check-${result.status}`}><span>{result.id}</span><span>{result.status}, {result.evidence} refs</span></li>)}</ul>
        </Section>
      ) : null}
      {d.findings.length ? <Section title="Findings"><Lines items={d.findings} /></Section> : null}
      {d.errors.length ? <Section title="Errors"><Lines items={d.errors} /></Section> : null}
      {d.discrepancies.length ? <Section title="Discrepancies"><Lines items={d.discrepancies} /></Section> : null}
      {d.candidate ? (
        <Section title="Candidate">
          <p className="mono">{d.candidate.path}</p>
          <p className="muted mono">{shortHash(d.candidate.sha256)}</p>
        </Section>
      ) : null}
      {d.evidence.length ? (
        <Section title="Evidence references">
          <ul className="evidence-list">{d.evidence.map((ref, index) => <li key={index}><span className="mono">{ref.path || ref.id}</span><span className="muted">{ref.kind}</span></li>)}</ul>
        </Section>
      ) : null}
    </div>
  );
}
