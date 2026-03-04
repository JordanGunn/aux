---
description: Identity and scope of the usages skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

usages is a single read-only skill that returns all definition locations and all reference
locations for a named symbol in one deterministic, structured call.
It eliminates the manual grep-before-mutate pre-flight pattern required by write skills
(rename, replace, sed).

## Scope

usages answers: where is this symbol defined, and where is it referenced?
It does not modify files. It does not infer behavior, architecture, or semantics.
It is the O(1) cross-reference primitive that write skills use for impact analysis.

The execution pipeline:
1. `find_kernel` (fd) — enumerate candidate files by glob
2. `grep_kernel` (rg, fixed-string) — exhaustive text matches (all refs + defs)
3. `query_kernel` (tree-sitter, optional) — definition tagging with symbol_type
4. Correlation — grep matches enriched with definition metadata from AST

Supported definition languages (requires tree-sitter grammars): Python, JavaScript,
TypeScript, Go, Rust, Java.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
Read-only — no file writes occur under any circumstances.
Tree-sitter is an enhancement, not a requirement. Without it, all matches are tagged
"reference" — the result is still complete.
No hidden state, indexing, or semantic inference is introduced.
