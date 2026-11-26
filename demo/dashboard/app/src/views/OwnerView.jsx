import React from "react";
import Icon from "../components/Icon.jsx";
import { plural, shortHash } from "../lib/format.js";

// The board reads only the generated owner-view.json that the publisher embedded.
// It never opens the ledger, never records a decision and offers no control that does.

function list(value) {
  return Array.isArray(value) ? value : [];
}

function Panel({ id, title, sub, children }) {
  return (
    <section className="panel" aria-labelledby={id}>
      <header className="panel-head"><div><h2 id={id}>{title}</h2>{sub ? <p className="panel-sub">{sub}</p> : null}</div></header>
      {children}
    </section>
  );
}

function Verbatim({ children }) {
  return <p className="verbatim">{children}</p>;
}

function Ids({ values }) {
  const items = list(values);
  return items.length ? <span className="mono">{items.join(", ")}</span> : <span className="muted">None</span>;
}

function EntryTable({ entries, empty }) {
  const rows = list(entries);
  if (!rows.length) return <p className="muted">{empty}</p>;
  return (
    <div className="table-scroll">
      <table className="table">
        <thead><tr><th scope="col">ID</th><th scope="col">Statement</th><th scope="col">Introduced</th><th scope="col">Sources</th></tr></thead>
        <tbody>
          {rows.map(entry => (
            <tr key={entry.id}>
              <td className="mono">{entry.id}</td>
              <td><span className="verbatim">{entry.content}</span></td>
              <td className="num">v{entry.version_introduced}</td>
              <td><Ids values={entry.source_ids} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Questions({ questions }) {
  const rows = list(questions);
  if (!rows.length) return <p className="muted">No open questions in this ledger version.</p>;
  return (
    <ul className="plain-list questions">
      {rows.map(question => (
        <li key={question.id} className="question">
          <p className="mono">{question.id}</p>
          <Verbatim>{question.wording}</Verbatim>
          <dl className="facts is-inline">
            <div><dt>Default</dt><dd>{question.default_stored ? (question.default === null ? "No default is permitted" : <span className="verbatim">{question.default}</span>) : "No default is stored"}</dd></div>
            <div><dt>Blocking</dt><dd>{question.blocking === null ? "Not stored" : question.blocking ? "Yes" : "No"}</dd></div>
            <div><dt>Reversibility</dt><dd>{question.reversibility || "Not stored"}</dd></div>
            <div><dt>Affected slices</dt><dd><Ids values={question.affected_slices} /></dd></div>
            {question.reason ? <div><dt>Reason for asking</dt><dd><span className="verbatim">{question.reason}</span></dd></div> : null}
          </dl>
          {question.packet_wording_matches === false ? <p className="muted">The stored question packet words this differently from the ledger entry shown here.</p> : null}
        </li>
      ))}
    </ul>
  );
}

export function OwnerView({ ui }) {
  const owner = ui.ownerView;
  if (!owner || !owner.view) {
    return (
      <div className="view">
        <header className="view-head">
          <h1>Owner view</h1>
          <p>A read-only summary of the project ledger, generated for the Owner.</p>
        </header>
        <section className="panel">
          <div className="unavailable">
            <Icon name="layers" size={22} />
            <div>
              <p className="unavailable-title">{owner && owner.error ? "The Owner view could not be read" : "No Owner view was published with this board"}</p>
              <p className="muted">{owner && owner.error ? owner.error : "Generate one with scripts/owner_view.py generate, then republish this board."}</p>
            </div>
          </div>
        </section>
      </div>
    );
  }
  const view = owner.view;
  const fresh = owner.freshness || { stale: false };
  const budget = view.default_budget;
  return (
    <div className="view">
      <header className="view-head">
        <h1>Owner view</h1>
        <p>Generated from the project ledger. It is read-only and is not the source of truth. Answer pending questions through the Manager.</p>
      </header>
      <section className={`panel stale-panel${fresh.stale ? " is-stale" : ""}`} aria-labelledby="ledger-version-title">
        <header className="panel-head"><div><h2 id="ledger-version-title">Ledger version {view.ledger_version}</h2>
          <p className="panel-sub">Generated {view.generated_at}; ledger file {shortHash(view.ledger_sha256)}</p></div>
          <span className={`badge ${fresh.stale ? "badge-blocked" : "badge-passed"}`}>{fresh.stale ? "Stale" : "Current"}</span>
        </header>
        <p role={fresh.stale ? "alert" : undefined}>{fresh.stale ? `Out of date: ${fresh.reason || "a newer ledger version exists"}. Regenerate the view before relying on it.` : `This view matches ledger version ${view.ledger_version} as of the last board publish.`}</p>
      </section>
      <Panel id="goal-title" title="Current project goal">
        {view.goal ? <><Verbatim>{view.goal.content}</Verbatim><p className="muted"><span className="mono">{view.goal.id}</span>, introduced in v{view.goal.version_introduced}</p></> : <p className="muted">No goal is recorded in the ledger.</p>}
      </Panel>
      <Panel id="requirements-title" title="Confirmed requirements" sub={plural(list(view.confirmed_requirements).length, "requirement")}>
        <EntryTable entries={view.confirmed_requirements} empty="No confirmed requirements." />
      </Panel>
      <Panel id="assumptions-title" title="Provisional assumptions" sub="Unconfirmed defaults; an unanswered question is not approval">
        <EntryTable entries={view.provisional_assumptions} empty="No provisional assumptions." />
      </Panel>
      <Panel id="questions-title" title="Open questions" sub="Exact stored wording">
        <Questions questions={view.open_questions} />
      </Panel>
      <Panel id="decisions-title" title="Decision history" sub={plural(list(view.decision_history).length, "decision")}>
        <EntryTable entries={view.decision_history} empty="No decisions recorded." />
      </Panel>
      <Panel id="budget-title" title="Unconfirmed default budget">
        <dl className="facts is-inline">
          <div><dt>Used</dt><dd>{budget.used} of {budget.limit}</dd></div>
          <div><dt>Remaining</dt><dd>{budget.remaining}</dd></div>
          <div><dt>Status</dt><dd>{budget.exceeded ? "Exceeded" : "Within budget"}</dd></div>
        </dl>
      </Panel>
      <Panel id="slices-title" title="Slice readiness and execution status" sub={plural(list(view.slices).length, "slice")}>
        {list(view.slices).length ? (
          <div className="table-scroll">
            <table className="table">
              <thead><tr><th scope="col">Slice</th><th scope="col">Readiness</th><th scope="col">Status</th><th scope="col">Pinned ledger</th><th scope="col">Ledger IDs</th></tr></thead>
              <tbody>
                {view.slices.map(item => (
                  <tr key={item.slice_id}>
                    <td className="mono">{item.slice_id}</td>
                    <td>{item.readiness || "Not assessed"}</td>
                    <td>{item.status}</td>
                    <td className="num">v{item.ledger_version}{item.pinned_to_older_ledger ? " (older)" : ""}</td>
                    <td><Ids values={item.ledger_ids} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="muted">The Manager has not recorded a plan yet.</p>}
      </Panel>
      <Panel id="qa-title" title="QA results" sub="Tester retests recorded in project state">
        {list(view.qa_results).length ? (
          <div className="table-scroll">
            <table className="table">
              <thead><tr><th scope="col">Retest</th><th scope="col">Slice</th><th scope="col">Result</th><th scope="col">Ledger</th><th scope="col">Freshness</th></tr></thead>
              <tbody>
                {view.qa_results.map(item => (
                  <tr key={item.retest_id}>
                    <td className="mono">{item.retest_id}</td>
                    <td className="mono">{item.slice_id}</td>
                    <td><span className={`badge ${item.result === "pass" ? "badge-passed" : "badge-failed"}`}>{item.result}</span></td>
                    <td className="num">v{item.ledger_version}</td>
                    <td>{item.stale ? "Stale: ledger has moved on" : "Current"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="muted">No retests recorded.</p>}
      </Panel>
      <Panel id="audit-title" title="Audit findings" sub="Advisory; the audit never changes delivery state">
        {list(view.audit_findings).length ? (
          <ul className="plain-list">
            {view.audit_findings.map(item => (
              <li key={`${item.audit_id}-${item.ledger_id}`}>
                <p><span className="mono">{item.audit_id}</span> on <span className="mono">{item.ledger_id}</span>: <b>{item.verdict}</b>, {item.kind}{item.owner_decision_needed ? ", needs an Owner decision" : ""}{item.stale ? " (stale)" : ""}</p>
                <Verbatim>{item.finding}</Verbatim>
              </li>
            ))}
          </ul>
        ) : <p className="muted">No audit recorded.</p>}
      </Panel>
    </div>
  );
}
