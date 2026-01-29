# grep

>**Agent-assisted text search using ripgrep**

## Overview

The `grep` skill performs deterministic, auditable text search over a codebase or file tree. It converts natural language intent into explicit ripgrep parameters and executes a portable disk scan.

The output is evidence suitable for **surface discovery** — identifying where patterns appear before deeper analysis begins.

## When to Use

- "Where is authentication handled?"
- "Find all uses of this API endpoint"
- "Search for TODO comments"
- "Which files reference this configuration key?"

## Key Capabilities

- **Pattern matching** — Fixed strings, regex, or glob patterns
- **Case control** — Case-sensitive or insensitive search
- **Scope filtering** — Include/exclude patterns, file extensions
- **Bounded output** — Configurable line limits prevent runaway results
- **Multiple formats** — Human-readable or JSONL for machine processing

## Example: Cross-Platform Search

A developer needs to understand how authentication flows work across a large polyglot monorepo. Rather than manually grepping through hundreds of thousands of lines of code, they invoke the grep skill:

```
/grep Where is oauth2 used across the platform
```

### What happens

1. **Agent interprets intent** — Understands "oauth2" as the search term, "across the platform" as scope
2. **Agent generates parameters** — Constructs explicit ripgrep arguments
3. **Script executes deterministically** — Runs the search with bounded output
4. **Results are structured** — Returns matches organized by location

### Sample output

```
● Search for oauth2 usage across the platform
  $ bash scripts/skill.sh run --root /path/to/repo --pattern "oauth2" --mode fixed --case insensitive --max-lines 1000

  Found 260 matches across 59 unique files

  Distribution by Component:

    - Backend Services (111 files) - Primary implementation
      - 105 source files with core authentication logic
      - Key modules: internal/auth/ (token management, OAuth2 flows)
      - Uses standard OAuth2 library

    - Infrastructure Configuration (82 files) - Deployment manifests
      - Proxy deployment templates
      - Identity provider configuration
      - Ingress routing rules

    - Frontend Application (3 files) - Minimal direct usage
      - HTTP client configuration
      - Relies on proxy for authentication

    - Support Modules (9 files) - Indirect dependencies
```

### Why this matters

In a **400,000+ line monorepo** spanning multiple languages (Go, Python, TypeScript) and dozens of services, manually searching would:

- Miss edge cases due to inconsistent search terms
- Waste time on irrelevant matches
- Fail to provide architectural context

The grep skill:

- **Controls token usage** — Bounded output prevents context overflow
- **Avoids drift** — Deterministic execution produces consistent results
- **Targets layers** — Results can be filtered by component or file type
- **Enables reasoning** — Structured output supports follow-up analysis

## Agent Usage (Under the hood)

### Command Line

```bash
# Basic search
scripts/skill.sh run --root /path/to/repo --pattern "TODO" --mode fixed

# Regex search, case-sensitive
scripts/skill.sh run --root /path/to/repo --pattern "api/v[0-9]+" --mode regex --case sensitive

# Scoped search with file filtering
scripts/skill.sh run --root /path/to/repo --pattern "import" --include "*.py" --exclude "test_*"
```

### Plan (stdin)

```bash
cat <<EOF | scripts/skill.sh run --stdin
{
  "schema": "grep_plan_v1",
  "grep": {
    "root": "/path/to/repo",
    "pattern": "oauth2",
    "mode": "fixed",
    "case": "insensitive",
    "include": [],
    "exclude": ["vendor/*", "node_modules/*"],
    "max_lines": 1000,
    "context_before": 0,
    "context_after": 0
  }
}
EOF
```

## Output Formats

### Human (TTY)

```
# query_id: sha256:abc123...
# root: /path/to/repo
# pattern: oauth2
# mode: fixed

total: 260
files: 59

/path/to/repo/auth/handler.go:45: oauth2Config := &oauth2.Config{
/path/to/repo/auth/handler.go:52: token, err := oauth2Config.Exchange(ctx, code)
...
```

### JSONL (pipe/file)

```json
{"kind":"param_block","param_block":{...}}
{"kind":"summary","total":260,"files":59,"truncated":false}
{"kind":"match","path":"auth/handler.go","line":45,"content":"oauth2Config := &oauth2.Config{"}
```

## Dependencies

- **ripgrep** (`rg`) — Must be installed and available in PATH
- **uv** — Python package manager for running the CLI
- **Python 3.10+**

## Constraints

- **Read-only** — Never modifies files
- **Deterministic** — Same parameters produce same results
- **Auditable** — All search criteria visible in output
- **Bounded** — Output is capped to prevent runaway results
