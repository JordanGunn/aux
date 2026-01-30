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
- Include the parameter block in all output
- Declare explicit root, patterns, excludes, type, and caps
- Use stable sorting for all lists
- Report empty results with full scope context
- Respect budget caps (`max_results`, `max_depth`)
- Use the scripts for all execution (never raw shell)
- Present file lists, not interpretations
- Stop if schema validation fails

## Never

The agent MUST NOT:

- Execute shell commands directly (use scripts)
- Invent file paths not confirmed to exist
- Assume repository structure without evidence
- Modify any files (this is a read-only skill)
- Bypass the schema validation step
- Emit file lists without the parameter block
- Use unbounded enumerations (must have caps)
- Read file contents (this skill only lists paths)
- Make claims about file contents based on names alone
- Auto-widen scope without explicit user consent
