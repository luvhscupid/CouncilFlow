// Synthetic CouncilFlow runs for dashboard tests and screenshots.
// These are fixtures: the dashboard never ships or shows them as live data.
"use strict";

const hash = "a".repeat(64);
const ids = ["AC1", "AC2", "AC3"];
const criteria = [
  { id: "AC1", criterion: "Every record issue appears on its own line in plain words." },
  { id: "AC2", criterion: "Issues that carry only an id keep that id in the sentence." },
  { id: "AC3", criterion: "All repository test suites pass after the change." }
];
const plan = {
  plan_id: "board-issues-plan", plan_revision: 2, task_id: "board-issues",
  acceptance: criteria,
  tasks: [
    { id: "T1", instructions: ["Show each record issue on its own line.", "Keep ids in plain-language sentences."], acceptance_ids: ["AC1", "AC2"], depends_on: [] },
    { id: "T2", instructions: ["Rebuild the release archive and run every suite."], acceptance_ids: ["AC3"], depends_on: ["T1"] }
  ]
};
const planRef = { artifact_id: "plan-json", path: ".councilflow/runs/board-issues/plan.json", sha256: hash, kind: "plan" };
const candidate = n => ({ artifact_id: `candidate-${n}`, path: "candidate-manifest.json", sha256: String(n).repeat(64).slice(0, 64), kind: "candidate" });
const evidence = { artifact_id: "evidence", path: "evidence/test-output.txt", sha256: "c".repeat(64), kind: "evidence" };

function envelope(id, type, sender, recipient, replyTo, payload, attempt) {
  return {
    protocol: "council-flow", version: "1.0", message_id: id, message_type: type,
    plan_id: plan.plan_id, plan_revision: plan.plan_revision, task_id: plan.task_id, attempt_id: attempt,
    sender: { role: sender, instance_id: `${sender}-${attempt === "attempt-2" && sender === "worker" ? 2 : 1}` },
    recipient: { role: recipient, instance_id: `${recipient}-${attempt === "attempt-2" && recipient === "worker" ? 2 : 1}` },
    in_reply_to: replyTo, payload, evidence_refs: [evidence]
  };
}

function report(id, role, replyTo, status, attempt, extra = {}) {
  const c = candidate(attempt === "attempt-2" ? 2 : 1);
  return envelope(id, "job.report", role, "manager", replyTo, {
    status, summary: extra.summary || `${role} ${status}`, acceptance_ids: ids, candidate_ref: c,
    findings: extra.findings || [], errors: extra.errors || [], ...extra.payload
  }, attempt);
}

function testerPayload(c, ok) {
  return {
    oracle_ref: evidence,
    checks: [{ name: "node --test demo/dashboard/tests", status: ok ? "passed" : "failed", evidence_ref: evidence }],
    deterministic_commands: [{ command_id: "suite", command: "node", arguments: ["--test", "demo/dashboard/tests"], workdir: ".", candidate_ref: c, input_refs: [], exit_code: ok ? 0 : 1, stdout_sha256: hash, acceptance_id: "AC3", evidence_ref: evidence }]
  };
}

function attemptOne() {
  const c = candidate(1);
  return [
    envelope("M001", "plan.publish", "planner", "manager", null, { objective: "Show every record issue on its own line", scope: ["Dashboard alert", "Dashboard tests", "Release archive"], acceptance_ids: ids, plan_ref: planRef }, "attempt-1"),
    envelope("M002", "job.assign", "manager", "worker", "M001", { objective: "Implement T1 and T2 exactly as planned", scope: ["dashboard/app.js", "demo/dashboard/tests"], acceptance_ids: ids, instructions: plan.tasks.flatMap(task => task.instructions) }, "attempt-1"),
    report("M003", "worker", "M002", "passed", "attempt-1", { summary: "Alert lists issues one per line; 8 new tests.", payload: { changed_files: ["dashboard/app.js", "demo/dashboard/tests/alert.test.cjs"] } }),
    envelope("M004", "job.assign", "manager", "tester", "M003", { objective: "Verify the candidate independently", scope: ["Run the declared suites"], acceptance_ids: ids, instructions: ["Run every suite against the exact candidate."], candidate_ref: c, oracle_ref: evidence }, "attempt-1"),
    report("M005", "tester", "M004", "failed", "attempt-1", { summary: "Alert drops issues past the twentieth without saying so.", findings: ["AC1: the 21st issue is silently dropped."], payload: testerPayload(c, false) }),
    envelope("M006", "task.decision", "manager", "planner", "M005", { disposition: "rework", reason: "Tester found AC1 unmet.", acceptance_ids: ids, candidate_ref: c, report_ids: ["M003", "M005"] }, "attempt-1")
  ];
}

function attemptTwo(stage) {
  const c = candidate(2);
  const all = [
    envelope("M007", "job.assign", "manager", "worker", "M006", { objective: "Rework: show a count line after the twentieth issue", scope: ["dashboard/app.js"], acceptance_ids: ids, instructions: ["Cap the list at 20 and add 'N more not shown'."] }, "attempt-2"),
    report("M008", "worker", "M007", "passed", "attempt-2", { summary: "Added the cap line and a test for it.", payload: { changed_files: ["dashboard/app.js"] } }),
    envelope("M009", "job.assign", "manager", "tester", "M008", { objective: "Verify the reworked candidate", scope: ["Run the declared suites"], acceptance_ids: ids, instructions: ["Run every suite against the exact candidate."], candidate_ref: c, oracle_ref: evidence }, "attempt-2"),
    report("M010", "tester", "M009", "passed", "attempt-2", { summary: "All suites pass; old code fails the new probes.", payload: testerPayload(c, true) }),
    envelope("M011", "job.assign", "manager", "reviewer", "M010", { objective: "Compare plan, candidate and Tester evidence", scope: ["Review and rerun"], acceptance_ids: ids, instructions: ["Rerun the declared suite command."], candidate_ref: c }, "attempt-2"),
    report("M012", "reviewer", "M011", "passed", "attempt-2", {
      summary: "Diff within scope; rerun hash matches the Tester's.",
      payload: { comparison: {
        plan_ref: planRef, tester_report_ref: { artifact_id: "M010", path: "messages/M010.json", sha256: hash, kind: "message" },
        candidate_ref: c, findings: [], discrepancies: [],
        independent_rerun: { status: "MATCH", command_id: "suite", command: "node", arguments: ["--test", "demo/dashboard/tests"], workdir: ".", candidate_ref: c, input_refs: [], exit_code: 0, stdout_sha256: hash, acceptance_id: "AC3", evidence_ref: evidence, tester_evidence_ref: evidence, tester_exit_code: 0, tester_stdout_sha256: hash }
      } }
    }),
    envelope("M013", "task.decision", "manager", "planner", "M012", { disposition: "accept", reason: "Independent test and review evidence recorded.", acceptance_ids: ids, candidate_ref: c, report_ids: ["M008", "M010", "M012"] }, "attempt-2"),
    envelope("M014", "plan.progress", "manager", "planner", "M013", { status: "verified", objective: "Show every record issue on its own line", scope: ["Dashboard alert"], acceptance_ids: ids, verified_progress: ["Tester and Reviewer evidence recorded"], next_action: "Check the original acceptance" }, "attempt-2"),
    envelope("M015", "plan.check", "planner", "manager", "M014", { status: "passed", summary: "AC1 to AC3 have evidence.", acceptance_ids: ids, plan_ref: planRef, results: ids.map(acceptance_id => ({ acceptance_id, status: "passed", evidence_refs: [evidence] })) }, "attempt-2")
  ];
  const count = { assigned: 1, testing: 3, reviewing: 5, accepted: all.length }[stage];
  return all.slice(0, count);
}

const STAGES = {
  planned: () => attemptOne().slice(0, 1),
  working: () => attemptOne().slice(0, 2),
  testing: () => attemptOne().slice(0, 4),
  sent_back: () => attemptOne(),
  rework: () => [...attemptOne(), ...attemptTwo("testing")],
  reviewing: () => [...attemptOne(), ...attemptTwo("reviewing")],
  accepted: () => [...attemptOne(), ...attemptTwo("accepted")]
};

/* start: ms epoch for the first packet; gaps: minutes between packets, cycled. */
function scenario(stage, { start = Date.UTC(2026, 10, 24, 9, 12, 0), gaps = [3, 11, 2, 7, 1, 4, 9, 2, 6, 1, 3, 5, 1, 2] } = {}) {
  const messages = STAGES[stage]();
  let time = start;
  const files = [{ name: "plan.json", path: ".councilflow/runs/board-issues/plan.json", data: plan, isMessageFile: false, sha256: hash, modified: new Date(start - 60000).toISOString() }];
  messages.forEach((data, index) => {
    if (index) time += gaps[(index - 1) % gaps.length] * 60000;
    files.push({ name: `${data.message_id}.json`, path: `.councilflow/runs/board-issues/messages/${data.message_id}.json`, data, isMessageFile: true, sha256: hash, modified: new Date(time).toISOString() });
  });
  return { taskId: plan.task_id, files };
}

module.exports = { scenario, stages: Object.keys(STAGES), plan };
