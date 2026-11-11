# ReviewerResult — CF-DEMO-001

- Role: Reviewer; actual native session `/root/demo_reviewer`.
- Request reference: parent Manager ReviewerRequest CF-DEMO-001.
- Contract: `reports/contracts/demo.json`, revision 1, original D01–D10 unchanged.
- Objective: assess first-use instructions and actual receipt-calculator interaction after independent technical verification.
- Scope: read repository instructions and use the finished CLI; write only this report and `reports/demo/review/` evidence.
- Implementation status: REVIEWED; no implementation, test, contract, configuration, or instruction edits made.
- Evidence: seven actual CLI interactions recorded separately as JSON, including exact argument arrays, working directory, exit status, stdout, and stderr.
- Open findings: no blocking usability defect found in the observed CLI flows. Successful native explicit skill invocation and custom-role-file selection remain unverified.
- Repair decisions: no application rework requested by this review. The Manager retains final acceptance authority.
- Final disposition: D08 observed PASS for the CLI/documentation experience; full product completion remains constrained by the previously reported invocation gap.

## Actual interaction

Commands ran in `/workspace/CouncilFlow` against `demo/receipt/receipt_calculator.py`; these are executed observations, not simulated user behavior.

| Interaction | Exit | Observation | Evidence |
|---|---:|---|---|
| `python3 demo/receipt/receipt_calculator.py --help` | 0 | Shows required four-field `--item` syntax, repeatability, unit examples, decimal convention, input bounds, quoting guidance, and sample arguments. | `review/help.json` |
| `python3 demo/receipt/receipt_calculator.py --item rice 2 30000 kg --item onions 1 43000 kg` | 0 | Two understandable line calculations, Rp60,000 and Rp43,000; `Total = Rp103,000`. | `review/owner-sample.json` |
| `python3 demo/receipt/receipt_calculator.py --item "black tea" 3 12500 box --item sugar 1.5 14000 kg` | 0 | Quoted multiword name and fractional quantity work; total Rp58,500. | `review/alternative.json` |
| `python3 demo/receipt/receipt_calculator.py --item tiny 0.1 0.2 each --item free 1 0 each` | 0 | Fractional rupiah remain visible; free item is accepted; total Rp0.02. | `review/fraction.json` |
| `python3 demo/receipt/receipt_calculator.py --item rice 2 'Rp30,000' kg` | 2 | Actionable item-specific price message gives valid decimal examples and says no Rp or commas; no traceback. | `review/invalid-price.json` |
| `python3 demo/receipt/receipt_calculator.py --item rice -2 30000 kg` | 2 | Clear quantity error: zero or greater; no traceback. | `review/negative-quantity.json` |
| `python3 demo/receipt/receipt_calculator.py` | 2 | Usage and missing `--item` message direct the user to the required input. | `review/empty.json` |

## Document inspection

- `demo/README.md` leads with the finished application and a copyable command, expected output, repeated-item syntax, units, numeric limits, quoted names, test command, and importable API. The intentionally broken starter is separately identified and labelled as expected to fail.
- `README.md` explains repository installation, the exact `$council-flow` invocation pattern, native versus external Planner mode, optional custom-agent-file fallback, and preservation of existing installations.
- The README prominently reports PARTIAL status and explains that manual execution of the real-agent workflow does not prove successful skill activation. This avoids implying that a working calculator proves every product acceptance criterion.
- Role documentation distinguishes this review from Worker self-evaluation and technical testing. The Manager is the parent and retains the final decision.

The instructions were sufficient to execute the sample, a different receipt, and error cases without asking the Owner to coordinate engineering steps. The command-line interface is appropriate for the requested small offline Python program. Requiring an explicit unit in the CLI is consistent with the frozen contract and is explained in help and documentation.

## Limits

This Reviewer exercised the CLI through real subprocess invocations and inspected installation/use documentation. I did not interact with Codex's skill selector, verify a completed native `$council-flow` turn, select the custom-role files through Codex, or install globally. Those capabilities are not granted a pass by this review. Technical arithmetic coverage and network-isolated execution are independently reported by `/root/demo_tester`; this review does not replace that evidence. No score is used to waive mandatory criteria or Owner authority.
