# Rework and recovery

1. Preserve the failing original acceptance ID, exact candidate, command/output
   and evidence hash. Tester reports failed technical status through job.report
   JSON, not a prose substitute; it never repairs product code. If the Planner
   finds a mandatory criterion unmet after Manager acceptance, preserve that
   failed plan.check and its cited evidence unchanged.
2. Manager records task.decision rework/reject/escalate with causal report IDs and
   evidence. For Planner-detected rework, the decision replies to the exact
   failed plan.check and carries every failed original acceptance ID unchanged.
   Never accept a mandatory failure or lower criteria. Ordinary scoped
   engineering repair is already authorized and does not need Owner reapproval.
3. Delegate job.assign JSON to a fresh native Worker and new attempt. Prior
   Worker must stop. One mutating Worker per workspace; parallel implementation
   requires independently authorized isolation. Preserve original plan/hash.
4. Independently recheck changed candidate, then the approved Reviewer comparison;
   finish with original Planner plan.check. Keep old failures and actual repair
   decisions instead of overwriting inconvenient history.
5. There is no arbitrary lifetime engineering-repair cap. Continue useful,
   authorized progress within budget/native limits. Stop identical unproductive
   retries when no new evidence or meaningful alternative exists.
6. YAML's three infrastructure retries and two crash recoveries are **policy
   instructions only**. CouncilFlow has no corresponding persistent accounting
   runtime; do not confuse these numbers with normal Worker repair attempts or
   claim enforcement/crash safety.
7. Only genuinely consequential new scope/authorization or required subjective
   acceptance needs Owner action. Prepare a concrete reviewable result before
   approval.request. approval.decision must reference actual Owner input, never
   an AI-created permission. No external-path, global-config, security-policy,
   paid-provider, ACL or authentication bypass may be self-authorized.

Newly discovered authorized follow-up work is distinct from failed mandatory
acceptance. Preserve successful candidate verification and start a separate
bounded task/plan publication boundary when appropriate. Record a real failed
Tester/Reviewer report or Planner check only when its actual criterion is unmet;
sequence grammar never justifies manufacturing a failure. Keep invalid historical
message chains unchanged and identify the new boundary and its causal reason.

JSON structure/context validation does not authenticate a sender or enforce OS
isolation. Respect native permissions. If native activation, a role or tests
cannot run, preserve evidence, mark the precise gap, and continue independent
authorized work. Never replace unavailable native agents with scripted exchanges.

Contract restoration may pass while native activation is UNVERIFIED. Use
CONTRACT_RESTORED — NATIVE_ACTIVATION_UNVERIFIED for that case. Only genuine
invocation plus real required roles supports COUNCILFLOW_FULLY_VERIFIED.
