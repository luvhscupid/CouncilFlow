# Native model-routing A/B outcome

This is a descriptive record of the sealed, completed offline task comparison.
Both workers were asked for `gpt-6-luna` with `low` reasoning. Independent Tester
reports record both runs as passing all nine fixed oracle fixtures. Each recorded
exit code was `0`; both normalized stdout digests were
`9ed810921d4507720d2297f9fa448c836f7d1b78434e7910cbacb49a560f240c`.

| Measure | A | B |
| --- | --- | --- |
| Fixed oracle cases passed | 9/9 | 9/9 |
| Tester command exit | 0 | 0 |
| Requested model/reasoning | `gpt-6-luna` / `low` | `gpt-6-luna` / `low` |
| Effective model identity | Unverified | Unverified |
| Native SkillLab activation | Not applicable to suggestion arm | Unverified |
| Token, cost and quota observations | Unavailable | Unavailable |
| Comparable duration | Not recorded | Not recorded |

The matching test output shows identical fixture outcomes for this task only. It
does not establish a causal benefit, general reliability, token savings, cost
savings, real provider dispatch, or effective model identity. Selection metadata
does not prove native skill activation. No route authorization or external
provider dispatch occurred as part of this report.

The machine-readable outcome and SHA-256-bound source reports are in
[`benchmark-outcome.json`](../../evidence/native-model-routing/benchmark-outcome.json).

## Preserved evidence

The immutable source/task and independent result messages remain in
`evidence/native-model-routing/benchmark/`: the two Worker reports, two Tester
reports, and assignments. The sealed candidate subtree is not repeated here.
Their digests are checked by the Manager/Tester boundary; this summary does not
replace those records.
