---
description: Identity and scope of the delta skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

delta is a single read-only skill that surfaces what has semantically changed since a
git ref. It combines git's line-level diff stats with tree-sitter symbol extraction to
produce a structured account of: which files changed, how many lines, and which symbols
(functions, classes, types) were added or removed.

It directly attacks the accumulated session drift problem: after a sequence of edits,
agents can call delta to know exactly what changed and what API surface was affected.

## Scope

delta answers: what changed since ref X, at both the file level and the symbol level?
It does not modify files. It does not analyze behavior or semantics beyond symbol presence.

The execution pipeline:
1. `git diff --name-status` — list changed files with status (M/A/D/R)
2. `git diff --numstat` — line addition/deletion counts per file
3. For each changed file (semantic mode):
   - `git show <ref_from>:<path>` — old content
   - Working tree read or `git show <ref_to>:<path>` — new content
   - tree-sitter symbol extraction on both versions → symbol diff

Supported languages for symbol diff (requires tree-sitter): Python, JavaScript,
TypeScript, Go, Rust, Java.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
Read-only — no file writes occur under any circumstances.
Git must be available; if absent, an error is returned immediately.
Tree-sitter is optional — without it, stat-only mode runs automatically.
Symbol diff semantics are conservative: only name+type presence is compared.
A function renamed (same body) appears as one removed + one added symbol.
