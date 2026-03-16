---
description: Explicit prohibitions and mandates for the robert skill.
index:
  - Prohibitions
  - Mandates
  - Scope limits
---

# Policies

## Prohibitions

robert MUST NOT:
- Write to any file under any circumstances
- Infer package identity from runtime behavior or dynamic dispatch
- Silently auto-detect language (language is always required)
- Count self-loops in Ca or Ce (a package importing itself is excluded)
- Emit metrics for packages that fail language-specific resolution rules
  (Go: no .go files in dir; Python: no `__init__.py`)
- Cache or persist state between invocations
- Treat external stdlib or third-party packages as internal graph nodes
  (they appear in file-level imports but do not contribute to Ca/Ce)

## Mandates

robert MUST:
- Return the same output for the same plan JSON (determinism)
- Fall back to text-tier regex when tree-sitter is unavailable
- Sort `packages` output by distance (D') descending — worst first
- Include `zone` as a machine-readable field on every package entry
- Include `interpretation` as a human-readable verdict on every package entry
- Include `guidance` in summary for every package with zone pain/uselessness/warning
- Include all errors encountered in the `errors` field (never silently swallow)
- Report `truncated: true` when max_results cap is applied
- Require `language` — do not guess or auto-detect

## Scope limits

Package resolution is intentionally strict:
- Go: `package main` directories excluded by default (`include_main: false`)
- Python: directories without `__init__.py` are skipped entirely
- External packages (stdlib, third-party) are not resolved to package nodes
- Only files discovered by `find_kernel` within `root` participate in the graph

These constraints prevent false zone assignments and keep metrics tractable.

Interpretation of metrics is advisory:
- A Zone of Pain classification does not mandate refactoring — it surfaces
  a design tension for human judgment
- Dynamic languages may legitimately violate static metrics (duck typing,
  runtime injection) — always note this caveat when reporting to users
