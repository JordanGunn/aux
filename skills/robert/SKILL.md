---
name: robert
license: MIT
description: >
  Robert C. Martin package design metrics skill. Computes coupling (Ca/Ce/I),
  abstractness (Na/Nc/A), and distance from the main sequence (D') per package.
  Classifies packages into zones: pain, uselessness, warning, clean, ok.
  Read-only. Tree-sitter is optional — text-tier regex fallback always runs.
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
    - robert
    - martin
    - package-design
    - coupling
    - abstractness
    - instability
    - main-sequence
    - zone-of-pain
    - zone-of-uselessness
    - design-metrics
    - code-quality
    - architecture
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
