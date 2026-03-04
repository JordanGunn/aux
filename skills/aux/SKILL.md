---
name: aux
license: MIT
description: >
  Meta-skill for agent discovery and skill routing. Returns the structured
  capability registry for all aux skills so agents can select the right skill,
  understand composition patterns, and bootstrap with no prior context.
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
    - aux
    - capabilities
    - discovery
    - routing
    - meta
    - bootstrap
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
