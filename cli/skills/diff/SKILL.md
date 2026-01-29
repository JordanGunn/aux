---
name: diff
description: Compare files or directories and show differences. Use for code review or change analysis.
compatibility: Requires aux-skills >= 0.2.0 (pip install aux-skills), diff
metadata:
  version: "2.0"
  command: aux diff
---

# Diff Skill

Compare files or directories and show structured differences.

## When to Use

- Comparing two versions of a file
- Reviewing changes between directories
- Structured diff output for analysis

## Invocation

```bash
# Simple
aux diff /path/a /path/b --context 3

# Plan-based
aux diff --plan '<json>'

# Get schema
aux diff --schema
```

## Plan Schema

```json
{
  "path_a": "/path/to/original",
  "path_b": "/path/to/modified",
  "context_lines": 3,
  "ignore_whitespace": false,
  "ignore_case": false
}
```

## Output

JSON with hunks:

```json
{
  "summary": {"files": 1, "additions": 5, "deletions": 2},
  "results": [
    {
      "path_a": "file.go",
      "path_b": "file.go",
      "hunks": [
        {"old_start": 10, "old_count": 5, "new_start": 10, "new_count": 8, "lines": [...]}
      ]
    }
  ]
}
```
