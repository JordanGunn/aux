# find

**Agent-assisted file enumeration using fd**

## Overview

The find skill performs deterministic, auditable file enumeration over a directory tree. It converts natural language intent into explicit fd parameters and executes a portable disk scan.

The output is a list of file paths suitable for **surface discovery** — understanding what exists before reading contents.

## When to Use

- "What Python files are in this project?"
- "Find all configuration files"
- "List directories matching this pattern"
- "Show me all test files"

## Key Capabilities

- **Pattern matching** — Glob or regex patterns for file names
- **Extension filtering** — Filter by one or more file extensions
- **Type filtering** — Files, directories, or any
- **Depth control** — Limit search depth
- **Exclusions** — Skip directories or patterns (e.g., `node_modules`, `.git`)
- **Bounded output** — Configurable result limits

## Example: Cross-Cutting Feature Discovery

A developer needs to identify all files related to authentication across a large polyglot monorepo. Rather than manually searching through hundreds of directories, they invoke the find skill:

```text
/find please identify all usages of oauth2 related stuff
```

### What happens

1. **Agent interprets intent** — Understands multiple patterns needed (oauth, oauth2, dex, auth)
2. **Agent generates multiple searches** — Runs targeted enumeration for each pattern
3. **Script executes deterministically** — Each search produces reproducible results
4. **Results are aggregated** — Comprehensive view across the codebase

### Sample execution

```text
● Find all files with oauth in name
  $ bash scripts/skill.sh run --root /path/to/repo --pattern "*oauth*" --type file --max-results 500
   └ 16 lines...

● Find all files with dex in name
  $ bash scripts/skill.sh run --root /path/to/repo --pattern "*dex*" --type file --max-results 500
   └ 27 lines...

● Find all files with auth in name excluding node_modules
  $ bash scripts/skill.sh run --root /path/to/repo --pattern "*auth*" --type file --max-results 500 --exclude "node_modules"
   └ 22 lines...

● Find OAuth directories
  $ bash scripts/skill.sh run --root /path/to/repo --pattern "*oauth*" --type directory --max-results 500
   └ 14 lines...

● Find all files in oauth2 templates directory
  $ bash scripts/skill.sh run --root /path/to/repo/deploy/templates/oauth2 --pattern "*" --type file --max-results 100
   └ 16 lines...

● Find all files in backend auth directory
  $ bash scripts/skill.sh run --root /path/to/repo/backend/server/internal/auth --pattern "*" --type file --max-results 100
   └ 23 lines...
```

### Sample summary

```text
Total OAuth2-Related Files: 42

Backend Implementation (13 files)
  Authentication Module (backend/server/internal/auth/):
    - All 11 files in auth package including token management, controllers, claims
  Environment & Middleware:
    - backend/server/internal/env/oauth2.go - OAuth2 config
    - backend/server/internal/env/dex.go - Identity provider integration
    - backend/server/internal/middleware/auth.go - Auth middleware

  Client Library (2 files)
    - client/internal/auth/auth.go
    - client/internal/auth/oauth2.go

Deployment Configuration (22 files)
  OAuth2-Proxy (4 files in deploy/templates/oauth2/):
    - ConfigMap, Deployment, Secret, Service
  Identity Provider (11 files in deploy/templates/dex/):
    - Core resources: ConfigMap, Deployment, Service, Secrets, RBAC
    - Client configs and connector configs

Container Definitions (2 files)
  - containers/oauth2-proxy/Containerfile
  - containers/oauth2-proxy/.grype.yaml

Documentation & Infrastructure (2 files)
  - docs/architecture/adr/ADR-0042-authentication.md
  - iac/bicep/module/identity/roleassignment/authorization.bicep
```

### Why this matters

In a **polyglot monorepo** with multiple languages (Go, Python, TypeScript) and dozens of services:

- Authentication touches many layers (backend, deployment, infrastructure)
- Files are scattered across different architectural boundaries
- Manual exploration would miss edge cases

The find skill:

- **Surfaces cross-cutting concerns** — Find all files related to a feature across layers
- **Supports iterative refinement** — Run multiple searches with different patterns
- **Enables architectural reasoning** — Understand how features are distributed
- **Produces audit trails** — Each search has a stable query_id for reproducibility

## Usage

### Command Line

```bash
# Find all Python files
scripts/skill.sh run --root /path/to/repo --extension py --type file

# Find directories matching a pattern
scripts/skill.sh run --root /path/to/repo --pattern "*test*" --type directory

# Find with exclusions
scripts/skill.sh run --root /path/to/repo --extension js --exclude "node_modules" --exclude "dist"

# Include hidden files
scripts/skill.sh run --root /path/to/repo --pattern ".*" --hidden
```

### Via Plan (stdin)

```bash
cat <<EOF | scripts/skill.sh run --stdin
{
  "schema": "find_plan_v2",
  "find": {
    "root": "/path/to/repo",
    "include_patterns": [{"kind": "glob", "value": "*.py"}],
    "exclude_patterns": [{"kind": "glob", "value": "__pycache__"}],
    "extensions": [],
    "type": "file",
    "max_depth": null,
    "max_results": 1000,
    "format": "auto",
    "policy": {
      "hidden": false,
      "follow": false,
      "no_ignore": false
    },
    "limits": {
      "max_pattern_length": 512,
      "max_exclude_pattern_length": 512
    }
  }
}
EOF
```

## Output Formats

### Human (TTY)

```
# query_id: sha256:def456...
# root: /path/to/repo
# include_patterns: [{"kind": "glob", "value": "*.py"}]
# extensions: []
# type: file

total: 127
files: 127
directories: 0

data/processing/__init__.py
data/processing/core/engine.py
...
```

### JSONL (pipe/file)

```json
{"kind":"param_block","param_block":{...}}
{"kind":"summary","total":127,"files":127,"directories":0,"truncated":false}
{"kind":"entry","path":"data/processing/__init__.py","type":"file"}
{"kind":"entry","path":"data/processing/core/engine.py","type":"file"}
```

## Dependencies

- **fd** (`fd` or `fdfind`) — Must be installed and available in PATH
  - On Debian/Ubuntu: `apt install fd-find` (binary is `fdfind`)
  - On macOS: `brew install fd`
  - On Arch: `pacman -S fd`
- **uv** — Python package manager for running the CLI
- **Python 3.10+**

## Constraints

- **Read-only** — Never modifies files
- **Deterministic** — Same parameters produce same results
- **Auditable** — All criteria visible in output
- **Bounded** — Output capped by `max_results`
- **No content access** — Only enumerates paths, does not read file contents
