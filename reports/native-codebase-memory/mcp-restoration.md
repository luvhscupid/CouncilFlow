# MCP restoration follow-up

2026-11-12: The Owner authorized reinstalling Codebase Memory MCP after the
initial integration verification. The earlier final/review/verification reports
remain records of that earlier candidate and unavailable-server observation.

The configured executable was missing. Official release v0.12.1 was downloaded
from DeusData/codebase-memory-mcp and its Windows AMD64 archive matched the
release SHA-256: 4e4e0f16b45233af5c757a1fcbe3c3b16e9056375b1fbe2ce020b6de75dedcc0.
Restoring the executable at the already configured path repaired startup;
the Codex registration did not need changing. No binary or global Codex
configuration is included in this repository.

Observed recovery checks:

- Direct stdio MCP initialization negotiated protocol 2024-11-05 and listed 17 tools.
- A fresh Codex app-server discovered server version 0.12.1 and its tools.
- Indexing the exact CouncilFlow checkout completed successfully.
- This Codex session subsequently exposed native Codebase Memory MCP tools.
- Native list_projects resolved E-Saint-PROJECTS-CouncilFlow-cf-recall to
  E:/Saint/PROJECTS/CouncilFlow-cf-recall; index_status reported ready.
- Native search_graph returned indexed validate_message symbols from historical
  report sources. This bounded positive lookup was a connectivity check, not an
  exhaustive structural assessment of current application code.
- Native coverage for demo/receipt/receipt_calculator.py returned
  no_recorded_issue / metadata_match, with the server's best-effort caveat.

The server excludes some paths, including CouncilFlow skill scripts; direct
source inspection remains necessary there. This session also reports that this
checkout is not its auto-watched session project, so supported explicit refresh
is required before relying on later changes. End-to-end automatic invocation
of the CouncilFlow workflow remains UNVERIFIED; successful MCP connectivity
does not prove that separate behavior.
