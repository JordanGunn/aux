---
name: ls
description: List directory contents with metadata (size, type, time). Use for understanding directory structure.
compatibility: Requires aux-skills >= 0.2.0 (pip install aux-skills)
metadata:
  version: "2.0"
  command: aux ls
---

# Ls Skill

List directory contents with optional metadata.

## When to Use

- Understanding directory structure
- Finding large files
- Exploring unfamiliar codebases

## Invocation

```bash
# Simple
aux ls /path --depth 2 --sort size

# Plan-based
aux ls --plan '<json>'

# Get schema
aux ls --schema
```

## Plan Schema

```json
{
  "path": "/path/to/list",
  "depth": 2,
  "show_hidden": false,
  "show_size": true,
  "show_time": false,
  "sort_by": "name",
  "max_entries": 100
}
```

## Output

JSON with entries:

```json
{
  "summary": {"path": "/path", "total_entries": 50, "total_size": 1024000},
  "results": [
    {"name": "main.go", "path": "main.go", "type": "file", "size": 2048},
    {"name": "pkg", "path": "pkg", "type": "directory", "size": 0}
  ]
}
```
