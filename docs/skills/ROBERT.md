# robert — Robert C. Martin Package Design Metrics

**Version:** 0.1.0 | **Type:** Read-only | **Tier:** Analysis

## What it does

`aux robert` computes Robert C. Martin's package design metrics from source files:
coupling (Ca/Ce/I), abstractness (Na/Nc/A), distance from the main sequence (D'),
and zone classification per package.

It provides a computable vocabulary for design quality — replacing subjective judgment
with concrete scores. An agent can detect Zone of Pain packages before a refactor,
report a D' score instead of "this is tightly coupled", and verify that proposed
structural changes improve design quality.

## Quick start

```bash
# Analyze all Python packages
aux robert --root ./src --language python

# Analyze all Go packages (excluding package main)
aux robert --root ./src --language go

# Include package main in Go analysis
aux robert --root ./src --language go --include-main

# Plan mode
aux robert --plan '{"root":"./src","language":"python"}'

# Schema
aux robert --schema
```

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--root` | path | required | Search root directory |
| `--language` | go\|python | required | Language to analyze |
| `--glob` | pattern | (lang default) | Include glob (repeatable) |
| `--exclude` | pattern | — | Exclude glob (repeatable) |
| `--hidden` | flag | false | Include hidden files |
| `--no-ignore` | flag | false | Don't respect gitignore |
| `--max-results` | int | unlimited | Cap on packages in output |
| `--include-main` | flag | false | Go only: include package main packages |
| `--plan` | JSON | — | Full plan JSON (overrides other options) |
| `--schema` | flag | — | Print JSON schema and exit |

## Output format

```json
{
  "summary": {
    "language": "python",
    "packages_analyzed": 8,
    "files_searched": 32,
    "zone_counts": { "pain": 2, "uselessness": 0, "warning": 1, "clean": 4, "ok": 1, "unknown": 0 },
    "mean_distance": 0.19,
    "guidance": [
      "pkg/handlers (Zone of Pain): I=0.10, A=0.00. Extract interfaces from structs or invert dependencies to reduce Ca."
    ]
  },
  "packages": [
    {
      "package": "pkg/handlers",
      "path": "/abs/path/pkg/handlers",
      "language": "python",
      "files": 4,
      "ca": 9,
      "ce": 1,
      "instability": 0.1,
      "na": 0,
      "nc": 5,
      "abstractness": 0.0,
      "distance": 0.9,
      "zone": "pain",
      "interpretation": "Zone of Pain — stable (I=0.10) but concrete (A=0.00). Rigid under changing requirements. Consider extracting interfaces to allow substitution, or accept the stability contract explicitly."
    }
  ],
  "errors": []
}
```

## Metrics reference

| Metric | Formula | Range | Meaning |
|--------|---------|-------|---------|
| Ca | packages that import this | ≥ 0 | Incoming dependencies |
| Ce | packages this imports | ≥ 0 | Outgoing dependencies |
| I | Ce / (Ca + Ce) | [0, 1] | 0 = stable, 1 = unstable |
| Na | abstract types in package | ≥ 0 | Interfaces / ABCs / Protocols |
| Nc | concrete types in package | ≥ 0 | Structs / classes |
| A | Na / (Na + Nc) | [0, 1] | 0 = concrete, 1 = abstract |
| D' | \|A + I − 1\| | [0, 1] | 0 = on main sequence (ideal) |

## Zone reference

| Zone | Condition | Meaning |
|------|-----------|---------|
| `pain` | I < 0.3 AND A < 0.3 | Stable-Concrete. Rigid under change. |
| `uselessness` | I > 0.7 AND A > 0.7 | Unstable-Abstract. Wasted abstraction. |
| `warning` | D' ≥ 0.5 | Drifting from main sequence. |
| `clean` | D' < 0.2 | On or near main sequence. Ideal. |
| `ok` | everything else | Minor drift. |
| `unknown` | I or A is null | Insufficient data. |

## Package resolution

**Go**: every directory containing `.go` files is a package. `package main` directories
are excluded by default (use `--include-main` to include them).

**Python**: a directory is a package only if it contains `__init__.py`. Directories
without `__init__.py` are skipped entirely.

## Abstractness detection

| Language | Abstract | Concrete |
|----------|----------|----------|
| Go | `type X interface { }` | `type X struct { }` |
| Python | `class X(ABC):` / `class X(Protocol):` / `class X(ABCMeta):` | All other `class X:` |

Tree-sitter is used when available; text-tier regex fallback runs otherwise.

## Composing with other skills

```bash
# Identify Zone of Pain package, then examine its import graph
aux robert --root ./src --language python
aux deps --root ./src --glob "**/*.py" --target src/handlers/api.py

# Cross-reference with symbol usage for targeted refactor
aux usages --root ./src --symbol "Handler" --language python
```
