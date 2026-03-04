# files

> **Agent-assisted file enumeration using fd**

## Overview

The `files` skill performs deterministic, auditable file enumeration over a directory tree. It converts natural language intent into explicit fd parameters and executes a portable disk scan.

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

## Usage

### Simple mode

```bash
# Find all Python files
aux files --root /path/to/repo --glob "*.py"

# Find directories
aux files --root /path/to/repo --type directory --max-depth 2

# Find with exclusions
aux files --root /path/to/repo --glob "*.js" --exclude "node_modules" --exclude "dist"
```

### Plan mode

```bash
aux files --plan '{
  "root": "/path/to/repo",
  "globs": ["*.py"],
  "excludes": ["**/vendor/**"],
  "type": "file",
  "max_results": 200
}'
```

### Schema

```bash
aux files --schema
```

## Plan Schema

```json
{
  "root": "/path/to/search",
  "globs": ["*.py"],
  "excludes": ["**/vendor/**"],
  "type": "file",
  "max_depth": null,
  "hidden": false,
  "no_ignore": false,
  "max_results": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `root` | string | yes | Search root directory |
| `globs` | list[str] | no | Include glob patterns |
| `excludes` | list[str] | no | Exclude glob patterns |
| `type` | string | no | `file`, `directory`, or `any` (default: `file`) |
| `max_depth` | int | no | Maximum directory depth |
| `hidden` | bool | no | Include hidden files (default: false) |
| `no_ignore` | bool | no | Don't respect gitignore (default: false) |
| `max_results` | int | no | Maximum results to return |

## Output Format

```json
{
  "summary": {"total": 127, "returned": 127},
  "results": [
    {"path": "src/main.py", "type": "file"},
    {"path": "src/util.py", "type": "file"}
  ]
}
```

## Skill Interface

```bash
# Init (agent onboarding)
./skills/files/scripts/skill.sh init

# Validate (dependency check)
./skills/files/scripts/skill.sh validate

# Schema
./skills/files/scripts/skill.sh schema

# Run (simple)
./skills/files/scripts/skill.sh run --root /path --glob "*.py"

# Run (plan via stdin)
echo '{"root":"/path","globs":["*.py"]}' | ./skills/files/scripts/skill.sh run --stdin
```

## Dependencies

- **fd** (`fd` or `fdfind`) — Must be installed and available in PATH
  - On Debian/Ubuntu: `apt install fd-find` (binary is `fdfind`)
  - On macOS: `brew install fd`
  - On Arch: `pacman -S fd`

## Constraints

- **Read-only** — Never modifies files
- **Deterministic** — Same parameters produce same results
- **Auditable** — All criteria visible in output
- **Bounded** — Output capped by `max_results`
- **No content access** — Only enumerates paths, does not read file contents
