import React, { useMemo, useState } from "react";
import Icon from "../components/Icon.jsx";
import Chamber from "../components/Chamber.jsx";
import ProgressPanel, { LifecycleRibbon } from "../components/Progress.jsx";
import ActivityFeed, { RecordHealth, RoleTag, OutcomeBadge } from "../components/Activity.jsx";
import Sequence from "../components/Sequence.jsx";
import { BarRows, HoldTimeline, TokenStack, holdIntervals } from "../components/Charts.jsx";
import { ROLE_NAMES, ROLE_ORDER } from "../data/council-model.js";
import { clock, duration, plural, sentence, shortHash, tokens } from "../lib/format.js";

function RunHeader({ model }) {
  const { run } = model;
  const [expanded, setExpanded] = useState(false);
  const name = run.project || run.taskId || "CouncilFlow run";
  const long = Boolean(run.objective && run.objective.length > 160);
  return (
    <header className="run-header">
      <div className="run-title">
        <h1>{name}</h1>
        {run.objective ? (
          <div className="run-objective">
            <p id="run-objective-text" className={long && !expanded ? "is-clamped" : undefined}>{run.objective}</p>
            {long ? (
              <button type="button" className="text-button" aria-expanded={expanded} aria-controls="run-objective-text" onClick={() => setExpanded(!expanded)}>
                {expanded ? "Show less" : "Show full task"}
              </button>
            ) : null}
          </div>
        ) : null}
        <p className="run-ids">
          {run.project && run.taskId ? <span>Task <b className="mono">{run.taskId}</b></span> : null}
          {run.planId ? <span>Plan <b className="mono">{run.planId}</b>{run.planRevision ? ` rev ${run.planRevision}` : ""}</span> : null}
          {run.currentAttempt ? <span>Current attempt <b className="mono">{run.currentAttempt}</b>{run.attemptCount > 1 ? `, ${run.attemptCount} recorded` : ""}</span> : null}
        </p>
      </div>
      {run.scope.length ? (
        <ul className="scope-list" aria-label="Plan scope">{run.scope.slice(0, 4).map(item => <li key={item}>{item}</li>)}</ul>
      ) : null}
    </header>
  );
}

export function OverviewView({ model, ui }) {
  return (
    <div className="view view-overview">
      <RunHeader model={model} />
      <div className="overview-grid">
        <section className="panel chamber-panel" aria-labelledby="council-title">
          <header className="panel-head">
            <div>
              <h2 id="council-title">The council</h2>
              <p className="panel-sub">Select a role to see its task, history and evidence</p>
            </div>
            <StateLegend />
          </header>
          <Chamber model={model} selectedRole={ui.selectedRole} onSelectRole={ui.openRole} reduced={ui.reduced} />
        </section>
        <div className="stack overview-side">
          <ProgressPanel model={model} freshIds={ui.freshIds} reduced={ui.reduced} now={ui.now} onOpenPacket={ui.openPacket} />
          <RecordHealth model={model} mode={ui.mode} />
        </div>
        <ActivityFeed model={model} freshIds={ui.freshIds} onOpenPacket={ui.openPacket} now={ui.now} limit={6} title="Recent activity" showFilter={false} />
      </div>
    </div>
  );
}

function StateLegend() {
  const items = [["working", "Active"], ["waiting", "Waiting"], ["completed", "Done"], ["failed", "Failed"], ["blocked", "Blocked"], ["idle", "Idle"]];
  return (
    <ul className="state-legend" aria-label="Role states">
      {items.map(([key, label]) => <li key={key}><span className={`legend-dot state-dot-${key}`} aria-hidden="true" />{label}</li>)}
    </ul>
  );
}

export function OrchestrationView({ model, ui }) {
  return (
    <div className="view">
      <RunHeader model={model} />
      <section className="panel" aria-labelledby="flow-title">
        <header className="panel-head">
          <div>
            <h2 id="flow-title">Handoff sequence</h2>
            <p className="panel-sub">Every validated packet, in reply order, grouped by attempt</p>
          </div>
        </header>
        <Sequence model={model} onOpenPacket={ui.openPacket} freshIds={ui.freshIds} />
      </section>
      <div className="split">
          <section className="panel" aria-labelledby="routes-title">
            <header className="panel-head">
              <div>
                <h2 id="routes-title">Routes</h2>
                <p className="panel-sub">The routes the CouncilFlow contract allows, with packets counted</p>
              </div>
            </header>
            <table className="table">
              <thead><tr><th scope="col">From</th><th scope="col">To</th><th scope="col">Carries</th><th scope="col" className="num-col">Packets</th></tr></thead>
              <tbody>
                {model.routes.map(route => (
                  <tr key={route.id} className={route.latest ? "is-latest" : ""}>
                    <td><RoleTag role={route.from} /></td>
                    <td><RoleTag role={route.to} /></td>
                    <td className="muted">{route.label}{route.recorded ? "" : " (not a packet)"}</td>
                    <td className="num-col num">{route.recorded ? route.count : "None"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="panel" aria-labelledby="stages-title">
            <header className="panel-head">
              <div>
                <h2 id="stages-title">Stages in this attempt</h2>
                <p className="panel-sub">Who is responsible for each step</p>
              </div>
            </header>
            <LifecycleRibbon lifecycle={model.lifecycle} freshIds={ui.freshIds} reduced={ui.reduced} size="small" />
            <ol className="stage-table">
              {model.lifecycle.steps.map(step => (
                <li key={step.key} className={`step-${step.status}`}>
                  <RoleTag role={step.role} />
                  <span>{step.label}</span>
                  <span className="muted">{sentence(step.status)}</span>
                </li>
              ))}
            </ol>
          </section>
      </div>
    </div>
  );
}

export function AgentsView({ model, ui }) {
  return (
    <div className="view">
      <header className="view-head">
        <h1>Roles</h1>
        <p>Each CouncilFlow role is a responsibility carried out by the host's own agents. States come from the packets in this run.</p>
      </header>
      <ul className="agent-grid">
        {model.roles.map(role => (
          <li key={role.role}>
            <button type="button" className={`agent-card role-scope-${role.role} state-${role.state.key}`} onClick={() => ui.openRole(role.role)}>
              <span className="agent-top">
                <span className={`agent-glyph role-tint-${role.role}`}><Icon name={role.role} size={26} /></span>
                <span className={`state-pill state-${role.state.key}`}>{role.state.label}</span>
              </span>
              <span className="agent-name">{role.name}</span>
              <span className="agent-duty">{role.duty}</span>
              <span className="agent-stats">
                <span><b className="num">{role.sentCount}</b> sent</span>
                <span><b className="num">{role.receivedCount}</b> received</span>
                <span><b className="num">{role.instances.length}</b> {role.instances.length === 1 ? "instance" : "instances"}</span>
              </span>
              <span className="agent-model">Model: {role.model.value || "not recorded"}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ExecutionsView({ model, ui }) {
  const [typeFilter, setTypeFilter] = useState("all");
  const types = useMemo(() => [...new Set(model.packets.map(packet => packet.type))], [model.packets]);
  const packets = model.packets.filter(packet => typeFilter === "all" || packet.type === typeFilter);
  return (
    <div className="view">
      <RunHeader model={model} />
      <section className="panel" aria-labelledby="attempts-title">
        <header className="panel-head">
          <div>
            <h2 id="attempts-title">Attempts</h2>
            <p className="panel-sub">A new attempt starts when the Manager sends work back for rework</p>
          </div>
        </header>
        {model.attempts.length ? (
          <ol className="attempts">
            {model.attempts.map(attempt => (
              <li key={attempt.id} className={`attempt outcome-${attempt.outcome}${attempt.current ? " is-current" : ""}`}>
                <div className="attempt-head">
                  <span className="mono attempt-id">{attempt.id}</span>
                  <OutcomeBadge outcome={attempt.outcome} />
                  {attempt.current ? <span className="badge badge-neutral">Current</span> : null}
                </div>
                <p className="attempt-decision">{attempt.decision ? `Manager decision: ${attempt.decision}` : attempt.current ? "No decision yet" : "No decision recorded"}</p>
                <ul className="attempt-reports">
                  {attempt.reports.map(report => (
                    <li key={report.id}><RoleTag role={report.role} /> <span className={`badge badge-${report.status === "in_progress" ? "active" : report.status}`}>{sentence(report.status)}</span></li>
                  ))}
                  {!attempt.reports.length ? <li className="muted">No reports yet</li> : null}
                </ul>
                <p className="muted num">{plural(attempt.packets.length, "packet")}{attempt.start !== null && attempt.end !== null ? `, ${duration(attempt.end - attempt.start)} between first and last file` : ""}</p>
              </li>
            ))}
          </ol>
        ) : <p className="muted">No attempts recorded yet.</p>}
      </section>

      <div className="split">
        <section className="panel" aria-labelledby="criteria-title">
          <header className="panel-head">
            <div>
              <h2 id="criteria-title">Acceptance criteria</h2>
              <p className="panel-sub">{model.acceptance.verified ? "Results from the Planner's final check" : "Not checked until the Planner's final check is recorded"}</p>
            </div>
          </header>
          {model.acceptance.criteria.length ? (
            <ul className="criteria">
              {model.acceptance.criteria.map(item => (
                <li key={item.id} className={`criterion crit-${item.status}`}>
                  <span className="crit-mark" aria-hidden="true"><Icon name={item.status === "passed" ? "check" : item.status === "failed" ? "cross" : item.status === "blocked" ? "alert" : "clock"} size={14} /></span>
                  <span className="crit-body"><b>{item.id}</b><span>{item.text}</span></span>
                  <span className="crit-status">{item.status === "unchecked" ? "Not checked" : `${sentence(item.status)}, ${plural(item.evidenceCount, "ref")}`}</span>
                </li>
              ))}
            </ul>
          ) : <p className="muted">The original acceptance criteria are not available from this run folder.</p>}
        </section>
        <section className="panel" aria-labelledby="tasks-title">
          <header className="panel-head">
            <div>
              <h2 id="tasks-title">Plan tasks</h2>
              <p className="panel-sub">The Planner's work breakdown</p>
            </div>
          </header>
          {model.plan && model.plan.tasks.length ? (
            <ul className="tasks">
              {model.plan.tasks.map(task => (
                <li key={task.id}>
                  <span className="mono task-id">{task.id}</span>
                  <span className="task-body">
                    <span>{task.title || "Task"}</span>
                    <span className="muted">{plural(task.instructionCount, "instruction")}{task.acceptanceIds.length ? `, covers ${task.acceptanceIds.join(", ")}` : ""}{task.dependsOn.length ? `, after ${task.dependsOn.join(", ")}` : ""}</span>
                  </span>
                </li>
              ))}
            </ul>
          ) : <p className="muted">{model.plan ? "The linked plan lists no tasks." : "The linked plan file was not available."}</p>}
        </section>
      </div>

      <section className="panel" aria-labelledby="packets-title">
        <header className="panel-head">
          <div>
            <h2 id="packets-title">Packets</h2>
            <p className="panel-sub">{plural(model.packets.length, "validated packet")}</p>
          </div>
          <label className="select">
            <span className="visually-hidden">Filter packets by type</span>
            <select value={typeFilter} onChange={event => setTypeFilter(event.target.value)}>
              <option value="all">All types</option>
              {types.map(type => <option key={type} value={type}>{type}</option>)}
            </select>
          </label>
        </header>
        <div className="table-scroll">
          <table className="table packet-table">
            <thead><tr><th scope="col">Packet</th><th scope="col">From</th><th scope="col">To</th><th scope="col">Type</th><th scope="col">Result</th><th scope="col">Attempt</th><th scope="col">File time</th></tr></thead>
            <tbody>
              {packets.map(packet => (
                <tr key={packet.id} className={ui.freshIds.has(packet.id) ? "is-fresh" : ""}>
                  <td><button type="button" className="link-button mono" onClick={() => ui.openPacket(packet.id)}>{packet.id}</button></td>
                  <td><RoleTag role={packet.from} instance={packet.fromInstance} /></td>
                  <td><RoleTag role={packet.to} instance={packet.toInstance} /></td>
                  <td className="mono">{packet.type}</td>
                  <td><OutcomeBadge outcome={packet.outcome} /></td>
                  <td className="mono">{packet.attempt}</td>
                  <td className="num">{packet.time !== null ? clock(packet.time) : "None"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Unavailable({ title, children }) {
  return (
    <div className="unavailable">
      <Icon name="layers" size={22} />
      <div><p className="unavailable-title">{title}</p><p className="muted">{children}</p></div>
    </div>
  );
}

export function AnalyticsView({ model }) {
  const holds = useMemo(() => holdIntervals(model), [model]);
  const holdByRole = ROLE_ORDER.map(role => {
    const total = holds.filter(item => item.role === role).reduce((sum, item) => sum + (item.end - item.start), 0);
    return { key: role, label: ROLE_NAMES[role], value: total, display: total ? duration(total) : "None", tone: `role-bg-${role}`, note: `${ROLE_NAMES[role]} held the work for ${duration(total)} in total.` };
  });
  const sentRows = model.roles.map(role => ({ key: role.role, label: role.name, value: role.sentCount, tone: `role-bg-${role.role}`, note: `${role.name} sent ${plural(role.sentCount, "packet")} and received ${role.receivedCount}.` }));
  const outcomeRows = ["worker", "tester", "reviewer"].flatMap(role => ["passed", "failed", "blocked", "in_progress"].map(status => ({
    key: `${role}:${status}`, label: `${ROLE_NAMES[role]} ${sentence(status).toLowerCase()}`,
    value: model.analytics.reportOutcomes[`${role}:${status}`] || 0, tone: `outcome-bg-${status}`
  }))).filter(row => row.value);
  const eff = model.efficiency;

  return (
    <div className="view">
      <header className="view-head">
        <h1>Analytics</h1>
        <p>Measures computed from this run's packets, their file times, and Agent Efficiency records when supplied. Missing data stays missing.</p>
      </header>
      <div className="kpis">
        <div className="kpi"><span className="kpi-value num">{model.packets.length}</span><span className="kpi-label">validated packets</span></div>
        <div className="kpi"><span className="kpi-value num">{model.run.attemptCount}</span><span className="kpi-label">{model.run.attemptCount === 1 ? "attempt" : "attempts"}, {model.analytics.rework} sent back</span></div>
        <div className="kpi"><span className="kpi-value num">{model.timing.span !== null ? duration(model.timing.span) : "Unknown"}</span><span className="kpi-label">first to last packet file</span></div>
        <div className="kpi"><span className="kpi-value num">{model.acceptance.verified ? `${model.acceptance.passed}/${model.acceptance.total}` : "Not yet"}</span><span className="kpi-label">criteria verified</span></div>
      </div>
      <div className="split">
        <section className="panel" aria-labelledby="hold-title">
          <header className="panel-head"><div><h2 id="hold-title">Who held the work, and for how long</h2><p className="panel-sub">From packet file write times, not authenticated event times</p></div></header>
          <HoldTimeline model={model} />
          <BarRows rows={holdByRole} label="Total time each role held the work" emptyText="" />
        </section>
        <section className="panel" aria-labelledby="traffic-title">
          <header className="panel-head"><div><h2 id="traffic-title">Packets sent by role</h2><p className="panel-sub">The Manager should carry most of the traffic: it coordinates every handoff</p></div></header>
          <BarRows rows={sentRows} label="Packets sent by each role" emptyText="No packets yet." />
          <h3 className="sub-head">Report outcomes</h3>
          <BarRows rows={outcomeRows} label="Report outcomes by role" emptyText="No Worker, Tester or Reviewer reports yet." />
        </section>
      </div>
      <section className="panel" aria-labelledby="usage-title">
        <header className="panel-head"><div><h2 id="usage-title">Token usage and models</h2><p className="panel-sub">{eff.available ? `From ${plural(eff.records.length, "Agent Efficiency record")}${eff.source ? ` in ${eff.source}` : ""}` : "Optional Agent Efficiency records"}</p></div></header>
        {eff.available ? (
          <div className="split is-tight">
            <div>
              <TokenStack totals={eff.totals} />
              {eff.totals.cost.value !== null ? <p className="muted">Reported cost: {eff.totals.cost.value.toFixed(4)} across {plural(eff.totals.cost.reported, "record")}.</p> : <p className="muted">No record reported a cost.</p>}
            </div>
            <div>
              <h3 className="sub-head">By model</h3>
              <BarRows rows={eff.byModel.map(item => ({ key: item.model, label: item.model, value: item.input + item.output, display: item.known ? tokens(item.input + item.output) : "Not reported", tone: "tone-a", note: `${item.model}: ${plural(item.records, "record")}, ${tokens(item.input)} input and ${tokens(item.output)} output tokens.` }))} label="Tokens by model" emptyText="Records did not report token counts." />
            </div>
            <div className="table-scroll span-all">
              <table className="table">
                <thead><tr><th scope="col">Attempt</th><th scope="col">Harness</th><th scope="col">Model</th><th scope="col" className="num-col">Input</th><th scope="col" className="num-col">Output</th><th scope="col" className="num-col">Elapsed</th><th scope="col">Acceptance</th></tr></thead>
                <tbody>
                  {eff.records.map((record, index) => (
                    <tr key={index}>
                      <td className="num">{record.attempt}</td><td>{record.harness}</td><td className="mono">{record.model || "Not reported"}</td>
                      <td className="num-col num" title={record.input === null ? record.availability.input : undefined}>{tokens(record.input)}</td>
                      <td className="num-col num" title={record.output === null ? record.availability.output : undefined}>{tokens(record.output)}</td>
                      <td className="num-col num">{record.elapsedMs !== null ? duration(record.elapsedMs) : "Not reported"}</td>
                      <td>{record.acceptance}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <Unavailable title="Token and model data are not available for this run">
            {eff.reason} Packets do not carry token counts or model names. To show them, record usage with <code>scripts/efficiency.py</code> using this task ID as the run ID, then publish with <code>--efficiency-records</code>.
          </Unavailable>
        )}
      </section>
    </div>
  );
}

export function ProjectListView({ model, ui }) {
  const run = model ? model.run : null;
  const source = ui.mode === "embedded" ? "Published by the Manager" : ui.mode === "folder" ? "Opened from a folder" : ui.mode === "files" ? "Opened from files" : null;
  return (
    <div className="view">
      <header className="view-head">
        <h1>Project list</h1>
        <p>The board opens on the current run by itself. Switching to another run is a separate, deliberate step: nothing here loads until you pick a run.</p>
      </header>
      <div className="split">
        <section className="panel" aria-labelledby="current-run-title">
          <header className="panel-head"><div><h2 id="current-run-title">Current run</h2><p className="panel-sub">{source || "No run is open"}</p></div></header>
          {run && run.hasPackets ? (
            <>
              <dl className="facts">
                {run.project ? <div><dt>Project</dt><dd>{run.project}</dd></div> : null}
                <div><dt>Task</dt><dd className="mono">{run.taskId || "Unknown"}</dd></div>
                {run.planId ? <div><dt>Plan</dt><dd className="mono">{run.planId}{run.planRevision ? ` rev ${run.planRevision}` : ""}</dd></div> : null}
                <div><dt>Status</dt><dd>{run.disposition}</dd></div>
              </dl>
              <div className="empty-actions"><button type="button" className="button button-quiet" onClick={ui.goOverview}><Icon name="overview" size={16} /><span>Back to the council</span></button></div>
            </>
          ) : <p className="muted">Boards published by the Manager open on their run automatically. This one has no run records yet.</p>}
        </section>
        <section className="panel" aria-labelledby="other-run-title">
          <header className="panel-head"><div><h2 id="other-run-title">Open another run</h2><p className="panel-sub">Reads the run you choose from this computer</p></div></header>
          <p>Pick a run folder, usually <code>.councilflow/runs/&lt;task-id&gt;</code>, or select its JSON packets. The current view is replaced by the run you pick.</p>
          <div className="empty-actions">
            <button type="button" className="button button-primary" onClick={ui.onOpenFolder}><Icon name="folder" size={16} /><span>Open run folder</span></button>
            <button type="button" className="button button-quiet" onClick={ui.onChooseFiles}><Icon name="files" size={16} /><span>Choose message files</span></button>
          </div>
          <p className="muted">In Chromium browsers an opened folder is watched for new packets. Elsewhere, file choices load as a snapshot.</p>
        </section>
      </div>
    </div>
  );
}

export function SettingsView({ model, ui, prefs, setPrefs }) {
  const policy = model.policy;
  return (
    <div className="view">
      <header className="view-head">
        <h1>Settings</h1>
        <p>Dashboard preferences are saved in this browser. CouncilFlow's workflow configuration is shown read-only: the board never changes it.</p>
      </header>
      <div className="split">
        <section className="panel" aria-labelledby="prefs-title">
          <header className="panel-head"><div><h2 id="prefs-title">Dashboard preferences</h2></div></header>
          <fieldset className="field">
            <legend>Motion</legend>
            {[["system", "Follow system setting"], ["reduce", "Reduce motion"], ["full", "Full motion"]].map(([value, label]) => (
              <label key={value} className="radio"><input type="radio" name="motion" value={value} checked={prefs.motion === value} onChange={() => setPrefs({ ...prefs, motion: value })} /> {label}</label>
            ))}
          </fieldset>
          <fieldset className="field">
            <legend>Live follow</legend>
            <label className="toggle">
              <input type="checkbox" checked={ui.follow} onChange={event => ui.setFollow(event.target.checked)} disabled={ui.mode !== "embedded"} />
              <span>Reload this published board every 3 seconds while the run is in progress</span>
            </label>
            <p className="muted">{ui.mode === "embedded" ? "Stops by itself once the final check is recorded. Your view and scroll position are kept." : "Live follow applies to boards published by the Manager. An opened folder is watched directly instead."}</p>
          </fieldset>
        </section>
        <section className="panel" aria-labelledby="routing-title">
          <header className="panel-head"><div><h2 id="routing-title">Model routing</h2></div></header>
          <p>CouncilFlow does not pick models. Each role runs on the host's own models, tools and permissions.</p>
          <ul className="plain-list">
            <li>Routing hints from <code>scripts/route.py</code> are advice. The Manager records whether it accepted, ignored or overrode them.</li>
            <li>Role preferences resolve to <b>inherit host</b>. The effective model stays unknown until a host reports it.</li>
            <li>Agent Efficiency records can report the upstream model per run. {model.efficiency.available ? `This board has ${plural(model.efficiency.records.length, "record")}.` : "None were supplied for this board."}</li>
          </ul>
        </section>
      </div>
      <section className="panel" aria-labelledby="policy-title">
        <header className="panel-head"><div><h2 id="policy-title">Workflow policy</h2><p className="panel-sub">{policy ? `From ${policy.source}` : "Not embedded in this board"}</p></div></header>
        {policy ? (
          <>
            <ol className="policy-order" aria-label="Workflow order">
              {policy.order.map((role, index) => <li key={`${role}-${index}`}><RoleTag role={role} /></li>)}
            </ol>
            <div className="policy-grid">
              {Object.entries(policy.roles).map(([role, value]) => (
                <div key={role} className="policy-role">
                  <RoleTag role={role} />
                  <ul className="plain-list">{(value.responsibilities || []).map(item => <li key={item}>{item}</li>)}</ul>
                  <p className="muted">{value.application_code ? "Changes application code" : "No application code"}{value.abilities && value.abilities.length ? `; abilities: ${value.abilities.join(", ")}` : ""}</p>
                </div>
              ))}
            </div>
            {policy.resources && Object.keys(policy.resources).length ? (
              <dl className="facts is-inline">
                {Object.entries(policy.resources).map(([key, value]) => <div key={key}><dt>{sentence(key)}</dt><dd>{sentence(String(value))}</dd></div>)}
              </dl>
            ) : null}
          </>
        ) : <p className="muted">Boards opened from a folder or files do not include the policy. Boards published by the Manager do.</p>}
      </section>
      <section className="panel" aria-labelledby="sources-title">
        <header className="panel-head"><div><h2 id="sources-title">Data sources</h2><p className="panel-sub">{ui.mode === "embedded" ? "Embedded by scripts/dashboard.py" : ui.mode === "folder" ? "Read from the selected folder" : "Read from the selected files"}</p></div></header>
        <div className="table-scroll">
          <table className="table">
            <thead><tr><th scope="col">File</th><th scope="col">SHA-256</th><th scope="col">Written</th><th scope="col">Status</th></tr></thead>
            <tbody>
              {model.files.map(file => (
                <tr key={file.path}>
                  <td className="mono">{file.path}</td>
                  <td className="mono" title={file.sha256 || ""}>{file.sha256 ? shortHash(file.sha256) : "None"}</td>
                  <td className="num">{file.modified ? clock(Date.parse(file.modified)) : "Unknown"}</td>
                  <td>{file.error ? <span className="badge badge-failed" title={file.error}>Problem</span> : <span className="badge badge-neutral">Read</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
