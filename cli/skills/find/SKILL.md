---
name: find
description: Locate files by name or glob pattern using fd. Use for surface discovery before deeper analysis.
compatibility: Requires aux-skills >= 0.2.0 (pip install aux-skills), fd-find
metadata:
  version: "2.0"
  command: aux find
---

# Find Skill

Locate files matching criteria using fd (fast file finder).

## When to Use

- Surface discovery before content search
- Finding files by extension or name pattern
- Building file manifests for downstream processing

## Invocation

```bash
# Simple
aux find --root /path --glob "**/*.go" --type file

# Plan-based
aux find --plan '<json>'

# Get schema
aux find --schema
```

## Plan Schema

```json
{
  "root": "/path/to/search",
  "globs": ["**/*.go", "**/*.ts"],
  "excludes": ["vendor/**", "node_modules/**"],
  "type": "file",
  "max_depth": 5,
  "hidden": false,
  "max_results": 500
}
```

## Output

JSON with file list:

```json
{
  "summary": {"total": 150, "returned": 150},
  "results": [
    {"path": "src/main.go", "type": "file"},
    {"path": "pkg/auth/token.go", "type": "file"}
  ]
}
```
