---
description: When and why to invoke the usages skill.
index:
  - When to Use
  - Compilation
  - Guardrails
---

# Intent

## When to Use

Use usages when the task requires knowing all locations where a symbol appears before
taking any action:

- Pre-flight check before renaming a symbol (replace/rename/sed)
- Impact analysis before deleting a function or class
- Verifying that a newly introduced symbol has no unexpected prior references
- Auditing usage distribution of a public API across a codebase
- Foundation for prune analysis (symbols with zero references)

Use search for arbitrary pattern matching. Use usages when the subject is a specific
named symbol and you need both definition and reference locations in one call.

## Compilation

`/usages <prompt>` is treated as intent. The agent compiles it into a plan matching
the CLI schema.

**Source of truth:** Run `aux usages --schema` to get the current plan schema.

**Example plan — find all usages of DataProcessor in Python files:**
```json
{
  "root": "/path/to/src",
  "symbol": "DataProcessor",
  "globs": ["**/*.py"]
}
```

**Example plan — usages without tree-sitter definition tagging:**
```json
{
  "root": "/path/to/src",
  "symbol": "process_batch",
  "globs": ["**/*.py"],
  "definitions": false
}
```

**Example plan — scoped to specific subdirectory:**
```json
{
  "root": "/path/to/src",
  "symbol": "UserService",
  "globs": ["**/*.ts"],
  "excludes": ["**/*.test.ts"]
}
```

## Guardrails

- **Schema first:** Run `aux usages --schema` before assuming field names.
- **Exact symbol:** `symbol` is a literal string — no regex, no wildcards.
- **Explicit scope:** Every plan declares `root` and optionally `globs`.
- **Absence is data:** Zero definitions and zero references must be reported with
  full plan context — it is a valid finding, not an error.
- **Ephemeral:** Do NOT write plan artifacts to disk unless explicitly asked.
- **Read-only:** usages never modifies files. Use replace/rename/sed for mutations.
