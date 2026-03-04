---
description: Mandatory and prohibited behaviors for this skill.
index:
  - Always
  - Never
---

# Policies

## Always

- Run Phase 1 (dry-run) before Phase 2 (apply) — no exceptions
- Read the preview output and confirm all moves look correct before applying
- Use the same plan JSON in both phases — the `plan_hash` must match
- Report the plan_hash when confirming Phase 2
- Use `backup: true` when renaming directories — directory moves are harder to undo
- Check `dst.parent` exists before constructing the plan — parent creation is out of scope

## Never

- Apply without reviewing the dry-run preview
- Use a different plan in Phase 2 than Phase 1
- Construct dst paths that require new parent directories
- Assume `overwrite: true` is safe without confirming the destination is disposable
- Use rename for file copy operations (rename moves, not copies)
