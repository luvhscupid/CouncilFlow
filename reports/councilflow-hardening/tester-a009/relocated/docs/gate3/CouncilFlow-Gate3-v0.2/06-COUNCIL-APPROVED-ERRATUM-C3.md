# Council-approved erratum C3 — Gate 3 E4

This erratum is approved by Council Round 6 and controls E4 wording for the
Gate 3b run. The frozen v0.2 source specification and all historical
observations remain preserved unchanged. This erratum changes only E4.

## E4 — Custom-agent loading

**PASS:** Host-observed configuration identity or agent type confirms that the
intended `council-*` custom-agent definitions were loaded for their corresponding
role sessions.

**FAIL:** Host evidence affirmatively demonstrates that a different or default
agent configuration was used instead.

**UNVERIFIED:** The host exposes only cosmetic thread labels or insufficient
information to identify the actual loaded custom-agent definition.

This check makes no claim about model or sandbox settings that the TOML files do
not define. A displayed role name alone does not prove that the corresponding
TOML file was loaded. Do not hardcode unsupported model or sandbox settings to
make E4 pass. Do not alter agent settings beyond the approved Reviewer and Tester
instruction corrections.
