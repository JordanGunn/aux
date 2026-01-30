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
- Declare explicit paths, context, and caps
- Use stable ordering for all enumerations and outputs
- Report clean/empty results with full scope context
- Respect budget caps and surface truncation explicitly
- Use the scripts for all execution (never raw shell)
- Present emitted artifacts rather than interpretations
- Stop if validation fails

## Never

The agent MUST NOT:

- Execute shell commands directly (use scripts)
- Modify any files or repository state (read-only)
- Bypass schema validation or fail-open on errors
- Invent implicit defaults (must be explicit in plan)
- Use unbounded diffing (must have caps)
- Read file contents directly (use diff tool output)
- Auto-widen scope without explicit user consent
- Make claims about changes not supported by artifacts
