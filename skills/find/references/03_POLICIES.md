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
- Run `aux find --schema` to confirm field names before building a plan
- Run `aux find --languages` before writing a query for an unfamiliar language
- Declare explicit file targets (`files` or `root` + globs)
- Report the full result in output, including files_searched and total_matches
- Use the scripts for all execution (never raw shell)
- Stop if schema validation fails
- Treat zero matches as a valid, reportable result — not an error

## Never

The agent MUST NOT:

- Use find to modify files (it is read-only by design)
- Substitute find for replace when writes are needed
- Invent file paths not confirmed to exist
- Auto-widen scope without explicit user consent
- Execute shell commands directly (use scripts or aux CLI)
- Write query plan artifacts to disk unless explicitly asked
- Assume a grammar is available without checking `--languages` first
