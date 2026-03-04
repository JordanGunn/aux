---
name: usages
license: MIT
description: >
  Symbol cross-reference skill. Returns all definition locations and all
  reference locations for a given symbol in one structured call. Uses
  ripgrep for exhaustive text matches enriched by tree-sitter for semantic
  definition tagging.
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
    - usages
    - cross-reference
    - definitions
    - references
    - symbol
    - code-analysis
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
