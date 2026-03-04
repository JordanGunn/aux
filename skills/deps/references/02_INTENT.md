---
description: When and why to invoke the deps skill.
index:
  - Primary use cases
  - When NOT to use deps
  - Prerequisite signals
---

# Intent

## Primary use cases

deps is the correct skill when any of these questions must be answered:

1. **Blast radius analysis** — before renaming or deleting a module, determine every
   file that imports it (afferent coupling). High afferent count = high blast radius.

2. **Coupling audit** — identify the most-coupled modules (sorted by afferent desc)
   to prioritize refactoring effort.

3. **Cycle detection** — find import cycles that create initialization ordering issues,
   circular dependencies, or tight coupling that resists extraction.

4. **Instability metric** — compute Ce / (Ca + Ce) per file. Instability near 1.0
   means a module is heavily dependent on others but rarely imported (highly volatile).
   Instability near 0.0 means a module is widely used but changes little (stable).

5. **Target mode** — given a single file, show exactly what it imports and who imports it.
   This is the O(1) pre-flight check before any modification to that file.

## When NOT to use deps

- When you need symbol-level cross-reference → use `usages` instead
- When you need dead code candidates → use `prune` instead
- When you need to search file content → use `search` or `find` instead
- When you need git change history → use `delta` instead

## Prerequisite signals

Run deps when:
- You are about to rename or delete a module and need impact scope
- You are planning an extract-refactor and need to understand coupling
- You see import errors and suspect circular imports
- An audit or architecture review requires coupling metrics
