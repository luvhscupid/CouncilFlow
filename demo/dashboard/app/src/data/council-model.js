/* Derive the dashboard's view model from CouncilFlow run files.
   Pure: no DOM, clock or file access. Every value comes from the given files,
   the run reader's validation, or optional embedded context. Nothing is invented:
   a value that the records do not hold is null with a reason. */
"use strict";

const ROLE_ORDER = ["owner", "planner", "manager", "worker", "tester", "reviewer"];
const ROLE_NAMES = { owner: "Owner", planner: "Planner", manager: "Manager", worker: "Worker", tester: "Tester", reviewer: "Reviewer" };
const ROLE_DUTIES = {
  owner: "Sets the goal and constraints, and decides anything consequential.",
  planner: "Publishes the frozen plan and acceptance, then checks the outcome against it.",
  manager: "Coordinates every handoff and decides on the evidence. Does not implement.",
  worker: "Implements the assigned task exactly as instructed. Cannot approve itself.",
  tester: "Verifies the exact candidate independently. Does not repair it.",
  reviewer: "Compares plan, candidate and Tester evidence, and reruns one declared command."
};

/* The contract's message routes, as drawn edges. `recorded: false` edges are real
   workflow handoffs that CouncilFlow packets do not carry. */
const ROUTES = [
  { id: "owner>planner", from: "owner", to: "planner", label: "Goal and constraints", recorded: false },
  { id: "planner>manager", from: "planner", to: "manager", label: "plan.publish, plan.check", recorded: true },
  { id: "manager>planner", from: "manager", to: "planner", label: "task.decision, plan.progress", recorded: true },
  { id: "manager>worker", from: "manager", to: "worker", label: "job.assign", recorded: true },
  { id: "worker>manager", from: "worker", to: "manager", label: "job.report", recorded: true },
  { id: "manager>tester", from: "manager", to: "tester", label: "job.assign", recorded: true },
  { id: "tester>manager", from: "tester", to: "manager", label: "job.report", recorded: true },
  { id: "manager>reviewer", from: "manager", to: "reviewer", label: "job.assign", recorded: true },
  { id: "reviewer>manager", from: "reviewer", to: "manager", label: "job.report", recorded: true },
  { id: "manager>owner", from: "manager", to: "owner", label: "approval.request", recorded: true },
  { id: "owner>manager", from: "owner", to: "manager", label: "approval.decision", recorded: true },
  { id: "planner>owner", from: "planner", to: "owner", label: "Final result", recorded: false }
];

/* One accepted attempt records these ten packets, in this order. */
const LIFECYCLE = [
  { key: "publish", label: "Plan published", role: "planner", match: m => m.message_type === "plan.publish" },
  { key: "worker-assign", label: "Worker assigned", role: "manager", match: m => m.message_type === "job.assign" && m.recipient.role === "worker" },
  { key: "worker-report", label: "Worker reported", role: "worker", match: m => m.message_type === "job.report" && m.sender.role === "worker" },
  { key: "tester-assign", label: "Tester assigned", role: "manager", match: m => m.message_type === "job.assign" && m.recipient.role === "tester" },
  { key: "tester-report", label: "Tester reported", role: "tester", match: m => m.message_type === "job.report" && m.sender.role === "tester" },
  { key: "reviewer-assign", label: "Reviewer assigned", role: "manager", match: m => m.message_type === "job.assign" && m.recipient.role === "reviewer" },
  { key: "reviewer-report", label: "Reviewer reported", role: "reviewer", match: m => m.message_type === "job.report" && m.sender.role === "reviewer" },
  { key: "decision", label: "Manager decided", role: "manager", match: m => m.message_type === "task.decision" },
  { key: "progress", label: "Progress to Planner", role: "manager", match: m => m.message_type === "plan.progress" },
  { key: "check", label: "Final check", role: "planner", match: m => m.message_type === "plan.check" }
];

function isObject(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function text(value) { return typeof value === "string" && value.trim() ? value.trim() : null; }
function list(value) { return Array.isArray(value) ? value : []; }
function timeOf(iso) { const t = iso ? Date.parse(iso) : NaN; return Number.isFinite(t) ? t : null; }

function describePacket(message) {
  const p = message.payload || {};
  const to = ROLE_NAMES[message.recipient.role] || "a role";
  const from = ROLE_NAMES[message.sender.role] || "A role";
  switch (message.message_type) {
    case "plan.publish": return { title: `${from} published the plan`, verb: "published" };
    case "job.assign": return { title: `${from} assigned the ${to}`, verb: "assigned" };
    case "job.report": return { title: `${from} reported ${String(p.status || "a result").replace("_", " ")}`, verb: "reported" };
    case "task.decision": return { title: `${from} decided to ${p.disposition || "act"}`, verb: "decided" };
    case "plan.progress": return { title: `${from} sent verified progress to the Planner`, verb: "sent progress" };
    case "plan.check": return { title: `${from} ran the final check: ${p.status || "recorded"}`, verb: "checked" };
    case "approval.request": return { title: `${from} asked the Owner to decide`, verb: "asked" };
    case "approval.decision": return { title: `Owner answered: ${p.decision || "recorded"}`, verb: "answered" };
    default: return { title: `${from} sent a packet`, verb: "sent" };
  }
}

function packetOutcome(message) {
  const p = message.payload || {};
  if (message.message_type === "job.report" || message.message_type === "plan.check" || message.message_type === "plan.progress") {
    return { passed: "passed", failed: "failed", blocked: "blocked", in_progress: "active" }[p.status] || "neutral";
  }
  if (message.message_type === "task.decision") {
    return { accept: "passed", rework: "rework", reject: "failed", escalate: "blocked" }[p.disposition] || "neutral";
  }
  return "neutral";
}

function packetDetail(message) {
  const p = message.payload || {};
  return {
    objective: text(p.objective),
    summary: text(p.summary) || text(p.reason) || text(p.question),
    instructions: list(p.instructions).filter(item => typeof item === "string"),
    scope: list(p.scope).filter(item => typeof item === "string"),
    acceptanceIds: list(p.acceptance_ids).filter(item => typeof item === "string"),
    findings: list(p.findings).map(item => typeof item === "string" ? item : isObject(item) ? (text(item.detail) || text(item.summary) || JSON.stringify(item)) : String(item)),
    errors: list(p.errors).map(item => typeof item === "string" ? item : JSON.stringify(item)),
    changedFiles: list(p.changed_files).filter(item => typeof item === "string"),
    checks: list(p.checks).filter(isObject).map(item => ({ name: text(item.name) || text(item.check_id) || "Check", status: text(item.status) || "unknown" })),
    commands: list(p.deterministic_commands).filter(isObject).map(item => ({
      id: text(item.command_id), command: [item.command, ...list(item.arguments)].filter(part => typeof part === "string").join(" "),
      exitCode: Number.isInteger(item.exit_code) ? item.exit_code : null, stdoutSha256: text(item.stdout_sha256)
    })),
    rerun: isObject(p.comparison) && isObject(p.comparison.independent_rerun) ? {
      status: text(p.comparison.independent_rerun.status),
      command: [p.comparison.independent_rerun.command, ...list(p.comparison.independent_rerun.arguments)].filter(part => typeof part === "string").join(" "),
      stdoutSha256: text(p.comparison.independent_rerun.stdout_sha256),
      testerStdoutSha256: text(p.comparison.independent_rerun.tester_stdout_sha256)
    } : null,
    discrepancies: isObject(p.comparison) ? list(p.comparison.discrepancies).map(item => typeof item === "string" ? item : JSON.stringify(item)) : [],
    candidate: isObject(p.candidate_ref) ? { path: text(p.candidate_ref.path), sha256: text(p.candidate_ref.sha256), id: text(p.candidate_ref.artifact_id) } : null,
    disposition: text(p.disposition),
    status: text(p.status),
    nextAction: text(p.next_action),
    results: list(p.results).filter(isObject).map(item => ({ id: text(item.acceptance_id), status: text(item.status) || "unknown", evidence: list(item.evidence_refs).length })),
    evidence: list(message.evidence_refs).filter(isObject).map(item => ({ id: text(item.artifact_id), path: text(item.path), kind: text(item.kind), sha256: text(item.sha256) }))
  };
}

function linkPlan(files, publication, issueCodes) {
  if (!publication || !isObject(publication.payload.plan_ref)) return null;
  const blocked = ["missing_plan", "plan_hash_mismatch", "plan_identity_mismatch", "missing_plan_reference"];
  if (blocked.some(code => issueCodes.has(code))) return null;
  const reference = String(publication.payload.plan_ref.path || "").replace(/\\/g, "/");
  const name = reference.split("/").pop();
  const entry = files.find(item => isObject(item) && !item.error && isObject(item.data) && Array.isArray(item.data.acceptance)
    && (item.name === name || item.path === reference));
  return entry ? entry.data : null;
}

function planTasks(plan) {
  if (!plan) return [];
  return list(plan.tasks).filter(isObject).map(task => ({
    id: text(task.id) || "Task",
    title: text(task.title) || text(list(task.instructions)[0] || "")?.split(/(?<=[.!?])\s/)[0] || null,
    instructionCount: list(task.instructions).length,
    acceptanceIds: list(task.acceptance_ids).filter(item => typeof item === "string"),
    dependsOn: list(task.depends_on || task.dependencies).filter(item => typeof item === "string")
  }));
}

function buildLifecycle(attemptPackets) {
  const steps = LIFECYCLE.map(step => {
    const matches = attemptPackets.filter(packet => step.match(packet.raw));
    const packet = matches[matches.length - 1] || null;
    let status = "pending";
    if (packet) {
      const outcome = packet.outcome;
      status = outcome === "failed" ? "failed" : outcome === "blocked" ? "blocked" : outcome === "active" ? "active" : outcome === "rework" ? "rework" : "done";
    }
    return { key: step.key, label: step.label, role: step.role, status, packetId: packet ? packet.id : null, modified: packet ? packet.modified : null };
  });
  const lastRecorded = steps.reduce((last, step, index) => step.packetId ? index : last, -1);
  const haltIndex = steps.findIndex(step => ["failed", "blocked"].includes(step.status));
  for (let index = 0; index < lastRecorded; index += 1) {
    // Steps after a failed or blocked report are skipped by the decision, not missing.
    if (steps[index].status === "pending") steps[index].status = haltIndex !== -1 && index > haltIndex ? "skipped" : "gap";
  }
  const stopped = steps.some(step => ["failed", "blocked", "rework"].includes(step.status));
  const next = steps.findIndex((step, index) => index > lastRecorded && step.status === "pending");
  if (!stopped && next !== -1 && !steps.some(step => step.status === "active")) steps[next].status = "current";
  const done = steps.filter(step => step.status === "done").length;
  return {
    steps,
    done,
    total: steps.length,
    gaps: steps.filter(step => step.status === "gap").length,
    current: steps.find(step => step.status === "current" || step.status === "active") || null,
    halted: steps.find(step => ["failed", "blocked", "rework"].includes(step.status)) || null,
    complete: done === steps.length
  };
}

function roleState(role, ctx) {
  const { attemptPackets, allPackets, lifecycle, pendingApproval } = ctx;
  const sent = allPackets.filter(packet => packet.from === role);
  const received = allPackets.filter(packet => packet.to === role);
  const last = attemptPackets[attemptPackets.length - 1] || null;
  const state = (key, label, packet) => ({ key, label, sourceId: packet ? packet.id : null });

  if (role === "owner") {
    if (pendingApproval) return state("waiting", "Decision requested", pendingApproval);
    const check = attemptPackets.filter(packet => packet.type === "plan.check").pop();
    if (check && check.outcome === "passed") return state("completed", "Result ready", check);
    return state("idle", allPackets.length ? "Following the run" : "No run loaded", null);
  }
  if (role === "planner") {
    const check = attemptPackets.filter(packet => packet.type === "plan.check").pop();
    if (check) return state(check.outcome === "passed" ? "completed" : check.outcome === "blocked" ? "blocked" : "failed", `Final check ${check.raw.payload.status}`, check);
    const progress = attemptPackets.filter(packet => packet.type === "plan.progress").pop();
    if (progress) return state("reviewing", "Final check due", progress);
    const publish = allPackets.find(packet => packet.type === "plan.publish");
    if (publish) return state("waiting", "Plan published, waiting", publish);
    if (allPackets.length) return state("blocked", "Plan packet not found", null);
    return state("planning", "No plan published yet", null);
  }
  if (role === "manager") {
    if (!allPackets.length) return state("idle", "Waiting for a plan", null);
    if (pendingApproval) return state("blocked", "Waiting for the Owner", pendingApproval);
    if (lifecycle.complete) return state("completed", "Run accepted", last);
    if (last && last.to === "manager") return state("working", `Acting on ${last.title.toLowerCase()}`, last);
    if (last && last.type === "task.decision" && last.outcome === "rework") return state("working", "Preparing the rework", last);
    const decision = attemptPackets.filter(packet => packet.type === "task.decision").pop();
    if (decision && decision.outcome === "failed") return state("failed", "Rejected the attempt", decision);
    if (decision && decision.outcome === "blocked") return state("blocked", "Escalated", decision);
    if (last) return state("waiting", `Waiting on the ${ROLE_NAMES[last.to] || "next role"}`, last);
    return state("idle", "No handoffs yet", null);
  }
  const active = { worker: ["working", "Working"], tester: ["testing", "Testing"], reviewer: ["reviewing", "Reviewing"] }[role];
  const assignments = attemptPackets.filter(packet => packet.type === "job.assign" && packet.to === role);
  const reports = attemptPackets.filter(packet => packet.type === "job.report" && packet.from === role);
  const report = reports[reports.length - 1];
  const assignment = assignments[assignments.length - 1];
  if (report && (!assignment || report.order > assignment.order)) {
    const status = report.raw.payload.status;
    if (status === "passed") return state("completed", "Reported passed", report);
    if (status === "failed") return state("failed", "Reported failed", report);
    if (status === "blocked") return state("blocked", "Reported blocked", report);
    return state(active[0], `${active[1]}, progress reported`, report);
  }
  if (assignment) return state(active[0], active[1], assignment);
  const earlier = sent.concat(received).length;
  return state("idle", earlier ? "Idle in this attempt" : "Not assigned yet", null);
}

function buildRoles(ctx, policy) {
  return ROLE_ORDER.map(role => {
    const sent = ctx.allPackets.filter(packet => packet.from === role);
    const received = ctx.allPackets.filter(packet => packet.to === role);
    const touching = ctx.allPackets.filter(packet => packet.from === role || packet.to === role);
    const instances = [...new Set([...sent.map(packet => packet.raw.sender.instance_id), ...received.map(packet => packet.raw.recipient.instance_id)])];
    const assignment = ctx.attemptPackets.filter(packet => packet.type === "job.assign" && packet.to === role).pop()
      || (role === "planner" || role === "manager" ? ctx.allPackets.find(packet => packet.type === "plan.publish") : null);
    const durations = [];
    if (["worker", "tester", "reviewer"].includes(role)) {
      for (const report of sent.filter(packet => packet.type === "job.report")) {
        const assign = ctx.byId.get(report.raw.in_reply_to);
        if (assign && assign.time !== null && report.time !== null && report.time >= assign.time) durations.push(report.time - assign.time);
      }
    }
    const policyRole = policy && isObject(policy.roles) && isObject(policy.roles[role]) ? policy.roles[role] : null;
    return {
      role,
      name: ROLE_NAMES[role],
      duty: ROLE_DUTIES[role],
      responsibilities: policyRole ? list(policyRole.responsibilities) : [],
      abilities: policyRole ? list(policyRole.abilities) : [],
      writesCode: policyRole ? policyRole.application_code === true : null,
      state: roleState(role, ctx),
      instances,
      sentCount: sent.length,
      receivedCount: received.length,
      history: touching.map(packet => packet.id),
      currentTask: assignment ? {
        packetId: assignment.id,
        objective: assignment.detail.objective,
        instructions: assignment.detail.instructions,
        acceptanceIds: assignment.detail.acceptanceIds
      } : null,
      model: { value: null, reason: "Packets do not record a model. The host's own model selection applies." },
      handlingMs: durations.length ? durations : null
    };
  });
}

const RUN_HREF = /^(?:\.\.\/|\.\/)?(?:[A-Za-z0-9][A-Za-z0-9._-]*\/|\.\.\/)*dashboard\.html$/;

function projectRuns(runs) {
  return list(runs).filter(isObject).slice(0, 200).map(run => ({
    taskId: text(run.taskId),
    href: typeof run.href === "string" && RUN_HREF.test(run.href) ? run.href : null,
    updated: text(run.updated) ? Date.parse(run.updated) : null,
    current: run.current === true
  })).filter(run => run.taskId && run.href);
}

function buildEfficiency(efficiency) {
  if (!isObject(efficiency)) return { available: false, reason: "No Agent Efficiency records were supplied when this board was published.", records: [] };
  const records = list(efficiency.records).filter(isObject);
  if (!records.length) {
    return {
      available: false,
      reason: efficiency.error || `No Agent Efficiency records in ${efficiency.source || "the supplied file"} match this task.`,
      records: [], otherRuns: efficiency.other_runs || 0, invalid: efficiency.invalid || 0
    };
  }
  const sum = key => {
    const values = records.map(record => record.usage && record.usage[key]).filter(value => typeof value === "number");
    return values.length ? { value: values.reduce((a, b) => a + b, 0), reported: values.length } : { value: null, reported: 0 };
  };
  const byModel = new Map();
  for (const record of records) {
    const model = record.upstream_model || "Not reported";
    const entry = byModel.get(model) || { model, records: 0, input: 0, output: 0, known: false };
    entry.records += 1;
    if (typeof record.usage.input === "number") { entry.input += record.usage.input; entry.known = true; }
    if (typeof record.usage.output === "number") { entry.output += record.usage.output; entry.known = true; }
    byModel.set(model, entry);
  }
  return {
    available: true,
    source: efficiency.source || null,
    records: records.map(record => ({
      attempt: record.attempt, harness: record.harness, route: record.route, model: record.upstream_model,
      scope: record.usage_scope, elapsedMs: record.elapsed_ms, input: record.usage.input, cachedInput: record.usage.cached_input,
      output: record.usage.output, cost: record.usage.reported_cost, acceptance: record.acceptance && record.acceptance.status,
      availability: record.usage.availability || {}
    })),
    totals: { input: sum("input"), cachedInput: sum("cached_input"), cacheCreation: sum("cache_creation"), output: sum("output"), cost: sum("reported_cost") },
    byModel: [...byModel.values()],
    otherRuns: efficiency.other_runs || 0,
    invalid: efficiency.invalid || 0,
    warning: efficiency.error || null
  };
}

function buildModel(input, reader) {
  const context = isObject(input) ? input : {};
  const files = list(context.files);
  const snapshot = reader.buildSnapshot(files);
  const scratch = [];
  const fileByMessage = new Map();
  const rawMessages = [];
  for (const entry of files) {
    if (!isObject(entry) || entry.error || !isObject(entry.data) || entry.data.protocol !== "council-flow" || !("message_type" in entry.data)) continue;
    if (!reader.validateMessage(entry.data, scratch, entry.path)) continue;
    rawMessages.push(entry.data);
    if (!fileByMessage.has(entry.data.message_id)) fileByMessage.set(entry.data.message_id, entry);
  }
  const ordered = reader.orderMessages(rawMessages, scratch);
  const packets = ordered.map((message, index) => {
    const entry = fileByMessage.get(message.message_id) || {};
    const description = describePacket(message);
    return {
      id: message.message_id,
      order: index,
      type: message.message_type,
      from: message.sender.role,
      to: message.recipient.role,
      fromInstance: message.sender.instance_id,
      toInstance: message.recipient.instance_id,
      inReplyTo: message.in_reply_to,
      attempt: message.attempt_id,
      title: description.title,
      outcome: packetOutcome(message),
      detail: packetDetail(message),
      file: entry.path || entry.name || null,
      sha256: entry.sha256 || null,
      modified: entry.modified || null,
      time: timeOf(entry.modified),
      raw: message
    };
  });
  const byId = new Map(packets.map(packet => [packet.id, packet]));
  const attempts = [];
  for (const packet of packets) if (!attempts.includes(packet.attempt)) attempts.push(packet.attempt);
  const currentAttempt = packets.length ? packets[packets.length - 1].attempt : null;
  const attemptPackets = packets.filter(packet => packet.type === "plan.publish" || packet.attempt === currentAttempt);
  const lifecycle = buildLifecycle(attemptPackets);
  const answered = new Set(packets.filter(packet => packet.type === "approval.decision").map(packet => packet.raw.payload.approval_request_id || packet.inReplyTo));
  const pendingApproval = packets.filter(packet => packet.type === "approval.request" && !answered.has(packet.id)).pop() || null;
  const ctx = { allPackets: packets, attemptPackets, lifecycle, pendingApproval, byId };
  const issueCodes = new Set(snapshot.issues.map(issue => issue.code).filter(Boolean));
  const publication = packets.find(packet => packet.type === "plan.publish") || null;
  const plan = linkPlan(files, publication && publication.raw, issueCodes);

  const edgeCounts = {};
  for (const packet of packets) edgeCounts[`${packet.from}>${packet.to}`] = (edgeCounts[`${packet.from}>${packet.to}`] || 0) + 1;
  const latest = packets[packets.length - 1] || null;

  const times = packets.map(packet => packet.time).filter(time => time !== null);
  const generated = timeOf(context.generatedAt);
  const timing = {
    source: "file write times",
    available: times.length > 0,
    first: times.length ? Math.min(...times) : null,
    last: times.length ? Math.max(...times) : null,
    span: times.length > 1 ? Math.max(...times) - Math.min(...times) : null,
    generatedAt: generated,
    missing: packets.length - times.length
  };

  const attemptSummaries = attempts.map(attempt => {
    const inAttempt = packets.filter(packet => packet.attempt === attempt);
    const decision = inAttempt.filter(packet => packet.type === "task.decision").pop() || null;
    const attemptTimes = inAttempt.map(packet => packet.time).filter(time => time !== null);
    return {
      id: attempt,
      packets: inAttempt.map(packet => packet.id),
      decision: decision ? decision.raw.payload.disposition : null,
      outcome: decision ? decision.outcome : attempt === currentAttempt ? "active" : "neutral",
      reports: inAttempt.filter(packet => packet.type === "job.report").map(packet => ({ role: packet.from, status: packet.raw.payload.status, id: packet.id })),
      start: attemptTimes.length ? Math.min(...attemptTimes) : null,
      end: attemptTimes.length ? Math.max(...attemptTimes) : null,
      current: attempt === currentAttempt
    };
  });

  const typeCounts = {};
  for (const packet of packets) typeCounts[packet.type] = (typeCounts[packet.type] || 0) + 1;
  const reportOutcomes = {};
  for (const packet of packets.filter(item => item.type === "job.report")) {
    const key = `${packet.from}:${packet.raw.payload.status}`;
    reportOutcomes[key] = (reportOutcomes[key] || 0) + 1;
  }

  return {
    run: {
      taskId: snapshot.taskId || text(context.taskId),
      project: text(context.project),
      planId: snapshot.planId,
      planRevision: publication ? publication.raw.plan_revision : null,
      objective: publication ? text(publication.raw.payload.objective) : null,
      scope: publication ? list(publication.raw.payload.scope).filter(item => typeof item === "string") : [],
      valid: snapshot.valid,
      disposition: snapshot.disposition,
      currentAttempt,
      attemptCount: attempts.length,
      generatedAt: context.generatedAt || null,
      hasPackets: packets.length > 0
    },
    issues: snapshot.issues.map(issue => ({ code: issue.code || null, detail: String(issue.detail || "") })),
    acceptance: {
      criteria: snapshot.criteria,
      passed: snapshot.progress.passed,
      total: snapshot.progress.total,
      verified: snapshot.progress.recorded
    },
    lifecycle,
    roles: buildRoles(ctx, isObject(context.policy) ? context.policy : null),
    routes: ROUTES.map(route => ({ ...route, count: edgeCounts[route.id] || 0, latest: Boolean(latest && `${latest.from}>${latest.to}` === route.id) })),
    packets,
    latest,
    attempts: attemptSummaries,
    plan: plan ? { tasks: planTasks(plan), criteriaCount: list(plan.acceptance).length } : null,
    timing,
    analytics: { typeCounts, reportOutcomes, rework: attemptSummaries.filter(item => item.decision === "rework").length },
    efficiency: buildEfficiency(context.efficiency),
    policy: isObject(context.policy) ? context.policy : null,
    board: context.board === "project" || context.board === "task" ? context.board : null,
    projectRuns: projectRuns(context.runs),
    files: files.filter(isObject).map(entry => ({ path: entry.path || entry.name || "file", sha256: entry.sha256 || null, modified: entry.modified || null, error: entry.error || null, isMessageFile: Boolean(entry.isMessageFile) }))
  };
}

module.exports = { buildModel, ROLE_ORDER, ROLE_NAMES, ROUTES, LIFECYCLE };
