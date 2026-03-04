---
description: When to invoke search and how to build the plan.
index:
  - When to Use
  - Tier Selection
  - Compilation
  - Plan Structure
  - Guardrails
---

# Intent

## When to Use

Use search when:
- You need to find files containing a specific text pattern (tiers 1+2)
- You want to scope the search to a subset of files (by glob or type)
- You want a single command that combines file discovery + content search
- You need to further filter content matches to specific AST constructs (tier 3)

Use `files` alone when you only need file paths (no content search).
Use `find` when you need standalone AST-aware structural search (no content pre-filter).

## Tier Selection

| Goal | Tiers | structure field |
|------|-------|-----------------|
| Find files with pattern X | 1+2 | omit |
| Find AST nodes in files containing pattern X | 1+2+3 | set |

Tier 3 narrows the tier-2 result set — only files that had content matches are passed to
tree-sitter. This is the correct model when you want structural results that are guaranteed
to be co-located with a text pattern.

## Compilation

`/search <prompt>` is treated as intent. The agent compiles it into a SearchPlan
matching the CLI schema.

**Source of truth:** Run `aux search --schema` to get the current plan schema.

## Plan Structure

### Two-tier plan (fd → rg)

```json
{
  "root": "/path/to/search",
  "surface": {
    "root": "/path/to/search",
    "globs": ["*.py"],
    "excludes": ["**/test_*.py"],
    "type": "file"
  },
  "search": {
    "root": "/path/to/search",
    "patterns": [{"kind": "regex", "value": "TODO|FIXME"}],
    "case": "smart"
  }
}
```

- `surface` — controls which files are included (FilesPlan schema)
- `search` — controls what patterns to find in those files (GrepPlan schema)

### Three-tier plan (fd → rg → tree-sitter)

```json
{
  "root": "/path/to/search",
  "surface": {
    "root": "/path/to/search",
    "globs": ["*.py"],
    "type": "file"
  },
  "search": {
    "root": "/path/to/search",
    "patterns": [{"kind": "fixed", "value": "def "}]
  },
  "structure": {
    "query": "(function_definition name: (identifier) @fn)",
    "language": "python",
    "max_matches": 50
  }
}
```

- `structure.query` — tree-sitter S-expression query string
- `structure.language` — language override (auto-detected from extension if omitted)
- `structure.max_matches` — cap on total AST matches (optional)

## Result Mode

| Mode | Output | Use when |
|------|--------|----------|
| `"matches"` (default) | One entry per matched line | You need line-level content |
| `"files"` | One entry per matched file (`{file, matches}`) | Broad discovery pass — routing to relevant files |

Run a `"files"` scan first to identify which files contain your pattern, then run a
targeted `"matches"` scan (or targeted reads) on the shortlisted files. This can reduce
search result token cost by 90%+ on broad patterns.

## Guardrails

- **Schema first:** Run `aux search --schema` before assuming field names.
- **Explicit scope:** Declare `root`, globs, and excludes in both surface and search.
- **Absence is data:** Zero matches must be reported with full plan context.
- **Read-only:** search never modifies files.
- **Tier 3 requires tree-sitter:** Install with `pip install 'aux-skills[query]'`.
