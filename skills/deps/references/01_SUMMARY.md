---
description: Identity and scope of the deps skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

deps is a single read-only skill that builds a module dependency graph from source files
and returns per-file coupling metrics, the full import/imported-by topology, and any
detected import cycles.

It is the module-level topology primitive: `usages` answers symbol-level cross-reference,
`prune` answers reference-counting, `deps` answers the structural coupling question —
who depends on whom, and where are the cycles?

## Scope

deps answers: what does this module import, who imports it, how coupled is it, and is it
in a cycle? It does not modify files. It does not infer behavior or semantics.

The execution pipeline:
1. `find_kernel` (fd) — enumerate candidate files by glob
2. Import extraction:
   - AST tier (tree-sitter, optional) — language-specific import queries
   - Text tier (fallback) — per-language regex on raw file content
3. Module → file resolution — best-effort stem match within scanned set
4. Graph construction — adjacency dict, afferent/efferent counts, instability
5. Cycle detection — DFS over resolved graph

Supported languages (AST tier): Python, JavaScript, TypeScript, Go, Java.
Supported languages (text tier): Python, JavaScript, TypeScript, Go, Rust, Java.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
Read-only — no file writes occur under any circumstances.
Module resolution is best-effort: external packages and stdlib are recorded as import
strings but do not participate in graph edges or cycle detection.
Tree-sitter is an enhancement, not a requirement. Without it, text-tier regex always runs.
No hidden state, indexing, or semantic inference is introduced.
