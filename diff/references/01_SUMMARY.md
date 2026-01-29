---
description: Identity and scope of the diff skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

diff is a single skill that performs deterministic, bounded git diff inspection.
It converts natural language intent into an explicit internal plan and emits a reproducible summary and optional patch artifacts.

## Scope

diff answers what has changed between declared git endpoints (e.g., working tree vs index, index vs HEAD) and may optionally include rename detection and whitespace normalization as explicit plan flags.
It emits a bounded summary and optional patch under `.aux/diff`.

## Constraints

Execution is deterministic for a given plan and config.
No content interpretation beyond diff surfaces, and no filesystem or git mutation is performed.
