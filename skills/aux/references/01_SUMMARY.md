---
description: Identity and scope of the aux meta-skill.
index:
  - Identity
  - Skill Categories
  - Constraints
---

# Summary

## Identity

`aux` is a meta-skill. Its execution surface is `aux capabilities`, which returns a compact
JSON registry of all skills in the aux suite. It answers one question: **which skill should
I use for this task?**

It is not a general interface or an orchestrator. It is a routing index — a single read that
replaces loading 10 separate reference doc sets.

## Skill Categories

The aux suite contains 10 skills across 4 categories:

| Category | Skills | Mutates |
|----------|--------|---------|
| read     | files, search, find | No |
| write    | replace, rename | Yes |
| analysis | usages, prune, deps, delta | No |
| network  | curl | No |

**read** — Enumerate and inspect files and code structure without modification.
**write** — Mutate files on disk. Always dry-run first; apply requires explicit `--apply`.
**analysis** — Cross-reference, dead code, dependency, and change analysis. Advisory only.
**network** — HTTP fetch with agent-optimised output.

## Constraints

- `aux capabilities` is read-only and deterministic.
- The registry is a routing hint, not authoritative on field names. Always run
  `aux <skill> --schema` before constructing a plan.
- The meta-skill does not execute other skills. It only describes them.
- Do not use `/aux` as a default interface for every task. It is for bootstrap and ambiguous cases only.
