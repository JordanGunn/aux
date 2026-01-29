---
description: Mandatory behaviors for this skill.
index:
  - Always
---

# Always

The agent MUST:

- Compile intent into a schema-valid discovery plan and execution plan before running
- Validate assets/config fail-closed before running (via `scripts/skill.sh validate`)
- Declare explicit surface/root/scope/mode and caps (max files/lines/bytes)
- Use stable ordering for all enumerations and outputs
- Report clean/empty results with full scope context
- Respect budget caps and surface truncation explicitly in receipts/summaries
- Use the scripts for all execution (never raw shell)
- Present emitted artifacts (summary/receipts/patch) rather than interpretations
- Stop if validation fails
- Treat patch emission as optional and explicit (only when requested)
- Treat rename detection and normalization as explicit plan flags
