---
description: Identity and scope of the ls skill.
index:
  - Identity
  - Scope
  - Constraints
---

# Summary

## Identity

ls is a single skill that performs deterministic, bounded directory state inspection.
It converts natural language intent into an explicit internal plan and executes a reproducible inventory/ranking procedure.

## Scope

ls answers what entries exist under a root, what their basic stat metadata is (type, size, mtime), and how they rank under a declared ordering.
It emits a bounded inventory and receipt under `.aux/ls` and may optionally map git working-tree status per path when enabled.

## Constraints

Execution is deterministic for a given plan and config.
No content search, semantic inference, or filesystem mutation is performed.
