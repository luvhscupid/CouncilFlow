const test = require("node:test");
const assert = require("node:assert/strict");
const { buildSnapshot } = require("../run-reader.js");

const hash = "a".repeat(64);
const ids = ["AC1", "AC2"];
const criteria = ids.map(id => ({ id, text: `${id} is supported by recorded evidence.` }));
const plan = { plan_id: "plan-1", plan_revision: 1, task_id: "task-1", acceptance: criteria };
const planRef = { artifact_id: "plan-1-json", path: "plan.json", sha256: hash, kind: "plan" };
const candidateRef = { artifact_id: "candidate", path: "candidate-manifest.json", sha256: "b".repeat(64), kind: "candidate" };
const evidence = { artifact_id: "evidence", path: "evidence.txt", sha256: "c".repeat(64), kind: "evidence" };
const owner = { role: "planner", instance_id: "planner-1" };

function envelope(messageId, type, sender, recipient, inReplyTo, payload, attemptId = "attempt-1") {
  return {
    protocol: "council-flow", version: "1.0", message_id: messageId, message_type: type,
    plan_id: "plan-1", plan_revision: 1, task_id: "task-1", attempt_id: attemptId,
    sender: { role: sender, instance_id: `${sender}-1` },
    recipient: { role: recipient, instance_id: `${recipient}-1` },
    in_reply_to: inReplyTo, payload, evidence_refs: [evidence]
  };
}

function completeMessages() {
  const publish = envelope("m1", "plan.publish", "planner", "manager", null, {
    objective: "Review a task", scope: ["Read packet records"], acceptance_ids: ids, plan_ref: planRef
  });
  const workerAssign = envelope("m2", "job.assign", "manager", "worker", "m1", {
    objective: "Implement the task", scope: ["Bounded source"], acceptance_ids: ids, instructions: ["Implement only the approved change."]
  });
  const workerReport = envelope("m3", "job.report", "worker", "manager", "m2", {
    status: "passed", summary: "Implemented", acceptance_ids: ids, candidate_ref: candidateRef,
    findings: [], errors: [], changed_files: ["demo/dashboard/index.html"]
  });
  const testerAssign = envelope("m4", "job.assign", "manager", "tester", "m3", {
    objective: "Check the candidate", scope: ["Run independent checks"], acceptance_ids: ids,
    instructions: ["Verify the acceptance"], candidate_ref: candidateRef, oracle_ref: evidence
  });
  const testerReport = envelope("m5", "job.report", "tester", "manager", "m4", {
    status: "passed", summary: "All checks passed", acceptance_ids: ids, candidate_ref: candidateRef,
    findings: [], errors: [], oracle_ref: evidence,
    checks: [{ name: "candidate checks", status: "passed", evidence_ref: evidence }],
    deterministic_commands: [{ command_id: "test-1", command: "node", arguments: ["--test"], workdir: ".", candidate_ref: candidateRef, input_refs: [], exit_code: 0, stdout_sha256: hash, acceptance_id: "AC1", evidence_ref: evidence }]
  });
  const reviewerAssign = envelope("m6", "job.assign", "manager", "reviewer", "m5", {
    objective: "Compare the evidence", scope: ["Review candidate and rerun"], acceptance_ids: ids,
    instructions: ["Compare, then rerun"], candidate_ref: candidateRef
  });
  const reviewerReport = envelope("m7", "job.report", "reviewer", "manager", "m6", {
    status: "passed", summary: "Candidate matches the recorded plan and tests", acceptance_ids: ids,
    candidate_ref: candidateRef, findings: [], errors: [],
    comparison: {
      plan_ref: planRef, tester_report_ref: { artifact_id: "m5", path: "messages/tester-report.json", sha256: hash, kind: "message" },
      candidate_ref: candidateRef, findings: [], discrepancies: [],
      independent_rerun: { status: "MATCH", command_id: "test-1", command: "node", arguments: ["--test"], workdir: ".", candidate_ref: candidateRef, input_refs: [], exit_code: 0, stdout_sha256: hash, acceptance_id: "AC1", evidence_ref: evidence, tester_evidence_ref: evidence, tester_exit_code: 0, tester_stdout_sha256: hash }
    }
  });
  const decision = envelope("m8", "task.decision", "manager", "planner", "m7", {
    disposition: "accept", reason: "Independent checks and review are recorded", acceptance_ids: ids,
    candidate_ref: candidateRef, report_ids: ["m3", "m5", "m7"]
  });
  const progress = envelope("m9", "plan.progress", "manager", "planner", "m8", {
    status: "verified", objective: "Review a task", scope: ["Read packet records"], acceptance_ids: ids,
    verified_progress: ["Tester and Reviewer evidence recorded"], next_action: "Check the original acceptance"
  });
  const finalCheck = envelope("m10", "plan.check", "planner", "manager", "m9", {
    status: "passed", summary: "Both criteria have evidence", acceptance_ids: ids, plan_ref: planRef,
    results: ids.map(acceptance_id => ({ acceptance_id, status: "passed", evidence_refs: [evidence] }))
  });
  return [publish, workerAssign, workerReport, testerAssign, testerReport, reviewerAssign, reviewerReport, decision, progress, finalCheck];
}

function input(messages, { planSha = hash } = {}) {
  return [
    { name: "plan.json", path: "plan.json", data: plan, sha256: planSha },
    ...messages.map(data => ({ name: `${data.message_id}.json`, path: `messages/${data.message_id}.json`, data, isMessageFile: true }))
  ];
}

test("starts empty instead of inventing activity", () => {
  const snapshot = buildSnapshot([]);
  assert.equal(snapshot.activity.length, 0);
  assert.equal(snapshot.progress.passed, 0);
  assert.equal(snapshot.valid, false);
});

test("orders actual packets by causal references and records complete acceptance", () => {
  const snapshot = buildSnapshot(input(completeMessages().reverse()));
  assert.equal(snapshot.valid, true);
  assert.equal(snapshot.progress.passed, 2);
  assert.equal(snapshot.progress.total, 2);
  assert.equal(snapshot.progress.recorded, true);
  assert.deepEqual(snapshot.activity.map(item => item.id), completeMessages().map(item => item.message_id));
  assert.equal(snapshot.stages.find(stage => stage.role === "reviewer").tone, "done");
});

test("does not promote a Planner pass without the independent evidence chain", () => {
  const messages = completeMessages().filter(item => !["m3", "m5", "m7"].includes(item.message_id));
  const snapshot = buildSnapshot(input(messages));
  assert.equal(snapshot.progress.passed, 0);
  assert.equal(snapshot.progress.recorded, false);
  assert.ok(snapshot.issues.some(issue => issue.code === "acceptance_chain_incomplete"));
});

test("a publisher diagnostic suppresses recorded acceptance even with a passing chain", () => {
  const entries = input(completeMessages());
  entries.push({ name: "dashboard-validation.json", path: "dashboard-validation.json", data: {}, error: "tester-report-003.json: artifact_hash at evidence_refs: demo/dashboard/tests/run-reader.test.cjs. CouncilFlow packet sequence: missing_parent at m6." });
  const snapshot = buildSnapshot(entries);
  assert.equal(snapshot.valid, false);
  assert.equal(snapshot.progress.recorded, false);
  assert.equal(snapshot.progress.passed, 0);
  assert.ok(snapshot.issues.some(issue => issue.detail.includes("tester-report-003.json") && issue.detail.includes("artifact_hash")));
  assert.ok(snapshot.issues.some(issue => issue.detail.includes("CouncilFlow packet sequence") && issue.detail.includes("missing_parent")));
});

test("a stale test-input hash marks the referenced packet and run incomplete", () => {
  const entries = input(completeMessages());
  entries.push({ name: "dashboard-validation.json", path: "dashboard-validation.json", data: {},
    error: "tester-report-003.json: artifact_hash at evidence_refs: demo/dashboard/tests/run-reader.test.cjs." });
  const snapshot = buildSnapshot(entries);
  assert.equal(snapshot.valid, false);
  assert.equal(snapshot.progress.recorded, false);
  assert.equal(snapshot.progress.passed, 0);
  assert.ok(snapshot.issues.some(issue => issue.detail.includes("tester-report-003.json") && issue.detail.includes("run-reader.test.cjs")));
});

test("an unknown envelope field is identified by file and suppresses acceptance", () => {
  const messages = completeMessages();
  messages[4].unexpected = true;
  const snapshot = buildSnapshot(input(messages));
  assert.equal(snapshot.valid, false);
  assert.equal(snapshot.progress.recorded, false);
  assert.ok(snapshot.issues.some(issue => issue.detail.includes("m5.json") && issue.detail.includes("unexpected")));
});

test("a later attempt does not show the old attempt's acceptance as current", () => {
  const messages = completeMessages();
  const rework = envelope("m11", "task.decision", "manager", "planner", "m10", {
    disposition: "rework", report_ids: ["m7"], acceptance_ids: ids
  });
  const assignment = envelope("m12", "job.assign", "manager", "worker", "m11", {
    acceptance_ids: ids, instructions: ["Repair the candidate"]
  }, "attempt-2");
  const snapshot = buildSnapshot(input([...messages, rework, assignment]));
  assert.equal(snapshot.progress.recorded, false);
  assert.equal(snapshot.progress.passed, 0);
  assert.equal(snapshot.stages.find(stage => stage.role === "worker").state, "Assignment recorded");
});

test("does not promote a Planner pass when the Tester omits an original acceptance criterion", () => {
  const messages = completeMessages();
  messages.find(item => item.message_id === "m5").payload.acceptance_ids = ["AC1"];
  const snapshot = buildSnapshot(input(messages));
  assert.equal(snapshot.progress.passed, 0);
  assert.equal(snapshot.progress.recorded, false);
  assert.ok(snapshot.issues.some(issue => issue.code === "acceptance_chain_incomplete"));
});

test("does not promote a Planner pass when the Reviewer omits an original acceptance criterion", () => {
  const messages = completeMessages();
  messages.find(item => item.message_id === "m7").payload.acceptance_ids = ["AC1"];
  const snapshot = buildSnapshot(input(messages));
  assert.equal(snapshot.progress.passed, 0);
  assert.equal(snapshot.progress.recorded, false);
  assert.ok(snapshot.issues.some(issue => issue.code === "acceptance_chain_incomplete"));
});

test("marks a missing causal predecessor as incomplete", () => {
  const messages = completeMessages().slice(0, 2);
  messages[1].in_reply_to = "unknown-message";
  const snapshot = buildSnapshot(input(messages));
  assert.equal(snapshot.valid, false);
  assert.ok(snapshot.issues.some(issue => issue.code === "missing_parent"));
});

test("does not use a plan whose bytes differ from the published hash", () => {
  const snapshot = buildSnapshot(input(completeMessages(), { planSha: "d".repeat(64) }));
  assert.equal(snapshot.progress.passed, 0);
  assert.ok(snapshot.issues.some(issue => issue.code === "plan_hash_mismatch"));
});

test("reports malformed JSON packets instead of omitting them", () => {
  const snapshot = buildSnapshot([{ name: "bad.json", path: "messages/bad.json", data: null, isMessageFile: true }]);
  assert.equal(snapshot.valid, false);
  assert.ok(snapshot.issues.some(issue => issue.code === "invalid_message_file"));
});

test("flags packet folders containing multiple task or plan identities", () => {
  const messages = completeMessages().slice(0, 2);
  messages[1].task_id = "task-other";
  const snapshot = buildSnapshot(input(messages));
  assert.ok(snapshot.issues.some(issue => issue.code === "mixed_runs"));
});
