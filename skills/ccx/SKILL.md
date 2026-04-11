---
name: ccx
license: MIT
description: >
  Cyclomatic Complexity (McCabe 1976) and Cognitive Complexity (Campbell 2018)
  per function across a codebase, computed in a single tree-sitter AST
  traversal per file. Language-agnostic — supports Python, JavaScript,
  TypeScript, Go, Rust, and Java on day one. Classifies functions into zones:
  simple, moderate, complex, untestable. Read-only. No regex text-tier
  fallback — files that fail to parse are reported as errors and skipped.
metadata:
  author: Jordan Godau
  version: 0.1.0
  references:
    - references/01_SUMMARY.md
    - references/02_INTENT.md
    - references/03_POLICIES.md
    - references/04_PROCEDURE.md
  scripts:
    - scripts/skill.sh
    - scripts/skill.ps1
  keywords:
    - ccx
    - mccabe
    - campbell
    - cyclomatic
    - cognitive
    - complexity
    - function-metrics
    - method-metrics
    - code-quality
    - refactor-candidate
    - testability
    - zone-of-pain
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
