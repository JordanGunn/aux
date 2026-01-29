---
name: grep
description: Search patterns across files using ripgrep with concurrent execution. Use for multi-pattern searches, authentication audits, or codebase exploration.
compatibility: Requires aux-skills >= 0.2.0 (pip install aux-skills), ripgrep
metadata:
  version: "2.0"
  command: aux grep
---

# Grep Skill

Search for patterns across files using ripgrep with concurrent execution.

## When to Use

- Multi-pattern searches (authentication keywords, imports, etc.)
- Structured output with file/line/match context
- When you need to search with globs and excludes

## Invocation

```bash
# Simple
aux grep "pattern" --root /path --glob "**/*.py"

# Plan-based (recommended for complex searches)
aux grep --plan '<json>'

# Get schema
aux grep --schema
```

## Plan Schema

```json
{
  "root": "/path/to/search",
  "patterns": [
    {"kind": "regex", "value": "jwt|oauth|oidc"},
    {"kind": "fixed", "value": "Bearer"}
  ],
  "globs": ["**/*.go", "**/*.py"],
  "excludes": ["vendor/**", "node_modules/**"],
  "mode": "regex",
  "case": "smart",
  "context_lines": 2,
  "max_matches": 100
}
```

## Output

JSON with summary and results:

```json
{
  "summary": {"files": 12, "matches": 47, "patterns": [...]},
  "results": [
    {"file": "path/to/file.go", "line": 42, "content": "...", "pattern": "jwt|oauth"}
  ]
}
```
