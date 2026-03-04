# delta — Semantic Git Diff

**Version:** 0.1.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux delta` surfaces what has semantically changed since a git ref. It combines
git's line-level diff stats with tree-sitter symbol extraction to produce a
structured account of: which files changed, how many lines, and which symbols
(functions, classes, types) were added or removed.

Directly addresses accumulated session drift: after a sequence of edits, call
delta to know exactly what changed and what API surface was affected.

## Quick start

```bash
# Changes vs. working tree (HEAD → uncommitted)
aux delta --root .

# Since N commits ago
aux delta --root . --ref-from HEAD~3 --glob "**/*.py"

# Between two refs
aux delta --root . --ref-from v1.0 --ref-to v2.0

# Stat only (no tree-sitter needed)
aux delta --root . --stat-only

# Plan mode
aux delta --plan '{"root":".","ref_from":"HEAD~2","globs":["**/*.py"]}'

# Schema
aux delta --schema
```

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | required | Git repo root or subdirectory |
| `--ref-from` | `HEAD` | Base ref |
| `--ref-to` | `null` | Target ref (null = working tree) |
| `--glob` | `[]` | Filter changed files by glob (repeatable) |
| `--exclude` | `[]` | Exclude files matching glob (repeatable) |
| `--language` | auto | Tree-sitter language override |
| `--stat-only` | false | Skip symbol analysis, return only line counts |
| `--no-semantic` | false | Alias for --stat-only |
| `--max-files` | `null` | Cap on files analyzed |

## Output schema

```json
{
  "summary": {
    "files_changed": 3,
    "symbols_added": 2,
    "symbols_removed": 1,
    "lines_added": 45,
    "lines_deleted": 12
  },
  "ref_from": "HEAD",
  "ref_to": "working tree",
  "files": [
    {
      "file": "/abs/path/to/file.py",
      "language": "python",
      "status": "modified",
      "additions": 20,
      "deletions": 5,
      "symbols": {
        "added": [{"name": "new_function", "type": "function"}],
        "removed": [{"name": "old_helper", "type": "function"}],
        "unchanged": [{"name": "MyClass", "type": "class"}]
      }
    }
  ]
}
```

## Degradation chain

| Availability | Mode | Symbols field |
|-------------|------|---------------|
| git + tree-sitter | Full semantic | SymbolDiff (added/removed/unchanged) |
| git only | Stat-only (auto) | `null` |
| No git | Error | Empty result with error message |

## Symbol diff semantics

- **added** — (name, type) in ref_to but not ref_from
- **removed** — (name, type) in ref_from but not ref_to
- **unchanged** — (name, type) present in both

Signature changes (same name, different parameters) appear as **unchanged** —
intentionally conservative to avoid false positives on parameter edits.

## Skill layer

```bash
./skills/delta/scripts/skill.sh init       # onboarding — load all references
./skills/delta/scripts/skill.sh validate   # check dependencies (git + aux)
./skills/delta/scripts/skill.sh schema     # emit JSON schema
./skills/delta/scripts/skill.sh run --root . --ref-from HEAD~1
```
