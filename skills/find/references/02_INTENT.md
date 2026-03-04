---
description: How to compile user intent into deterministic query parameters.
index:
  - When to Use
  - Compilation
  - Query Language
  - Guardrails
---

# Intent

## When to Use

Use find when the task requires structure-aware search that regex cannot reliably express:

- Find all function definitions matching a name pattern
- Locate all call sites of a specific function
- Extract all import statements
- Audit all class methods with a given signature shape
- Identify all usages of a deprecated API by AST shape

Use search for plain-text pattern matching. Use find for structure-aware matching.

## Compilation

`/find <prompt>` is treated as intent. The agent compiles it into a plan matching the CLI schema.

**Source of truth:** Run `aux find --schema` to get the current plan schema.

Check grammar availability before writing queries:
```bash
aux find --languages
```

**Example plan — find all function names in Python files:**
```json
{
  "query": "(function_definition name: (identifier) @name)",
  "root": "/path/to/src",
  "globs": ["*.py"]
}
```

**Example plan — find all imports:**
```json
{
  "query": "(import_statement name: (dotted_name) @module)",
  "root": "/path/to/src",
  "globs": ["*.py"],
  "max_matches": 100
}
```

**Example plan — explicit files:**
```json
{
  "query": "(function_definition name: (identifier) @name)",
  "files": ["/path/to/module.py", "/path/to/util.py"]
}
```

## Query Language

tree-sitter queries use S-expression syntax. Key patterns:

- `(node_type)` — match a node by type
- `(node_type field: (child_type) @capture)` — match with field + capture
- `@capture_name` — bind a node to a capture name
- `(#eq? @cap "value")` — predicate: capture must equal value
- `(#match? @cap "regex")` — predicate: capture must match regex

Run `aux find --languages` to see which grammars are installed.
Each grammar's node types are documented at https://tree-sitter.github.io/tree-sitter/

## Guardrails

- **Schema first:** Run `aux find --schema` before assuming field names.
- **Grammar check:** Run `aux find --languages` before writing a query for a new language.
- **Explicit scope:** Every plan declares `files` or `root` + globs.
- **Absence is data:** Zero matches must be reported with full plan context.
- **Ephemeral:** Do NOT write plan artifacts to disk unless explicitly asked.
- **Read-only:** find never modifies files. Use replace for mutations.
