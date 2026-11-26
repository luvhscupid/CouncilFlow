# Manager dispatch checklist (mandatory)

Before EVERY dispatch (Worker, Tester, Reviewer):
1. Write the job.assign packet to a file, then run
   `python scripts/contracts.py message <packet.json> --root <repo root> --expected-sender manager --expected-instance <actual Manager instance>`.
   Do not dispatch on a nonzero exit. A sender mismatch (`origin_binding`) is a real failure, not a warning.
2. For Tester and Reviewer, also state the target application's hardware-facing status and the forbidden commands in the assignment, as the role policy requires; this repo's helper has no `dispatch-check` subcommand.
3. Confirm the assignment carries every evidence item the role needs. Missing
   evidence blocks dispatch; it is not a reason to dispatch anyway:
   - Worker/Tester: the exact candidate path and its SHA-256 (`artifact_for_file`).
   - Reviewer: the candidate SHA-256, the Tester's command records (executable,
     arguments, working directory, exit code, stdout SHA-256) and the Tester
     report reference (message ID and file hash).
4. Use the candidate SHA-256 the Worker reports. Do not reuse an old hash after an edit.

On receipt of every report, run `contracts.py message <report.json> --root <repo root>`
before accepting it. Before the final Planner check, run `contracts.py sequence`
over the plan, assignments and reports in causal order. Record in the Owner update
which validations ran and their results.
