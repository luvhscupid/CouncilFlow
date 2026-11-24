/* Pure CouncilFlow packet-to-view-state module. No DOM, clock, or file access. */
(function (root, factory) {
  const reader = factory();
  if (typeof module === "object" && module.exports) module.exports = reader;
  else root.CouncilFlowRunReader = reader;
})(typeof globalThis === "object" ? globalThis : this, function () {
  "use strict";

  const roles = ["planner", "manager", "worker", "tester", "reviewer"];
  const roleNames = { planner: "Planner", manager: "Manager", worker: "Worker", tester: "Tester", reviewer: "Reviewer" };
  const messageTypes = new Set(["plan.publish", "job.assign", "job.report", "task.decision", "plan.progress", "plan.check", "approval.request", "approval.decision"]);
  const messageFields = new Set(["protocol", "version", "message_id", "message_type", "plan_id", "plan_revision", "task_id", "attempt_id", "sender", "recipient", "in_reply_to", "payload", "evidence_refs"]);
  const routes = {
    "plan.publish": ["planner", "manager"], "plan.check": ["planner", "manager"],
    "plan.progress": ["manager", "planner"], "job.assign": ["manager", "worker|tester|reviewer"],
    "job.report": ["worker|tester|reviewer", "manager"], "task.decision": ["manager", "planner"],
    "approval.request": ["manager", "owner"], "approval.decision": ["owner", "manager"]
  };

  function recordIssue(issues, code, detail) {
    issues.push({ code, detail });
  }

  function isObject(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
  function nonEmpty(value) { return typeof value === "string" && value.trim().length > 0; }
  function isActor(value) { return isObject(value) && nonEmpty(value.role) && nonEmpty(value.instance_id); }
  function samePlan(a, b) {
    return a.task_id === b.task_id && a.plan_id === b.plan_id && a.plan_revision === b.plan_revision;
  }

  function orderMessages(messages, issues) {
    const byId = new Map();
    for (const message of messages) {
      if (!nonEmpty(message.message_id)) continue;
      if (byId.has(message.message_id)) recordIssue(issues, "duplicate_message_id", message.message_id);
      else byId.set(message.message_id, message);
    }

    const incoming = new Map(messages.map(message => [message, 0]));
    const children = new Map(messages.map(message => [message, []]));
    for (const message of messages) {
      if (message.in_reply_to === null) {
        if (message.message_type !== "plan.publish") recordIssue(issues, "orphan_message", `${message.message_id} has no causal predecessor.`);
        continue;
      }
      const parent = byId.get(message.in_reply_to);
      if (!parent) {
        recordIssue(issues, "missing_parent", `${message.message_id} refers to ${message.in_reply_to}`);
        continue;
      }
      if (!samePlan(parent, message)) {
        recordIssue(issues, "cross_run_parent", message.message_id);
        continue;
      }
      if (parent.attempt_id !== message.attempt_id && !(parent.message_type === "task.decision" && parent.payload.disposition === "rework" && message.message_type === "job.assign" && message.recipient.role === "worker")) {
        recordIssue(issues, "cross_attempt_parent", message.message_id);
        continue;
      }
      incoming.set(message, incoming.get(message) + 1);
      children.get(parent).push(message);
    }

    const ready = messages.filter(message => incoming.get(message) === 0).sort((a, b) => a.message_id.localeCompare(b.message_id));
    const ordered = [];
    while (ready.length) {
      const current = ready.shift();
      ordered.push(current);
      for (const child of children.get(current)) {
        incoming.set(child, incoming.get(child) - 1);
        if (incoming.get(child) === 0) ready.push(child);
      }
      ready.sort((a, b) => a.message_id.localeCompare(b.message_id));
    }
    if (ordered.length !== messages.length) recordIssue(issues, "causal_cycle", "Packet reply references contain a cycle.");
    return ordered;
  }

  function validateMessage(message, issues, sourceName) {
    if (!isObject(message)) { recordIssue(issues, "invalid_message", "A packet is not a JSON object."); return false; }
    const unknown = Object.keys(message).filter(key => !messageFields.has(key));
    if (unknown.length) { recordIssue(issues, "unknown_fields", `${sourceName ? `${sourceName}: ` : ""}${message.message_id || "Packet"}: ${unknown.join(", ")}`); return false; }
    const required = ["protocol", "version", "message_id", "message_type", "plan_id", "plan_revision", "task_id", "attempt_id", "sender", "recipient", "in_reply_to", "payload", "evidence_refs"];
    const missing = required.filter(key => !(key in message));
    if (missing.length) { recordIssue(issues, "missing_fields", `${message.message_id || "Packet"}: ${missing.join(", ")}`); return false; }
    if (message.protocol !== "council-flow" || message.version !== "1.0") { recordIssue(issues, "unsupported_contract", message.message_id || "Unknown packet"); return false; }
    if (!nonEmpty(message.message_id) || !messageTypes.has(message.message_type) || !nonEmpty(message.plan_id) || !nonEmpty(message.task_id) || !nonEmpty(message.attempt_id) || !Number.isInteger(message.plan_revision) || message.plan_revision < 1) {
      recordIssue(issues, "invalid_identity", message.message_id || "Packet identity or type is invalid."); return false;
    }
    if (!isActor(message.sender) || !isActor(message.recipient) || !(message.in_reply_to === null || nonEmpty(message.in_reply_to)) || !Array.isArray(message.evidence_refs) || !isObject(message.payload)) {
      recordIssue(issues, "invalid_envelope", message.message_id); return false;
    }
    const [senders, recipients] = routes[message.message_type];
    if (!senders.split("|").includes(message.sender.role) || !recipients.split("|").includes(message.recipient.role)) {
      recordIssue(issues, "invalid_route", message.message_id); return false;
    }
    if (message.message_type === "plan.publish" && (message.sender.role !== "planner" || message.in_reply_to !== null || !Array.isArray(message.payload.acceptance_ids) || !message.payload.acceptance_ids.length)) {
      recordIssue(issues, "invalid_plan_publication", message.message_id); return false;
    }
    if (message.message_type === "job.assign" && (!Array.isArray(message.payload.acceptance_ids) || !message.payload.acceptance_ids.length || !Array.isArray(message.payload.instructions))) {
      recordIssue(issues, "invalid_assignment", message.message_id); return false;
    }
    if (message.message_type === "job.report" && (!Array.isArray(message.payload.acceptance_ids) || !["passed", "failed", "blocked", "in_progress"].includes(message.payload.status))) {
      recordIssue(issues, "invalid_report", message.message_id); return false;
    }
    if (message.message_type === "plan.check" && (!Array.isArray(message.payload.results) || !Array.isArray(message.payload.acceptance_ids) || !["passed", "failed", "blocked"].includes(message.payload.status))) {
      recordIssue(issues, "invalid_final_check", message.message_id); return false;
    }
    if (message.message_type === "task.decision" && (!Array.isArray(message.payload.report_ids) || !["accept", "rework", "reject", "escalate"].includes(message.payload.disposition))) {
      recordIssue(issues, "invalid_decision", message.message_id); return false;
    }
    return true;
  }

  function labelFor(message) {
    const p = message.payload || {};
    const sender = roleNames[message.sender.role] || "Owner";
    if (message.message_type === "plan.publish") return `${sender} published the plan`;
    if (message.message_type === "job.assign") return `${sender} assigned ${roleNames[message.recipient.role] || "a role"}`;
    if (message.message_type === "job.report") return `${sender} returned a ${p.status || "recorded"} report`;
    if (message.message_type === "task.decision") return `${sender} recorded ${p.disposition || "a decision"}`;
    if (message.message_type === "plan.progress") return `${sender} sent the final progress record`;
    if (message.message_type === "plan.check") return `${sender} checked the acceptance criteria`;
    if (message.message_type === "approval.request") return `${sender} requested an Owner decision`;
    if (message.message_type === "approval.decision") return "Owner recorded an authorization decision";
    return `${sender} added a packet`;
  }

  function stageState(role, ordered) {
    const roleAssignments = ordered.filter(message => message.message_type === "job.assign" && message.recipient.role === role);
    const roleReports = ordered.filter(message => message.message_type === "job.report" && message.sender.role === role);
    const lastReport = roleReports[roleReports.length - 1];
    const lastAssignment = roleAssignments[roleAssignments.length - 1];
    if (role === "planner") {
      if (ordered.some(message => message.message_type === "plan.check")) return { state: "Final check recorded", tone: "done" };
      if (ordered.some(message => message.message_type === "plan.publish")) return { state: "Plan published", tone: "done" };
      return { state: "Waiting", tone: "idle" };
    }
    if (role === "manager") {
      const decision = ordered.filter(message => message.message_type === "task.decision").at(-1);
      if (decision) return { state: `Decision: ${decision.payload.disposition}`, tone: decision.payload.disposition === "accept" ? "done" : "active" };
      if (roleAssignments.length) return { state: "Handoff recorded", tone: "done" };
      return { state: "Waiting", tone: "idle" };
    }
    if (lastReport) return { state: `${lastReport.payload.status} report recorded`, tone: lastReport.payload.status === "passed" ? "done" : lastReport.payload.status === "in_progress" ? "active" : "issue" };
    if (lastAssignment) return { state: "Assignment recorded", tone: "active" };
    return { state: "Waiting", tone: "idle" };
  }

  function hasCompleteAcceptanceChain(finalCheck, messages, publication) {
    const byId = new Map(messages.map(message => [message.message_id, message]));
    const progress = byId.get(finalCheck.in_reply_to);
    const decision = progress && byId.get(progress.in_reply_to);
    if (!progress || progress.message_type !== "plan.progress" || !decision || decision.message_type !== "task.decision" || decision.payload.disposition !== "accept") return false;
    if (!(progress.payload.acceptance_ids || []).length || !(decision.payload.acceptance_ids || []).length) return false;
    const requiredIds = publication && publication.payload && publication.payload.acceptance_ids;
    const coversAllCriteria = claimedIds => {
      if (!Array.isArray(claimedIds) || claimedIds.length !== requiredIds.length) return false;
      const claimed = new Set(claimedIds);
      return claimed.size === requiredIds.length && requiredIds.every(id => claimed.has(id));
    };
    if (!Array.isArray(requiredIds) || !requiredIds.length
        || !coversAllCriteria(decision.payload.acceptance_ids)
        || !coversAllCriteria(progress.payload.acceptance_ids)) return false;
    const reports = (decision.payload.report_ids || []).map(id => byId.get(id)).filter(Boolean);
    const roleReports = {};
    for (const role of ["worker", "tester", "reviewer"]) {
      roleReports[role] = reports.find(report => report.message_type === "job.report" && report.sender.role === role && report.payload.status === "passed" && report.attempt_id === decision.attempt_id);
      if (!roleReports[role] || !coversAllCriteria(roleReports[role].payload.acceptance_ids)) return false;
      if ((roleReports[role].payload.errors || []).length || (roleReports[role].payload.checks || []).some(check => check.status !== "passed")) return false;
      const assignment = byId.get(roleReports[role].in_reply_to);
      if (!assignment || assignment.message_type !== "job.assign" || assignment.recipient.role !== role || assignment.recipient.instance_id !== roleReports[role].sender.instance_id || !coversAllCriteria(assignment.payload.acceptance_ids)) return false;
    }
    const worker = roleReports.worker;
    const tester = roleReports.tester;
    const reviewer = roleReports.reviewer;
    const candidate = worker.payload.candidate_ref;
    const sameRef = (a, b) => isObject(a) && isObject(b) && a.artifact_id === b.artifact_id && a.path === b.path && a.sha256 === b.sha256 && a.kind === b.kind;
    if (!sameRef(tester.payload.candidate_ref, candidate) || !sameRef(reviewer.payload.candidate_ref, candidate)) return false;
    if (new Set([worker.sender.instance_id, tester.sender.instance_id, reviewer.sender.instance_id]).size !== 3) return false;
    const comparison = reviewer.payload.comparison;
    if (!isObject(comparison) || !sameRef(comparison.candidate_ref, candidate) || !sameRef(comparison.plan_ref, publication.payload.plan_ref)) return false;
    if (!isObject(comparison.tester_report_ref) || comparison.tester_report_ref.artifact_id !== tester.message_id || comparison.tester_report_ref.kind !== "message") return false;
    if (!isObject(comparison.independent_rerun) || comparison.independent_rerun.status !== "MATCH" || (comparison.discrepancies || []).length) return false;
    const rerun = comparison.independent_rerun;
    const declared = (tester.payload.deterministic_commands || []).find(command => command.command_id === rerun.command_id);
    if (!declared || !sameRef(declared.candidate_ref, candidate) || !sameRef(rerun.candidate_ref, candidate)) return false;
    if (declared.command !== rerun.command || declared.workdir !== rerun.workdir || JSON.stringify(declared.arguments) !== JSON.stringify(rerun.arguments)) return false;
    if (declared.exit_code !== rerun.exit_code || declared.exit_code !== rerun.tester_exit_code || declared.stdout_sha256 !== rerun.stdout_sha256 || declared.stdout_sha256 !== rerun.tester_stdout_sha256) return false;
    return true;
  }

  function acceptanceFromPlan(plan, messages, issues, publication) {
    // Planner plans carry the original wording as `criterion`; older fixtures use `text`.
    const acceptance = (Array.isArray(plan && plan.acceptance) ? plan.acceptance : [])
      .map(item => isObject(item) && !nonEmpty(item.text) && nonEmpty(item.criterion) ? { ...item, text: item.criterion } : item);
    if (!acceptance.length || acceptance.some(item => !isObject(item) || !nonEmpty(item.id) || !nonEmpty(item.text)) || new Set(acceptance.map(item => item.id)).size !== acceptance.length) {
      recordIssue(issues, "invalid_plan_criteria", "The linked plan has no valid unique acceptance criteria.");
      return { criteria: [], passed: 0, total: 0, finalRecorded: false };
    }
    const ids = acceptance.map(item => item.id);
    const checks = messages.filter(message => message.message_type === "plan.check" && message.sender.role === "planner");
    const finalCheck = checks.at(-1);
    let resultsById = new Map();
    let finalRecorded = false;
    if (finalCheck) {
      const results = finalCheck.payload.results;
      const mapped = new Map(Array.isArray(results) ? results.filter(result => isObject(result) && nonEmpty(result.acceptance_id)).map(result => [result.acceptance_id, result]) : []);
      const publishedIds = publication && publication.payload.acceptance_ids || [];
      const exact = ids.every(id => mapped.has(id)) && mapped.size === ids.length && ids.every(id => (finalCheck.payload.acceptance_ids || []).includes(id)) && ids.length === publishedIds.length && ids.every(id => publishedIds.includes(id));
      if (!exact) recordIssue(issues, "incomplete_final_check", "Final check does not map every original plan criterion exactly once.");
      else {
        resultsById = mapped;
        finalRecorded = true;
        for (const id of ids) {
          const result = mapped.get(id);
          if (!Array.isArray(result.evidence_refs) || (result.status === "passed" && result.evidence_refs.length === 0)) {
            recordIssue(issues, "missing_criterion_evidence", id);
            finalRecorded = false;
          }
        }
        const completePass = finalCheck.payload.status === "passed" && ids.every(id => mapped.get(id).status === "passed" && Array.isArray(mapped.get(id).evidence_refs) && mapped.get(id).evidence_refs.length > 0);
        if (completePass && !hasCompleteAcceptanceChain(finalCheck, messages, publication)) {
          recordIssue(issues, "acceptance_chain_incomplete", "The passing final check is missing linked Worker, Tester, Reviewer, Manager, or independent-rerun evidence.");
          finalRecorded = false;
          resultsById = new Map();
        }
        if (finalCheck.payload.status === "passed" && ids.some(id => mapped.get(id).status !== "passed")) {
          recordIssue(issues, "contradictory_final_check", "A passed summary includes an unmet criterion.");
          finalRecorded = false;
        }
      }
    }
    const criteria = acceptance.map(item => {
      const result = resultsById.get(item.id);
      return { id: item.id, text: item.text, status: !result ? "unchecked" : result.status, evidenceCount: result && Array.isArray(result.evidence_refs) ? result.evidence_refs.length : 0 };
    });
    const passed = finalRecorded ? criteria.filter(item => item.status === "passed" && item.evidenceCount > 0).length : 0;
    return { criteria, passed, total: criteria.length, finalRecorded };
  }

  function buildSnapshot(input) {
    const entries = Array.isArray(input) ? input : [];
    const issues = [];
    const messages = [];
    const messageSources = new Map();
    const plans = [];
    for (const entry of entries) {
      if (!isObject(entry) || !("data" in entry)) { recordIssue(issues, "invalid_input", "A selected file could not be read."); continue; }
      if (entry.error) {
        recordIssue(issues, "input_error", `${entry.path || entry.name || "Selected file"}: ${entry.error}`);
        continue;
      }
      const data = entry.data;
      if (isObject(data) && data.protocol === "council-flow" && "message_type" in data) {
        messages.push(data);
        messageSources.set(data.message_id, entry.path || entry.name || null);
      } else if (isObject(data) && Array.isArray(data.acceptance) && "plan_id" in data && "plan_revision" in data) {
        plans.push({ ...entry, plan: data });
      } else if (entry.isMessageFile) {
        recordIssue(issues, "invalid_message_file", entry.path || entry.name || "Message file is not a CouncilFlow packet.");
      }
    }
    const validMessages = messages.filter(message => validateMessage(message, issues, messageSources.get(message.message_id)));
    const taskKeys = new Set(validMessages.map(message => `${message.task_id}/${message.plan_id}/${message.plan_revision}`));
    if (taskKeys.size > 1) recordIssue(issues, "mixed_runs", "Choose packet files from one task and plan at a time.");
    const ordered = orderMessages(validMessages, issues);
    for (const message of ordered) {
      if (message.message_type !== "plan.publish") {
        const parent = validMessages.find(item => item.message_id === message.in_reply_to);
        if (!parent) continue;
        if (message.message_type === "job.report" && (parent.message_type !== "job.assign" || parent.recipient.role !== message.sender.role)) {
          recordIssue(issues, "report_without_matching_assignment", message.message_id);
        }
        if (message.message_type === "plan.check" && (parent.message_type !== "plan.progress" || message.sender.role !== "planner")) {
          recordIssue(issues, "final_check_without_progress", message.message_id);
        }
      }
    }
    const publication = ordered.find(message => message.message_type === "plan.publish");
    let plan = null;
    if (publication) {
      const reference = publication.payload.plan_ref;
      if (!isObject(reference) || !nonEmpty(reference.path)) {
        recordIssue(issues, "missing_plan_reference", "The plan.publish packet does not name a plan file.");
      }
      const linked = !isObject(reference) || !nonEmpty(reference.path) ? undefined : plans.find(entry => {
        const artifact = reference && reference.path ? reference.path.replace(/\\/g, "/").split("/").pop() : "";
        return entry.name === artifact || entry.path === reference.path;
      });
      if (!isObject(reference) || !nonEmpty(reference.path)) { /* reported above as missing_plan_reference */ }
      else if (!linked) recordIssue(issues, "missing_plan", "The plan referenced by plan.publish was not found in the selected folder.");
      else if (reference.sha256 && !linked.sha256) recordIssue(issues, "plan_hash_unverifiable", "This browser cannot verify the selected plan's SHA-256.");
      else if (linked.sha256 && reference.sha256 && linked.sha256 !== reference.sha256) recordIssue(issues, "plan_hash_mismatch", "The selected plan file does not match the published plan hash.");
      else if (linked.plan.plan_id !== publication.plan_id || linked.plan.plan_revision !== publication.plan_revision || linked.plan.task_id !== publication.task_id) {
        recordIssue(issues, "plan_identity_mismatch", "The selected plan does not match the published task identity.");
      } else plan = linked.plan;
    }
    if (!publication) recordIssue(issues, "missing_publication", "No Planner plan.publish packet was found.");
    const latestAttempt = ordered.length ? ordered[ordered.length - 1].attempt_id : publication && publication.attempt_id;
    const attemptMessages = ordered.filter(message => message.message_type === "plan.publish" || message.attempt_id === latestAttempt);
    const acceptance = plan ? acceptanceFromPlan(plan, attemptMessages, issues, publication) : { criteria: [], passed: 0, total: publication && Array.isArray(publication.payload.acceptance_ids) ? publication.payload.acceptance_ids.length : 0, finalRecorded: false };
    const activeEvents = attemptMessages.map((message, index) => ({ id: message.message_id, label: labelFor(message), role: message.sender.role, type: message.message_type, index: index + 1 }));
    const stages = roles.map(role => ({ role, label: roleNames[role], ...stageState(role, attemptMessages) }));
    const current = activeEvents[activeEvents.length - 1] || null;
    const displayAcceptance = issues.length ? {
      ...acceptance,
      criteria: acceptance.criteria.map(item => ({ ...item, status: "unchecked", evidenceCount: 0 })),
      passed: 0,
      finalRecorded: false
    } : acceptance;
    const passed = displayAcceptance.finalRecorded && displayAcceptance.total > 0 && displayAcceptance.passed === displayAcceptance.total;
    return {
      valid: Boolean(publication) && issues.length === 0,
      issues,
      taskId: publication ? publication.task_id : null,
      planId: publication ? publication.plan_id : null,
      stages,
      criteria: displayAcceptance.criteria,
      progress: { passed: displayAcceptance.passed, total: displayAcceptance.total, recorded: displayAcceptance.finalRecorded },
      activity: activeEvents,
      current,
      disposition: passed ? "All criteria recorded as passed" : displayAcceptance.finalRecorded ? "Final check recorded" : publication ? "Run in progress" : "Waiting for a run",
      sourceNotice: "Informational packet view. Sender identity and host activity are not authenticated."
    };
  }

  return { buildSnapshot, validateMessage, orderMessages };
});
