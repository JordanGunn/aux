---
name: scan
description: Two-phase codebase scan - find files then grep patterns. More efficient than separate find + grep due to in-memory pipeline.
compatibility: Requires aux-skills >= 0.2.0 (pip install aux-skills), ripgrep, fd-find
metadata:
  version: "2.0"
  command: aux scan
---

# Scan Skill

Composite find → grep pipeline that passes file list in-memory.

## When to Use

- Large codebase exploration with targeted file types
- When you want to find files first, then search content
- More efficient than separate find + grep (no intermediate I/O)

## Invocation

```bash
# Plan-based only (required for scan)
aux scan --plan '<json>'

# Get schema
aux scan --schema
```

## Plan Schema

```json
{
  "root": "/path/to/search",
  "surface": {
    "globs": ["**/*.go", "**/*.ts"],
    "excludes": ["vendor/**"],
    "type": "file",
    "max_depth": 10
  },
  "search": {
    "patterns": [
      {"kind": "regex", "value": "auth|jwt|oauth"}
    ],
    "case": "insensitive",
    "context_lines": 2
  }
}
```

## Output

Combined results with surface and search summary:

```json
{
  "summary": {
    "surface_files": 200,
    "matches": 47,
    "files_with_matches": 12,
    "patterns": ["auth|jwt|oauth"]
  },
  "results": [
    {"file": "pkg/auth/token.go", "line": 42, "content": "...", "pattern": "..."}
  ]
}
```

## Pipeline Benefit

Traditional tool chaining:
```
find → [disk I/O] → grep → [disk I/O] → output
```

Scan pipeline:
```
find_kernel() → [memory] → grep_kernel() → output
```

Single command, no intermediate serialization.
