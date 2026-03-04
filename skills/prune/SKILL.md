---
name: prune
license: MIT
description: >
  Tiered dead code candidate audit. Enumerates symbols and modules with zero
  detected external references and emits advisory output for human verification.
  Never acts autonomously — all candidates require deeper-dive investigation
  via `aux usages` before any action is taken.
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
    - prune
    - dead-code
    - audit
    - static-analysis
    - code-quality
    - refactoring
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
