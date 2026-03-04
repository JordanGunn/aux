# search

Hierarchical file-discovery + content-search + optional AST-structure pipeline.
Progressively narrows a file set through up to three tiers and returns matched results
without modifying any files.

## Overview

`search` runs up to three kernels in sequence, passing results in-memory:

| Tier | Tool | Kernel | Purpose | Required |
|------|------|--------|---------|----------|
| 1 | fd | `find_kernel` | Name/glob/type surface reduction → file list | yes |
| 2 | rg | `grep_kernel` | Content pattern match across tier-1 files | yes |
| 3 | tree-sitter | `query_kernel` | AST structural match across tier-2 files | no |

**Key properties:**
- Read-only — no filesystem writes under any circumstances
- Deterministic — same plan JSON produces same output
- In-memory pipeline — no intermediate files, no shell pipelines
- Tier 3 is optional — omit `structure` for a two-tier fd+rg pipeline

## Prerequisites

```bash
# For tier 1+2 only (default):
aux doctor   # verify fd + rg are available

# For tier 3 (tree-sitter):
pip install 'aux-skills[query]'
```

## Usage

### Two-tier plan (fd → rg)

```bash
aux search --plan '{
  "root": "/path/to/repo",
  "surface": {
    "root": "/path/to/repo",
    "globs": ["*.py"],
    "excludes": ["**/vendor/**"],
    "type": "file"
  },
  "search": {
    "root": "/path/to/repo",
    "patterns": [{"kind": "regex", "value": "TODO|FIXME"}],
    "case": "smart"
  }
}'
```

### Three-tier plan (fd → rg → tree-sitter)

```bash
aux search --plan '{
  "root": "/path/to/repo",
  "surface": {
    "root": "/path/to/repo",
    "globs": ["*.py"],
    "type": "file"
  },
  "search": {
    "root": "/path/to/repo",
    "patterns": [{"kind": "fixed", "value": "def "}]
  },
  "structure": {
    "query": "(function_definition name: (identifier) @fn)",
    "language": "python",
    "max_matches": 100
  }
}'
```

### Schema

```bash
aux search --schema
```

## Plan Schema

```json
{
  "root": "/path/to/repo",
  "surface": {
    "root": "/path/to/repo",
    "globs": ["*.py"],
    "excludes": [],
    "type": "file",
    "max_depth": null,
    "hidden": false,
    "no_ignore": false,
    "max_results": null
  },
  "search": {
    "root": "/path/to/repo",
    "patterns": [{"kind": "regex", "value": "pattern"}],
    "globs": [],
    "excludes": [],
    "mode": "regex",
    "case": "smart",
    "context_lines": 0,
    "hidden": false,
    "no_ignore": false,
    "max_matches": null
  },
  "structure": null,
  "result_mode": "matches"
}
```

### `structure` field (tier 3)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Tree-sitter query string |
| `language` | string | no | Language override (auto-detected from extension if null) |
| `max_matches` | int | no | Maximum total AST matches |

## Output Format

### Two-tier output — `result_mode: "matches"` (default)

```json
{
  "summary": {
    "surface_files": 42,
    "matches": 7,
    "files_with_matches": 3,
    "patterns": 1
  },
  "results": [
    {
      "file": "/abs/path/module.py",
      "line": 23,
      "content": "  # TODO: refactor this",
      "pattern": "TODO|FIXME"
    }
  ]
}
```

### Two-tier output — `result_mode: "files"`

One entry per matching file, sorted by match count descending. Use for broad routing
passes where per-line content is not needed.

```json
{
  "summary": {
    "surface_files": 42,
    "files_with_matches": 3,
    "matches": 7,
    "patterns": ["TODO|FIXME"]
  },
  "results": [
    {"file": "/abs/path/heavy.py", "matches": 5},
    {"file": "/abs/path/other.py", "matches": 2}
  ]
}
```

When `max_matches` fires and results are incomplete, the summary gains a
`"truncated": true` field (present only when truncation occurred).
```

### Three-tier output (structure set)

```json
{
  "summary": {
    "tiers": ["fd", "rg", "tree-sitter"],
    "surface_files": 42,
    "content_files": 7,
    "matches": 3,
    "files_with_matches": 2
  },
  "results": [
    {
      "file": "/abs/path/module.py",
      "language": "python",
      "line": 5,
      "col": 0,
      "capture": "fn",
      "text": "my_func"
    }
  ]
}
```

Each three-tier result entry is one flattened AST capture:
- `file` — absolute path
- `language` — detected or overridden language
- `line` — 1-based line number of the captured node
- `col` — 0-based column offset
- `capture` — capture name from the query (e.g. `"fn"`)
- `text` — matched source text of the captured node

## Skill Interface

```bash
# Init (agent onboarding)
./skills/search/scripts/skill.sh init

# Validate (dependency check)
./skills/search/scripts/skill.sh validate

# Schema
./skills/search/scripts/skill.sh schema

# Run (plan via stdin)
echo '<plan_json>' | ./skills/search/scripts/skill.sh run --stdin
```
