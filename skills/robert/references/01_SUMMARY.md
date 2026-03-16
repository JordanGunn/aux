---
description: Identity and scope of the robert skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

robert is a single read-only skill that computes Robert C. Martin's package design metrics
from source files and returns per-package coupling, abstractness, distance from the main
sequence, zone classification, and natural-language interpretations.

It is named after Robert C. Martin, who formalized these metrics in *Agile Software
Development: Principles, Patterns, and Practices*. The metrics provide a computable,
shared vocabulary for design quality that replaces subjective assessment.

robert is the package-level design health primitive: `deps` answers file-level coupling,
`usages` answers symbol-level cross-reference, `robert` answers structural design quality —
where are the brittle packages, and how far is each from the ideal main sequence?

## Scope

robert answers: how stable, abstract, and well-positioned is each package relative to the
main sequence? It does not modify files. It does not infer runtime behavior or semantics.

The execution pipeline:

1. `find_kernel` (fd) — enumerate candidate files by language-specific glob
2. `deps_kernel` — extract file-level import edges (AST or text-tier)
3. `_resolve_packages` — group files into packages by language rules
4. `_aggregate_coupling` — map file edges to package-level Ca and Ce
5. `_compute_abstractness` — count Na/Nc per package (tree-sitter or regex)
6. `_build_metrics` — compute I, A, D', zone, interpretation per package

Supported languages: **Go** and **Python** only.

Language-specific package rules:
- **Go**: every directory of `.go` files is a package. `package main` directories
  are excluded by default; pass `include_main: true` to include them.
- **Python**: a directory is a package only if it contains `__init__.py`.
  Directories without `__init__.py` are skipped entirely.

## Constraints

Execution is deterministic and reproducible for a given plan JSON.
Read-only — no file writes occur under any circumstances.
`language` is required; silent misdetection would corrupt the metrics.
Tree-sitter is an enhancement, not a requirement. Without it, regex fallback runs.
Dynamic dispatch, runtime polymorphism, and duck typing are invisible to these metrics.
Metrics reflect static structure only — they are advisory, not prescriptive.
No hidden state, indexing, or semantic inference is introduced.
