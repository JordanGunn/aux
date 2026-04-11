# aux (capabilities)

> **Agent bootstrap and skill routing meta-skill**

## Overview

The `aux capabilities` command returns a compact JSON registry of all skills in the aux
suite. It is designed for agent bootstrap: run it once to understand what is available,
then fetch `--schema` for the selected skill before constructing a plan.

It is not a general interface or an orchestrator. It is a routing index that replaces
loading 10 separate reference doc sets.

## When to Use

- You have no prior context about which skill to use for a task
- The user's request is ambiguous and could map to multiple skills
- You need to plan a multi-skill composition and want to see `compose_with` hints
- Quick existence check: `aux capabilities --format names`

**Do not use `aux capabilities` before every task.** When the correct skill is obvious
from context, go directly to `aux <skill> --schema`.

## Usage

### Full registry
```bash
aux capabilities
```

### Skill names only (lightweight)
```bash
aux capabilities --format names
```

## Output

```json
{
  "version": "0.2.0",
  "skills": [
    {
      "name": "usages",
      "description": "Symbol cross-reference: all definitions and all references in one call.",
      "category": "analysis",
      "intent_signals": [
        "find all references to a symbol",
        "check impact before renaming a function or class",
        "locate where a symbol is defined across a codebase"
      ],
      "requires": ["root", "symbol"],
      "optional_deps": [],
      "compose_with": ["replace", "rename"],
      "mutates": false,
      "schema_cmd": "aux usages --schema"
    }
  ],
  "composition_note": "Fetch --schema for each selected skill before constructing a plan. ..."
}
```

## Skill Categories

| Category | Skills | Mutates |
|----------|--------|---------|
| read     | files, search, find | No |
| write    | replace, rename | Yes |
| analysis | usages, prune, deps, delta | No |
| network  | curl | No |

## Canonical Flow

```
1. aux capabilities              → select skill(s)
2. aux <skill> --schema          → get field names
3. aux <skill> --plan '<json>'   → execute
   (write skills: dry-run first, then --apply)
```

## Common Composition Chains

```bash
# Dead code removal
aux prune --root /path --glob "**/*.py"
aux usages <candidate> --root /path --glob "**/*.py"
aux replace <dead> "" --root /path --glob "**/*.py" --apply

# Symbol rename
aux usages OldName --root /path --glob "**/*.py"
aux replace OldName NewName --root /path --glob "**/*.py"

# Dependency-aware refactor
aux deps --root /path --glob "**/*.py" --target module.py
aux usages <coupled_symbol> --root /path --glob "**/*.py"
```
