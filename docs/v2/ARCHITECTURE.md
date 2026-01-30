# AUx v2 Architecture

> Design document for the unified CLI architecture.

## Motivation

### Experiment Findings

The token comparison experiment (2026-01-29) revealed:

| Metric | v1 (isolated skills) | Observation |
|--------|---------------------|-------------|
| **Tool calls** | 43 | Agent used `grep_search` 7× but skill only 1× |
| **Adoption** | Partial | High friction to invoke structured plans |
| **Composability** | Manual | No native find→grep workflow |

**Key insight:** The bottleneck is not skill capability—it's adoption friction and lack of composition.

### Pipeline vs Tool Chaining

Current agent model (tool chaining):
```
agent → find → [serialize] → [disk] → agent → grep → [serialize] → [disk] → agent
         ↑                              ↑
         I/O overhead                   I/O overhead
```

Proposed model (true pipeline):
```
agent → aux scan → find_kernel() → [memory] → grep_kernel() → [disk] → agent
                         ↑                           ↑
                         no serialization            single output
```

**Unified CLI enables in-process data flow between commands.**

## Design Principles

1. **Kernels over commands** — Business logic lives in pure functions (kernels), CLI is a thin wrapper
2. **Composition at kernel level** — Pipelines call kernels directly, not subprocesses
3. **Single installation** — One `pip install`, all commands available
4. **Progressive disclosure** — Skills remain thin SKILL.md files pointing to CLI
5. **Spec compliance** — Skills follow Agent Skills format, CLI is an implementation detail

## Architecture Overview

```
aux-v2/
├── pyproject.toml                    # Single package: aux-skills
├── src/aux/
│   ├── __init__.py
│   ├── cli.py                        # Entry point: aux <command>
│   │
│   ├── commands/                     # CLI wrappers (argparse → kernel)
│   │   ├── __init__.py
│   │   ├── grep.py                   # aux grep --plan '...'
│   │   ├── find.py                   # aux find --plan '...'
│   │   ├── diff.py                   # aux diff --plan '...'
│   │   ├── ls.py                     # aux ls --plan '...'
│   │   └── scan.py                   # aux scan --plan '...' (composite)
│   │
│   ├── kernels/                      # Pure functions (no I/O except final)
│   │   ├── __init__.py
│   │   ├── grep.py                   # grep_kernel(patterns, files) → matches
│   │   ├── find.py                   # find_kernel(root, globs) → files
│   │   ├── diff.py                   # diff_kernel(a, b) → hunks
│   │   └── ls.py                     # ls_kernel(path, opts) → entries
│   │
│   ├── plans/                        # Plan schemas and validation
│   │   ├── __init__.py
│   │   ├── schemas.py                # Pydantic models for each plan type
│   │   └── validate.py               # Plan validation utilities
│   │
│   ├── output/                       # Structured output formatting
│   │   ├── __init__.py
│   │   ├── formats.py                # JSON, text, summary modes
│   │   └── truncation.py             # Token-aware truncation
│   │
│   └── util/                         # Shared utilities
│       ├── __init__.py
│       ├── paths.py                  # Path resolution, glob handling
│       └── subprocess.py             # Wrapper for rg, fd, etc.
│
├── skills/                           # Thin SKILL.md wrappers
│   ├── grep/SKILL.md
│   ├── find/SKILL.md
│   ├── diff/SKILL.md
│   ├── ls/SKILL.md
│   └── scan/SKILL.md                 # Composite: find → grep
│
├── scripts/install.sh                # Single install for aux CLI + system deps
└── tests/
    ├── test_kernels/
    ├── test_commands/
    └── test_plans/
```

## Data Flow

### Isolated Command (grep)

```
User/Agent
    │
    ▼
┌─────────────────────────────────────────────────┐
│  aux grep --plan '{"patterns": [...], ...}'     │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  commands/grep.py                               │
│  - Parse args                                   │
│  - Validate plan (plans/validate.py)           │
│  - Call grep_kernel()                          │
│  - Format output                               │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  kernels/grep.py                                │
│  - grep_kernel(patterns, files, opts)          │
│  - Invokes ripgrep via subprocess              │
│  - Returns: List[Match]                        │
└─────────────────────────────────────────────────┘
    │
    ▼
Structured output (JSON/text)
```

### Composite Command (scan = find → grep)

```
User/Agent
    │
    ▼
┌─────────────────────────────────────────────────┐
│  aux scan --plan '{"surface": {...}, ...}'      │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  commands/scan.py                               │
│  - Parse args                                   │
│  - Validate plan                               │
│  - Call find_kernel() → List[Path]             │  ← Phase 1: Surface
│  - Call grep_kernel(files=...) → List[Match]   │  ← Phase 2: Search
│  - Format combined output                      │
└─────────────────────────────────────────────────┘
    │                    │
    ▼                    ▼
┌────────────────┐  ┌────────────────┐
│ kernels/find   │  │ kernels/grep   │
│ → List[Path]   │──│ receives paths │
└────────────────┘  └────────────────┘
         │                   │
         └───────┬───────────┘
                 ▼
         Structured output
```

**Key:** No intermediate disk I/O. File list stays in memory.

## Kernel Interface

Each kernel is a pure function with typed inputs/outputs:

```python
# kernels/grep.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Match:
    path: Path
    line_number: int
    content: str
    pattern: str

def grep_kernel(
    patterns: list[str],
    root: Path,
    *,
    files: list[Path] | None = None,  # Optional: pre-filtered file list
    globs: list[str] | None = None,
    excludes: list[str] | None = None,
    mode: str = "regex",
    case: str = "smart",
    context_lines: int = 0,
) -> list[Match]:
    """
    Search for patterns in files.
    
    If `files` is provided, search only those files (pipeline mode).
    Otherwise, use globs/excludes to filter from root (standalone mode).
    """
    ...
```

```python
# kernels/find.py
from pathlib import Path

def find_kernel(
    root: Path,
    *,
    globs: list[str] | None = None,
    excludes: list[str] | None = None,
    type_filter: str = "file",
    max_depth: int | None = None,
) -> list[Path]:
    """
    Find files matching criteria.
    
    Returns list of paths for downstream pipeline consumption.
    """
    ...
```

## Plan Schemas

Unified schema definitions using Pydantic:

```python
# plans/schemas.py
from pydantic import BaseModel

class GrepPlan(BaseModel):
    root: str
    patterns: list[dict]  # {"kind": "regex"|"fixed", "value": "..."}
    globs: list[str] = []
    excludes: list[str] = []
    mode: str = "regex"
    case: str = "smart"
    context_lines: int = 0

class FindPlan(BaseModel):
    root: str
    globs: list[str] = []
    excludes: list[str] = []
    type: str = "file"
    max_depth: int | None = None

class ScanPlan(BaseModel):
    root: str
    surface: FindPlan      # Phase 1: what to search
    search: GrepPlan       # Phase 2: what to find
```

## SKILL.md Format (v2)

Skills become thin wrappers:

```yaml
---
name: grep
description: Concurrent regex search with ripgrep. Use for multi-pattern searches across codebases.
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
aux grep --plan '<json>'
```

## Plan Schema

```json
{
  "root": "/path/to/search",
  "patterns": [
    {"kind": "regex", "value": "pattern1"},
    {"kind": "fixed", "value": "literal string"}
  ],
  "globs": ["**/*.go", "**/*.py"],
  "excludes": ["vendor/**", "node_modules/**"],
  "mode": "regex",
  "case": "smart",
  "context_lines": 2
}
```

## Examples

See [references/EXAMPLES.md](references/EXAMPLES.md) for common patterns.
```

## Install

Single install validates system dependencies and installs the CLI:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== AUx Install ==="

# Check Python
python3 --version || { echo "error: python3 required"; exit 1; }

./scripts/install.sh

# Verify version
aux --version

# Check system dependencies
aux doctor  # validates rg, fd, git, diff

echo "ok: aux install complete"
```

## Migration Path

### From v1 to v2

1. **Install CLI:** `pip install aux-skills`
2. **Replace skill folders:** Copy new thin SKILL.md files
3. **Update plans:** Schema is compatible, no changes needed
4. **Remove venvs:** Per-skill venvs no longer needed

### Backward Compatibility

- Plan schemas remain compatible
- Output formats unchanged
- SKILL.md names unchanged

## Open Questions

1. **Versioning:** How to handle CLI version vs skill version?
2. **Offline install:** Bundle wheels for air-gapped environments?
3. **Plugin architecture:** Allow third-party kernels?

## Next Steps

1. [ ] Scaffold directory structure
2. [ ] Port grep kernel from v1 cli.py
3. [ ] Port find kernel
4. [ ] Implement scan composite
5. [ ] Write thin SKILL.md files
6. [ ] Test end-to-end with agent
