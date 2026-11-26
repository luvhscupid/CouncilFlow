import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Icon from "./components/Icon.jsx";
import Chamber from "./components/Chamber.jsx";
import { Drawer, AgentDetail, PacketDetail } from "./components/Drawer.jsx";
import { OwnerView } from "./views/OwnerView.jsx";
import { OverviewView, OrchestrationView, AgentsView, ExecutionsView, AnalyticsView, ProjectListView, SettingsView } from "./views/Views.jsx";
import { useRunSource } from "./state/useRunSource.js";
import { useNow, useSystemReducedMotion } from "./lib/hooks.js";
import { read, write } from "./lib/storage.js";
import { buildModel } from "./data/council-model.js";

const VIEWS = [
  { id: "overview", label: "Overview", icon: "overview" },
  { id: "orchestration", label: "Orchestration", icon: "orchestration" },
  { id: "agents", label: "Roles", icon: "agents" },
  { id: "executions", label: "Executions", icon: "executions" },
  { id: "analytics", label: "Analytics", icon: "analytics" },
  { id: "owner", label: "Owner view", icon: "overview" },
  { id: "projects", label: "Project list", icon: "layers" },
  { id: "settings", label: "Settings", icon: "settings" }
];

function readHash() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const view = VIEWS.some(item => item.id === params.get("view")) ? params.get("view") : "overview";
  return { view, role: params.get("role"), packet: params.get("packet") };
}

function writeHash(state) {
  const params = new URLSearchParams();
  if (state.view !== "overview") params.set("view", state.view);
  if (state.role) params.set("role", state.role);
  if (state.packet) params.set("packet", state.packet);
  const next = params.toString();
  const url = `${window.location.pathname}${window.location.search}${next ? `#${next}` : ""}`;
  try { window.history.replaceState(null, "", url); } catch { /* file:// can refuse history updates */ }
}

function useFreshIds(model) {
  const seenRef = useRef(null);
  const [fresh, setFresh] = useState(() => new Set());
  useEffect(() => {
    if (!model || !model.packets.length) return undefined;
    const key = `councilflow.seen.${model.run.taskId || "run"}`;
    if (seenRef.current === null) seenRef.current = read(key, null, "session");
    const seen = seenRef.current;
    const ids = model.packets.map(packet => packet.id);
    const next = seen ? new Set(ids.filter(id => !seen.includes(id))) : new Set();
    setFresh(next);
    seenRef.current = ids;
    write(key, ids, "session");
    if (!next.size) return undefined;
    const timer = window.setTimeout(() => setFresh(new Set()), 4200);
    return () => window.clearTimeout(timer);
  }, [model]);
  return fresh;
}

function CommandBar({ source }) {
  const { connection, mode, follow, followActive, finished, setFollow, watching, toggleWatch, refresh } = source;
  return (
    <header className="command-bar">
      <a className="wordmark" href="#main" aria-label="CouncilFlow dashboard, skip to content"><span>CouncilFlow</span></a>
      <div className={`connection tone-${connection.tone}${followActive || watching ? " is-live" : ""}`} role="status">
        <span className="connection-dot" aria-hidden="true" />
        <span className="connection-label">{connection.label}</span>
      </div>
      <div className="command-actions">
        {mode === "embedded" ? (
          <button type="button" className={`button button-quiet${followActive ? " is-on" : ""}`} aria-pressed={follow && !finished} onClick={() => setFollow(!follow)} disabled={finished}
            title={finished ? "The run has its final check. Nothing more to follow." : "Reload this published board every 3 seconds"}>
            <Icon name={followActive ? "pause" : "play"} size={16} />
            <span>{finished ? "Run finished" : followActive ? "Following live" : "Follow live"}</span>
          </button>
        ) : null}
        {mode === "folder" ? (
          <button type="button" className="button button-quiet" onClick={toggleWatch}>
            <Icon name={watching ? "pause" : "play"} size={16} /><span>{watching ? "Pause watching" : "Resume watching"}</span>
          </button>
        ) : null}
        {mode === "embedded" || mode === "folder" ? (
          <button type="button" className="button button-quiet" onClick={refresh}><Icon name="refresh" size={16} /><span>Refresh</span></button>
        ) : null}
      </div>
    </header>
  );
}

function EmptyState({ onOpenProjects, reduced, idleModel }) {
  return (
    <section className="empty" aria-labelledby="empty-title">
      <div className="empty-copy">
        <h1 id="empty-title">No run is published here yet</h1>
        <p>The Manager publishes the current run into <code>.councilflow/runs/&lt;task-id&gt;/dashboard.html</code>, and that board opens on it directly. To look at a different run, pick it from the project list.</p>
        <div className="empty-actions">
          <button type="button" className="button button-primary" onClick={onOpenProjects}><Icon name="layers" size={16} /><span>Open project list</span></button>
        </div>
      </div>
      <div className="empty-art" aria-hidden="true">
        <Chamber model={idleModel} onSelectRole={() => {}} reduced={reduced} compact />
      </div>
    </section>
  );
}

export default function App() {
  const source = useRunSource();
  const { model } = source;
  const [route, setRoute] = useState(readHash);
  const [prefs, setPrefsState] = useState(() => ({ motion: "system", ...read("councilflow.prefs", {}) }));
  const systemReduced = useSystemReducedMotion();
  const reduced = prefs.motion === "reduce" || (prefs.motion === "system" && systemReduced);
  const freshIds = useFreshIds(model);
  const now = useNow(1000, Boolean(model && model.run.hasPackets));
  const folderInput = useRef(null);
  const fileInput = useRef(null);
  const mainRef = useRef(null);

  const idleModel = useMemo(() => buildModel({ files: [] }, {
    buildSnapshot: () => ({ valid: false, issues: [], taskId: null, planId: null, criteria: [], progress: { passed: 0, total: 0, recorded: false }, disposition: "Waiting for a run" }),
    validateMessage: () => false, orderMessages: () => []
  }), []);

  useEffect(() => { writeHash(route); }, [route]);
  useEffect(() => {
    const onHash = () => setRoute(readHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.motion = reduced ? "reduced" : "full";
  }, [reduced]);

  const setPrefs = useCallback(next => { setPrefsState(next); write("councilflow.prefs", next); }, []);
  const go = useCallback(view => {
    setRoute(current => ({ ...current, view }));
    if (mainRef.current) mainRef.current.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  }, [reduced]);
  const openRole = useCallback(role => setRoute(current => ({ ...current, role, packet: null })), []);
  const openPacket = useCallback(packet => setRoute(current => ({ ...current, packet, role: null })), []);
  const closeDrawer = useCallback(() => setRoute(current => ({ ...current, role: null, packet: null })), []);

  const onOpenFolder = useCallback(() => source.openFolder(folderInput.current), [source]);
  const onChooseFiles = useCallback(() => { if (fileInput.current) fileInput.current.click(); }, []);

  const selectedRole = model && route.role ? model.roles.find(role => role.role === route.role) : null;
  const selectedPacket = model && route.packet ? model.packets.find(packet => packet.id === route.packet) : null;
  const ui = {
    reduced, freshIds, now, mode: source.mode, follow: source.follow, setFollow: source.setFollow,
    connection: source.connection, onOpenFolder, onChooseFiles, goOverview: () => go("overview"),
    selectedRole: route.role, openRole, openPacket, ownerView: source.ownerView
  };
  const View = { overview: OverviewView, orchestration: OrchestrationView, agents: AgentsView, executions: ExecutionsView, analytics: AnalyticsView, projects: ProjectListView, owner: OwnerView, settings: SettingsView }[route.view];
  const accent = selectedRole ? selectedRole.role : selectedPacket ? selectedPacket.from : null;

  return (
    <div className={`app${reduced ? " is-reduced" : ""}`}>
      <div className="ambient" aria-hidden="true"><span className="aurora a1" /><span className="aurora a2" /><span className="grain" /></div>
      <nav className="rail" aria-label="Dashboard sections">
        <span className="rail-mark" aria-hidden="true"><Icon name="manager" size={22} /></span>
        <ul>
          {VIEWS.map(view => (
            <li key={view.id}>
              <button type="button" className="rail-item" aria-current={route.view === view.id ? "page" : undefined} onClick={() => go(view.id)} disabled={!model && view.id !== "overview" && view.id !== "projects" && view.id !== "owner"}>
                <Icon name={view.icon} size={20} />
                <span>{view.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="frame">
        <CommandBar source={source} />
        <input ref={folderInput} className="visually-hidden" type="file" multiple webkitdirectory="" tabIndex={-1} aria-label="Choose a CouncilFlow run folder"
          onChange={event => source.importFiles(event.target.files, true)} />
        <input ref={fileInput} className="visually-hidden" type="file" multiple accept=".json,application/json" tabIndex={-1} aria-label="Choose CouncilFlow JSON messages"
          onChange={event => source.importFiles(event.target.files, false)} />
        <p className="loading" role="status" aria-live="polite" hidden={!source.loading}>{source.loading ? <><span className="loading-bar" aria-hidden="true" />{source.loading}</> : null}</p>
        <main id="main" ref={mainRef} tabIndex={-1} className="main">
          {model || route.view === "projects" || route.view === "owner" ? (
            <div key={route.view} className="view-enter">
              <View model={model} ui={ui} prefs={prefs} setPrefs={setPrefs} />
            </div>
          ) : (
            <EmptyState onOpenProjects={() => go("projects")} reduced={reduced} idleModel={idleModel} />
          )}
        </main>
        <footer className="footnote">
          <span>Read-only view of CouncilFlow run records.</span>
          <span>It does not dispatch agents, approve work or change packets.</span>
        </footer>
      </div>
      <Drawer open={Boolean(selectedRole || selectedPacket)} onClose={closeDrawer} labelledBy="drawer-title" accent={accent}>
        {selectedRole ? <AgentDetail role={selectedRole} model={model} onOpenPacket={openPacket} /> : null}
        {selectedPacket ? <PacketDetail packet={selectedPacket} onOpenPacket={openPacket} onOpenRole={openRole} /> : null}
      </Drawer>
    </div>
  );
}
