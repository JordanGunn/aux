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
- Run `aux usages --schema` to confirm field names before building a plan
- Declare `root` and (when scoping by type) `globs`
- Report the full result, including `summary.files_searched` and both `definitions`
  and `references` counts
- Use the scripts for all execution (never raw shell)
- Stop if schema validation fails
- Treat zero definitions and zero references as valid, reportable results
- Run usages before any rename/replace/sed that targets a symbol — this is the
  mandatory pre-flight check

## Never

The agent MUST NOT:

- Use usages to modify files (it is read-only by design)
- Pass a regex or glob pattern as `symbol` — the field is a literal string only
- Invent file paths not confirmed to exist
- Auto-widen scope without explicit user consent
- Execute shell commands directly (use scripts or aux CLI)
- Write plan artifacts to disk unless explicitly asked
- Skip the usages pre-flight check before a symbol mutation
