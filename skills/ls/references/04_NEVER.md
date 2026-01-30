---
description: Absolute prohibitions for this skill.
index:
  - Never
---

# Never

The agent MUST NOT:

- Execute shell commands directly (all execution goes through scripts)
- Invent file paths or directories not confirmed to exist
- Assume repository structure without evidence
- Modify any files (this is a read-only skill)
- Bypass the schema/config validation step
- Emit inventories without the plan/config parameter block
- Use unbounded enumerations (must always have caps)
- Read file contents (this skill only inspects filesystem metadata)
- Make claims about file contents based on names alone
- Auto-widen scope without explicit user consent
- Pretend to implement gitignore behavior without using git
- Emit per-entry git status fields unless git mapping is enabled and successful
