# Worker rework attempt 2

**Result:** Implementation rework complete; not self-approved.

Changed only:

- `tests/test_contracts.py`: the synthetic correction control now first rejects
  a plan with removed Markdown, records and checks that rejected plan bytes
  remain unchanged, then validates a separate new plan artifact with the exact
  authoritative criteria. This does not claim or simulate actual Owner
  authorization.
- `.agents/skills/council-flow/references/communication.md`: removed the stray
  leading `+` before the CLI option.

Checks run from the repository root with Python 3.12:

| Command | Exit | Evidence |
|---|---:|---|
| `python -m unittest tests.test_contracts -v` | 0 | `contracts.stdout.bin`, `contracts.stderr.bin`, `contracts.exit.txt`; 72 tests, 2 Windows symlink skips |
| `python -m py_compile .agents/skills/council-flow/scripts/contracts.py tests/test_contracts.py` | 0 | `pycompile.stdout.bin`, `pycompile.stderr.bin`, `pycompile.exit.txt` |
| `git diff --check` | 0 | `diff-check.stdout.bin`, `diff-check.stderr.bin`, `diff-check.exit.txt`; only Git line-ending notices |

Attempt-1 Tester and Reviewer evidence is preserved separately and remains a
failed review. The fresh Tester must rerun against this candidate and record
stdout hash after CRLF-to-LF-only normalization.
