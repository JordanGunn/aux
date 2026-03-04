---
name: delta
license: MIT
description: >
  Semantic git diff skill. Surfaces what has changed since a git ref —
  files modified, line counts, and symbols added/removed (requires tree-sitter).
  Attacks accumulated session drift: shows exactly what changed and what
  symbol-level API surface was affected. Read-only.
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
    - delta
    - git-diff
    - semantic-diff
    - symbols
    - changes
    - drift
    - code-analysis
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
