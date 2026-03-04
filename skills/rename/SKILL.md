---
name: rename
license: MIT
description: >
  Move or rename files and directories with a dry-run gate.
  Single-call filesystem rename that avoids read-write-delete token waste.
  Batch-capable via plan mode.
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
    - rename
    - move
    - mv
    - filesystem
    - refactor
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
