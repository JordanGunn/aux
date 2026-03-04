---
description: When and why to invoke prune, and how to compile intent into a plan.
index:
  - When to Use
  - When NOT to Use
  - Compilation
  - Confidence Interpretation
---

# Intent

## When to Use

Use prune when:
- A refactor or cleanup effort needs a starting point — "what might be unused?"
- A codebase has grown organically and symbol rot is suspected
- A merge or deprecation cycle needs a quick surface scan before deeper investigation
- The user asks for dead code candidates or unreferenced symbols

## When NOT to Use

Do NOT use prune as a substitute for reading the code. Do NOT use prune output to drive deletions
without running `aux usages` per candidate. Do NOT present prune candidates as confirmed dead code.

For single-symbol cross-referencing, use `aux usages` directly.

## Compilation

`/prune <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux prune --schema` to get the current plan schema.

**Example plan — symbol-scope audit of Python files:**
```json
{
  "root": "/path/to/src",
  "globs": ["**/*.py"],
  "scope": ["symbols"]
}
```

**Example plan — file-scope audit (no tree-sitter required):**
```json
{
  "root": "/path/to/src",
  "globs": ["**/*.py"],
  "scope": ["files"]
}
```

**Example plan — combined scope, widen threshold:**
```json
{
  "root": "/path/to/src",
  "globs": ["**/*.py", "**/*.ts"],
  "scope": ["symbols", "files"],
  "max_refs": 1
}
```

**Example plan — performance-capped symbols scan:**
```json
{
  "root": "/path/to/large/codebase",
  "globs": ["**/*.py"],
  "scope": ["symbols"],
  "max_symbols": 200
}
```

## Confidence Interpretation

Each candidate carries a `confidence` rating (`high`, `medium`, `low`) and a `caveats` list.

| Confidence | Meaning |
|------------|---------|
| `high`     | Long, unique-looking name with no external refs. Still requires `aux usages` verification. |
| `medium`   | Moderate name length or dynamic language. Check with `aux usages` before forming conclusions. |
| `low`      | Short name, common identifier, dunder method, or highly dynamic language. Treat as informational only — do not act. |

`caveats` lists specific reasons confidence is reduced: short name, common identifier, dynamic
language risk, dunder method. Read these before deciding whether to investigate further.
