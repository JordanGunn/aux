---
description: Absolute prohibitions for this skill.
index:
  - Never
---

# Never

The agent MUST NOT:

- Execute shell commands directly (all execution goes through scripts)
- Modify any files or repository state (read-only)
- Proceed with run phase if git is missing or the directory is not a git repo
- Bypass schema validation or fail-open on validation errors
- Invent implicit defaults for scope, bounds, or normalization (must be explicit in the plan)
- Use unbounded diffing (must always have caps)
- Emit `diff.patch` unless explicitly requested by the plan
- Claim a snapshot surface is supported (v1 is git-only)
- Infer renames; rename detection must come from the diff tool output and be surfaced explicitly
- Read file contents directly from disk for analysis (diff content must come from the diff tool output)
- Auto-widen scope without explicit user consent
- Make claims about changes not supported by emitted artifacts
