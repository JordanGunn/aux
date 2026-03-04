---
description: Identity and scope of the search skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

search is a three-tier hierarchical pipeline skill:

| Tier | Tool | Purpose |
|------|------|---------|
| 1 | fd | Surface reduction — enumerate files by name/glob |
| 2 | rg | Content match — grep patterns across tier-1 files |
| 3 | tree-sitter | Structure match — AST query across tier-2 files (optional) |

All three kernels pass results in-memory; no intermediate files, no shell pipelines.
Tier 3 is optional. When omitted, search returns content matches from tiers 1 and 2.

## Scope

search answers: which files (and optionally which AST nodes within those files) match
a layered set of name, content, and structural criteria?

It is more efficient than chaining tools separately because the file list narrows
progressively in-process at each tier.

search does NOT:
- Read or interpret file semantics beyond pattern/AST matching
- Modify files (read-only)
- Index or cache results between invocations

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
All criteria (surface + search + structure) are visible in the single invocation.
No hidden state, indexing, or semantic inference is introduced.
Read-only — no file writes occur under any circumstances.
Supports `result_mode: "files"` for token-efficient broad routing (one entry per file,
sorted by match count) or `"matches"` (default) for per-line content results.
