# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Developers using an AI coding environment who want to coordinate a coding task
through named Planner, Manager, Worker, Tester, and Reviewer responsibilities.
They need a quick, accurate view of who has acted and what acceptance evidence
has been recorded.

## Product Purpose

CouncilFlow is an installable workflow skill for existing AI coding environments.
It guides native role delegation and evidence handoffs so the Owner can follow a
task without relaying outputs between agents.

## Positioning

CouncilFlow uses the host's existing models, tools, permissions, and native
delegation. Its roles are workflow responsibilities, not independent agents,
servers, or processes.

## Operating Context

The workflow is Owner → Planner → Manager → Worker → Tester → Reviewer → Manager
→ Planner → Owner. CouncilFlow 1.0 JSON packets record assignments, reports,
decisions, and acceptance checks. A local browser dashboard can inspect selected
run records without controlling the workflow.

## Capabilities and Constraints

The host remains responsible for execution, delegation, and permissions. Packet
structure does not authenticate senders or enforce native transport. A dashboard
may report what the selected records say, but must not present that as proof of
host activity or add a second orchestration runtime.

## Brand Commitments

The product is named CouncilFlow. The Owner supplied a dark workflow dashboard as
a visual reference for the new browser surface; no broader visual identity was
provided.

## Evidence on Hand

The controlling project charter is
`docs/gate3/CouncilFlow-Gate3-v0.2/01-OWNER-CHARTER.md`. The versioned message
format is in `.agents/skills/council-flow/references/communication.md`. A visual
reference was supplied by the Owner for this dashboard. No production analytics
or live host event API is available in the repository.

## Product Principles

- Preserve the approved role order and authority.
- Keep workflow state in the host and its recorded packets.
- Show gaps as gaps; do not imply that a record is authenticated.
- Keep Manager coordination separate from Worker implementation.

## Accessibility & Inclusion

The browser surface must work with keyboard navigation, visible focus, readable
contrast, responsive layouts, and reduced-motion preferences.
