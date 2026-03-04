# deps — Module Dependency Graph

**Version:** 0.1.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux deps` builds a module import graph from source files, computes per-file coupling
metrics (afferent Ca, efferent Ce, instability), and detects import cycles via DFS.

It is the module-level topology primitive complementing `usages` (symbol-level) and
`prune` (reference-counting).

## Quick start

```bash
# Full graph — all Python files, sorted by most-imported first
aux deps --root ./src --glob "**/*.py"

# Target mode — who does find.py import, and who imports it?
aux deps --root ./src --glob "**/*.py" --target src/kernels/find.py

# Plan mode
aux deps --plan '{"root":"./src","globs":["**/*.py"]}'

# Schema
aux deps --schema
```

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | required | Search root directory |
| `--glob` | `[]` | Include files matching glob (repeatable) |
| `--exclude` | `[]` | Exclude files matching glob (repeatable) |
| `--target` | `null` | Focus on one file (full path or relative to cwd) |
| `--language` | auto | Tree-sitter language override |
| `--max-depth` | `null` | Transitive depth limit (reserved) |
| `--hidden` | false | Include hidden files |
| `--no-ignore` | false | Don't respect gitignore |
| `--max-results` | `null` | Cap on files in output |

## Output schema

```json
{
  "summary": {
    "files_analyzed": 42,
    "files_searched": 42,
    "cycles_detected": 0,
    "most_coupled": "/abs/path/to/hub.py"
  },
  "files": [
    {
      "file": "/abs/path/to/file.py",
      "language": "python",
      "imports": ["aux.kernels.find", "aux.kernels.grep"],
      "imported_by": ["/abs/path/to/cli.py"],
      "efferent": 2,
      "afferent": 1,
      "instability": 0.6667
    }
  ],
  "cycles": []
}
```

## Coupling metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Afferent (Ca) | files that import this | Higher = more stable (widely used) |
| Efferent (Ce) | modules this file imports | Higher = more volatile (many deps) |
| Instability (I) | Ce / (Ca + Ce) | 0 = stable, 1 = unstable |

## Import extraction

1. **AST tier** (tree-sitter, when available): accurate multi-line and aliased imports
2. **Text tier** (always available): per-language regex fallback

Both produce the same `ImportEdge` structure. AST tier is simply more accurate.

## Module resolution

Resolution is best-effort within the scanned file set only:
- Module last component (e.g., `aux.kernels.find` → `find`) matched against file stems
- External packages and stdlib appear in `imports` strings but are not graph edges
- Cycles are only reported for files within the scanned set

## Skill layer

```bash
./skills/deps/scripts/skill.sh init       # onboarding — load all references
./skills/deps/scripts/skill.sh validate   # check dependencies
./skills/deps/scripts/skill.sh schema     # emit JSON schema
./skills/deps/scripts/skill.sh run --root ./src --glob "**/*.py"
```
