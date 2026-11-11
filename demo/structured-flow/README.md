# Fresh structured-communication demonstration

This isolated offline program accepts positional signed ASCII integers:

~~~sh
python3 demo/structured-flow/sum_values.py 2 3 -1
python3 -m unittest discover -s demo/structured-flow -v
~~~

The first command prints `4`. All operands are summed exactly, including negative
values and zero. Missing/malformed inputs fail clearly without a traceback. No
third-party dependency or network is needed.

The initial primary Worker deliberately supplied a valid **incomplete fixture**
that returned only the first operand. A separate Tester observed the mandatory
multiple-value failure (`2` instead of `4`); the Manager rejected that candidate
and assigned a fresh Worker to repair it under unchanged acceptance. The current
program includes that repair and the same four acceptance tests pass. The initial
source and failed output are preserved under `reports/restoration/worker/` and
`reports/restoration/verification/initial/`. This is a new execution, not the old
receipt demonstration; independent final verification is recorded separately.

Actual JSON task packets, independent observations, rework and final outcomes
belong in reports/restoration/. Synthetic unit fixtures never count as agents.
