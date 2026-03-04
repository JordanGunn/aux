---
description: When and why to invoke the aux meta-skill; composition patterns.
index:
  - When to Use
  - When NOT to Use
  - Composition Patterns
  - Multi-Skill Signals
---

# Intent

## When to Use

Invoke `/aux` (run `aux capabilities`) when:

1. **New agent with no prior context** — You have never used the aux suite before
   and need to understand what is available before choosing a skill.

2. **Ambiguous intent** — The user's request could map to multiple skills and you
   cannot confidently select one from memory alone.
   Example: "clean up dead code" → could be `prune` → `usages` → `replace`.

3. **Multi-skill composition planning** — You need to chain skills and want to confirm
   which skills are available and what they compose with.

4. **Lightweight existence check** — Use `aux capabilities --format names` to verify
   that a specific skill exists before constructing its plan.

## When NOT to Use

Do NOT invoke `/aux` when:

- The correct skill for the task is obvious from context. Go directly to
  `aux <skill> --schema` and then `aux <skill> --plan '<json>'`.
- You are mid-task and already know which skill to use next.
- The task is purely informational and no aux skill is needed.

**The meta-skill is a bootstrap tool, not a default interface.**
Invoking it unnecessarily adds latency with no benefit.

## Composition Patterns

Each skill's registry entry includes a `compose_with` list. These are the most common
downstream skills after the current one completes.

Common chains:

```
# Dead code removal
prune --root /path --glob "**/*.py"
  → usages <each_candidate> --root /path --glob "**/*.py"   # verify zero refs
    → replace <old> "" --root /path --glob "**/*.py" --apply  # delete

# Symbol rename
usages <old_name> --root /path --glob "**/*.py"
  → replace <old_name> <new_name> --root /path --glob "**/*.py"
    → rename <old_file> <new_file>  # if filename also changes

# Dependency-aware refactor
deps --root /path --glob "**/*.py" --target path/to/module.py
  → usages <coupled_symbol> --root /path --glob "**/*.py"
    → replace ...
```

## Multi-Skill Signals

These phrases in a user request signal that multiple skills will be needed:

- "rename X everywhere" → `usages` then `replace` (and optionally `rename`)
- "remove dead code" → `prune` then `usages` then `replace`
- "what depends on X before I delete it" → `deps` then `usages`
- "what changed and is anything broken" → `delta` then `usages`
- "find all uses of X and show me where to update" → `usages` then `replace` dry-run
