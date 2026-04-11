---
description: Explicit prohibitions and mandates for the delta skill.
index:
  - Prohibitions
  - Mandates
  - Degradation chain
---

# Policies

## Prohibitions

delta MUST NOT:
- Write to any file under any circumstances
- Run `git checkout`, `git reset`, or any mutating git commands
- Perform runtime tracing or behavioral analysis
- Cache or persist state between invocations
- Interpret symbol changes as semantic equivalence (e.g., "same function, renamed")

## Mandates

delta MUST:
- Return the same output for the same plan JSON against the same git state (determinism)
- Check git availability at runtime and return a structured error if absent
- Fall back to stat-only mode automatically if tree-sitter is unavailable (warn in errors)
- Include all errors in the `errors` field — never silently swallow git command failures
- Report `truncated: true` when max_files cap is applied
- Use working tree content (Path.read_text) when ref_to is None (working tree mode)

## Modes

delta supports two modes, both gated on git being available:

1. **Full semantic mode** (default, requires git):
   - File list + line stats + symbol diff (added/removed/unchanged)
   - Tree-sitter is a bundled core dependency, so this mode always runs unless
     the caller explicitly opts out.

2. **Stat-only mode** (`stat_only=true`):
   - File list + line stats only; symbols=null per file
   - Use when only file-level churn matters and symbol analysis would be wasted work.

3. **Error mode** (git unavailable):
   - Return empty DeltaResult with error: "git not found"

## Symbol diff semantics

Symbol comparison is by (name, type) tuple:
- "added" = present in ref_to, absent in ref_from
- "removed" = present in ref_from, absent in ref_to
- "unchanged" = present in both

Signature changes (same name, different parameters) appear as "unchanged".
This is intentionally conservative — it avoids false positives on parameter edits.
