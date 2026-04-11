---
name: hotspots
license: MIT
description: >
  Churn-weighted complexity hotspots per file (Tornhill "Your Code as a Crime
  Scene", 2015). Composes `ccx` (complexity) with `git log` (change
  frequency) and ranks files by hotspot score = sum_ccx × change_freq. Files
  are classified into four quadrants — hotspot, stable_complex,
  churning_simple, calm — based on 75th-percentile cutoffs on both axes.
  Default time window is 90 days (tighter than Tornhill's canonical 1 year)
  because agentic code rot accumulates on a steeper curve than human rot.
  Read-only. Requires git. Language coverage inherits from ccx.
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
    - hotspots
    - tornhill
    - churn
    - change-coupling
    - code-quality
    - refactor-candidate
    - complexity
    - git-history
    - crime-scene
    - agentic-rot
    - architectural-rot
---

# INSTRUCTIONS

> **Do not read reference files directly.**
> Run `./scripts/skill.sh init` to load all references in a single call.

1. Run `./scripts/skill.sh init` and follow the instructions.
