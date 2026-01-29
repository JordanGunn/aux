---
description: When this skill activates.
index:
  - Activation
  - Examples
---

# Triggers

## Activation

diff activates when the user invokes `/diff` followed by a natural language prompt describing what changes they want summarized.

## Examples

- `/diff show what changed in the working tree`
- `/diff summarize staged changes only`
- `/diff show changes to src/ with rename detection`
- `/diff produce a bounded unified patch for the last commit`

The prompt is treated as intent. The agent compiles it into an explicit, bounded plan.
