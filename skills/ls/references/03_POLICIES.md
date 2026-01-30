---
description: Mandatory and prohibited behaviors for this skill.
index:
  - Always
  - Never
---

# Policies

## Always

The agent MUST:

- Compile intent into a schema-valid plan before execution
- Validate dependencies before running (via `scripts/skill.sh validate`)
- Declare explicit root, depth, include_hidden, ranking, and caps
- Use stable sorting for all lists and outputs
- Report empty results with full scope context
- Respect budget caps (scan caps, top_n cap)
- Use the scripts for all execution (never raw shell)
- Present inventories, not interpretations
- Stop if validation fails
- Treat git status as optional and explicitly enabled/disabled

## Never

The agent MUST NOT:

- Execute shell commands directly (use scripts)
- Invent file paths not confirmed to exist
- Assume repository structure without evidence
- Modify any files (this is a read-only skill)
- Bypass the schema validation step
- Emit inventories without the parameter block
- Use unbounded enumerations (must have caps)
- Read file contents (this skill only inspects metadata)
- Make claims about file contents based on names alone
- Auto-widen scope without explicit user consent
