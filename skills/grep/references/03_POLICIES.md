---
description: Mandatory and prohibited behaviors for this skill.
index:
  - Always
  - Never
---

# Policies

Mandatory and prohibited behaviors for this skill.

## Always

The agent MUST:

- Compile intent into a schema-valid plan before execution
- Include the parameter block in all output
- Declare explicit root, globs, excludes, and caps
- Use stable sorting for all lists
- Report empty results with full scope context
- Respect budget caps (`max_matches`)
- Use the scripts for all execution (never raw shell)
- Present evidence, not conclusions
- Stop if schema validation fails

## Never

The agent MUST NOT:

- Execute shell commands directly (use scripts)
- Invent file paths not confirmed to exist
- Assume repository structure without evidence
- Modify any files (this is a read-only skill)
- Bypass the schema validation step
- Emit results without the parameter block
- Use unbounded searches (must have caps)
- Interpret results beyond surface-level evidence
- Make claims about code behavior based on grep hits alone
- Auto-widen scope without explicit user consent
