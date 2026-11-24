import React from "react";

const PATHS = {
  owner: "M12 3.5 14.4 8l5 .7-3.6 3.5.9 5L12 14.9 7.3 17.2l.9-5L4.6 8.7l5-.7z",
  planner: "M5 4.5h10l4 4v11H5z M15 4.5v4h4 M8 12h8 M8 15.5h5",
  manager: "M12 9.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z M12 9.5V4 M9.5 12H4 M14.5 12H20 M12 14.5V20 M12 4l-2 2 M12 4l2 2 M4 12l2-2 M4 12l2 2 M20 12l-2-2 M20 12l-2 2 M12 20l-2-2 M12 20l2-2",
  worker: "m14.5 6.5 3-3 3 3-3 3 M4 20l8.7-8.7 M11.5 6.5a5 5 0 0 0 6 6l-7.8 7.8a2.1 2.1 0 0 1-3-3l7.8-7.8",
  tester: "M8 3h8 M10 3v5l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3 M8 14h8 M10 17h4",
  reviewer: "M9 4a5 5 0 1 1 0 10 5 5 0 0 1 0-10z m4 9 5.5 5.5 M7 9l1.5 1.5L11 7.8",
  overview: "M4 4h7v7H4z M13 4h7v4h-7z M13 10h7v10h-7z M4 13h7v7H4z",
  orchestration: "M6 6a2 2 0 1 1 0 .1z M18 6a2 2 0 1 1 0 .1z M12 18a2 2 0 1 1 0 .1z M7.5 7.5 11 16.5 M16.5 7.5 13 16.5 M8 6h8",
  agents: "M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3.5 19a5.5 5.5 0 0 1 11 0 M16 11a2.5 2.5 0 1 0 0-5 M17.5 19a4.5 4.5 0 0 0-2.4-4",
  executions: "M5 5h14 M5 12h9 M5 19h5 M17 15l4 2.5-4 2.5z",
  analytics: "M4 20V10 M10 20V4 M16 20v-7 M22 20H2",
  settings: "M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6z M19 12l2-1-1-3-2.2.2-1.3-1.3L16.7 5 14 4l-1 2h-2l-1-2-2.7 1 .2 2.2L6.2 8.5 4 8.3 3 11l2 1v0l-2 1 1 3 2.2-.2 1.3 1.3-.2 2.2L10 20l1-2h2l1 2 2.7-1-.2-2.2 1.3-1.3 2.2.2 1-3z",
  folder: "M3.5 6.5h6l2 2h9v10h-17z",
  files: "M7 3.5h7l4 4v13H7z M14 3.5v4h4 M4 7v13.5h11",
  refresh: "M19 12a7 7 0 1 1-2.1-5 M19 4.5V8h-3.5",
  pause: "M8 5v14 M16 5v14",
  play: "M7 5l12 7-12 7z",
  close: "M6 6l12 12 M18 6 6 18",
  check: "M5 12.5l4.5 4.5L19 7.5",
  cross: "M7 7l10 10 M17 7 7 17",
  alert: "M12 4 21 19.5H3z M12 10v4.5 M12 17.2v.1",
  shield: "M12 3 19 5.6v5.6c0 4.6-3 7.8-7 10-4-2.2-7-5.4-7-10V5.6z M12 8v4.5 M12 15.6v.1",
  clock: "M12 4a8 8 0 1 1 0 16 8 8 0 0 1 0-16z M12 8v4.5l3 2",
  arrow: "M4 12h15 M13 6l6 6-6 6",
  spark: "M12 3v5 M12 16v5 M3 12h5 M16 12h5 M6 6l3 3 M15 15l3 3 M18 6l-3 3 M9 15l-3 3",
  layers: "M12 4 21 9l-9 5-9-5z M3 14l9 5 9-5"
};

export default function Icon({ name, size = 20, className = "", title }) {
  const d = PATHS[name] || PATHS.overview;
  return (
    <svg className={`icon ${className}`} width={size} height={size} viewBox="0 0 24 24" aria-hidden={title ? undefined : "true"} role={title ? "img" : undefined}>
      {title ? <title>{title}</title> : null}
      <path d={d} />
    </svg>
  );
}
