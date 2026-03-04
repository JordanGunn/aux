---
description: Canonical execution path for this skill.
index:
  - Steps
  - CLI reference
  - Output Format
---

# Procedure

## Steps

**1. Get the schema**
```bash
bash scripts/skill.sh schema
```

**2. Build the plan JSON**

Construct a SearchPlan with `root`, `surface` (file discovery), and `search` (content
match). Add `structure` only when AST-level filtering is required.

**3. Execute**
```bash
echo '<plan_json>' | bash scripts/skill.sh run --stdin
```

Read the output:
- `summary.surface_files` — how many files were in scope after tier 1
- `summary.matches` — how many matches were found (content or AST)
- `results` — each match with file, line, content, pattern (2-tier) or
  file, language, line, col, capture, text (3-tier)

**4. Refine if needed**

If too many results, narrow the surface globs or add excludes.
If zero results, verify the pattern and surface scope.
If tier-3 returns no matches, verify the tree-sitter query with `aux find --schema`.

---

## CLI reference

```bash
# Plan mode (stdin) — only mode supported
echo '<plan_json>' | bash scripts/skill.sh run --stdin

# Schema
bash scripts/skill.sh schema
```

**Example plan — find Python files containing TODO (2-tier):**

```json
{
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
    "case": "smart",
    "context_lines": 1
  }
}
```

**Example plan — find function definitions in files containing `def ` (3-tier):**

```json
{
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
}
```

**Validate:**
```bash
bash scripts/skill.sh validate
```

---

## Output Format

### Two-tier (structure omitted)

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

### Two-tier, files mode (`result_mode: "files"`)

```json
{
  "summary": {
    "surface_files": 1449,
    "files_with_matches": 42,
    "matches": 312,
    "patterns": ["auth"]
  },
  "results": [
    {"file": "/abs/path/middleware/auth.go", "matches": 18},
    {"file": "/abs/path/oidc/client.go", "matches": 7}
  ]
}
```

### Three-tier (structure set)

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

Each result in the three-tier output is one flattened `AstCapture`:
- `file` — absolute path to the file
- `language` — detected language
- `line` — 1-based line number of the captured node
- `col` — 0-based column offset
- `capture` — capture name from the query (e.g. `"fn"`)
- `text` — matched source text of the captured node
