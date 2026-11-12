# Reviewer result — E10 remediation, attempt 2

**Result: ACCEPTED_WITH_LIMITATIONS.** The fresh replay exited 0 and matched
the Tester's exit and CRLF-to-LF-only stdout SHA-256. Candidate hashes were
unchanged during the replay. Exact executable, arguments, working directory,
raw outputs, normalized digest, and candidate hashes are recorded in this
folder.

The revised regression rejects a mutated plan, confirms its artifact bytes are
preserved, and then accepts a separate synthetic plan with the original
criteria. Exact comparison uses ordered criterion IDs and strings with no
normalization. Missing/stale sources fail closed in the required mode, unsafe
controls fail, and multiline text remains supported. Historical CSV edits are
tested only with explicitly synthetic input.

The hash validates artifact bytes, not Owner approval. No authentic
Owner-approved CSV fixture was available. E1/E2/E4 remain
`UNVERIFIED (HOST_CAPABILITY_MISSING)`. Gate 3 and the CSV experiment were not
run. Attempt 1's rejected review remains unchanged under
`reports/councilflow-e10/reviewer/`.
