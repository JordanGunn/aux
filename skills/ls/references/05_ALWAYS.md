---
description: Mandatory behaviors for this skill.
index:
  - Always
---

# Always

The agent MUST:

- Compile intent into a schema-valid plan before execution
- Validate dependencies before running (via `scripts/skill.sh validate`)
- Declare explicit root, depth, include_hidden, ranking, and caps
- Use stable sorting for all lists and outputs
- Report empty results with full scope context
- Respect budget caps (scan caps, top_n cap, view size cap)
- Use the scripts for all execution (never raw shell)
- Present inventories/receipts, not interpretations
- Stop if validation fails
- Treat git status as optional and explicitly enabled/disabled
