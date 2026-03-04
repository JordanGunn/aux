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
- Run `aux search --schema` to confirm field names before building a plan
- Declare explicit scope in both `surface` and `search` sub-plans
- Report the full result in output, including surface_files and matches
- Use the scripts for all execution (never raw shell)
- Stop if schema validation fails
- Treat zero matches as a valid, reportable result — not an error
- Install tree-sitter extras before using tier 3: `pip install 'aux-skills[query]'`
- **Use `result_mode: "files"` for broad discovery passes** — when the goal is routing
  (which files contain the pattern?), not content. Switch to `"matches"` or targeted
  reads only after shortlisting relevant files.

## Never

The agent MUST NOT:

- Use search to modify files (it is read-only by design)
- Invent file paths not confirmed to exist
- Auto-widen scope without explicit user consent
- Execute shell commands directly (use scripts or aux CLI)
- Skip tier-2 content pre-filtering when building a tier-3 plan — the pipeline
  always runs fd → rg → tree-sitter in order; tier 3 cannot run standalone
