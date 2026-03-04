---
name: replace
license: MIT
description: >
  Focused fixed-string text replacement across a codebase.
  Simpler than sed: one old string, one new string, one scope.
  Designed for Haiku-tier agents — no regex, no AST, no mode selection.
metadata:
  author: Jordan Godau
  version: 0.1.0
  model_tier: haiku
  references:
    - references/01_SUMMARY.md
    - references/02_INTENT.md
    - references/03_POLICIES.md
    - references/04_PROCEDURE.md
  scripts:
    - scripts/skill.sh
    - scripts/skill.ps1
  keywords:
    - replace
    - rename
    - refactor
    - identifier
    - fixed-string
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
