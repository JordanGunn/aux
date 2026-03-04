---
description: Explicit prohibitions and mandates for the deps skill.
index:
  - Prohibitions
  - Mandates
  - Scope limits
---

# Policies

## Prohibitions

deps MUST NOT:
- Write to any file under any circumstances
- Resolve modules outside the scanned file set (no package index lookups)
- Emit false cycle reports across package boundaries
- Perform semantic analysis (type inference, runtime tracing)
- Cache or persist state between invocations

## Mandates

deps MUST:
- Return the same output for the same plan JSON (determinism)
- Fall back to text-tier regex when tree-sitter is unavailable
- Sort FileDeps output by afferent coupling descending
- Include all errors encountered in the `errors` field (never silently swallow)
- Report `truncated: true` when max_results cap is applied
- Resolve module strings best-effort only — unresolved modules remain as import
  strings in `imports` but are excluded from graph edges and cycle detection

## Scope limits

Module resolution is intentionally limited to the scanned file set:
- External packages (e.g., `requests`, `numpy`) appear in `imports` as strings only
- Standard library modules appear in `imports` as strings only
- Only files discovered by `find_kernel` within `root` participate in the graph

This constraint is load-bearing: it prevents false cycle reports and keeps the output
tractable for large codebases.
