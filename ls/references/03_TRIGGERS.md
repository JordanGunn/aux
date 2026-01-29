---
description: When this skill activates.
index:
  - Activation
  - Examples
---

# Triggers

## Activation

This skill activates when the user invokes `/ls` followed by a natural language prompt describing what directory state they want summarized or ranked.

## Examples

- `/ls show the most recently modified files under src`
- `/ls list the largest files in the repo root`
- `/ls show directories with most recent changes`
- `/ls show files changed according to git status`

The prompt is treated as intent. The agent compiles it into an explicit, bounded plan.
