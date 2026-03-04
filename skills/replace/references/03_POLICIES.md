---
description: Mandatory and prohibited behaviors for this skill.
index:
  - Always
  - Never
---

# Policies

## Always

- Run Phase 1 (dry run) before Phase 2 (apply) — no exceptions
- Read the diff output and confirm the changes look correct before applying
- Use the same plan JSON in both phases — the `plan_hash` must match
- Declare an explicit scope (`root` + globs, or explicit `files`)
- Report the plan_hash when confirming Phase 2

## Never

- Apply without reviewing the dry-run diff
- Use a different plan in Phase 2 than Phase 1
- Replace when some occurrences should be skipped (do manual edits instead)
- Invent file paths — only replace in files confirmed to exist
- Use regex syntax in the `old` field — this skill is fixed-string only
