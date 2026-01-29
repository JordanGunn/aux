# ls

**Deterministic directory state inspection**

## Overview

The ls skill performs deterministic, bounded directory state inspection. It converts natural language intent into an explicit plan and executes a reproducible inventory with optional ranking and git status mapping.

The output is structured metadata suitable for **directory comprehension** — understanding what exists, how big it is, and when it changed.

## When to Use

- "What's in this directory?"
- "Show me the largest files"
- "What was modified most recently?"
- "List files with their git status"

## Key Capabilities

- **Metadata collection** — Size, modification time, type
- **Flexible ordering** — Sort by name, size, or modification time
- **Direction control** — Ascending or descending order
- **Depth control** — Recursive or shallow enumeration
- **Git integration** — Optional working tree status per file
- **Bounded output** — Configurable result limits

## Example: Finding Large Files

A developer notices the repository has grown significantly and wants to find the largest files:

```
/ls Show me the 20 largest files in the project
```

### What happens

1. **Agent interprets intent** — Understands ordering (size, descending) and limit (20)
2. **Agent generates plan** — Constructs explicit enumeration parameters
3. **Script executes deterministically** — Runs inventory with ranking
4. **Results are formatted** — Returns entries with size metadata

### Sample output

```
● List largest files in project
  $ bash scripts/skill.sh run --root /path/to/repo --order-by size --direction desc --max-results 20

  total: 20 (of 1,247)

  125.4 MB  data/fixtures/large_dataset.parquet
   45.2 MB  assets/images/satellite_composite.tiff
   23.1 MB  vendor/bin/tool-linux-amd64
   18.7 MB  docs/pdfs/specification.pdf
   12.3 MB  tests/fixtures/sample_video.mp4
    8.9 MB  data/cache/index.db
    ...
```

### Why this matters

In repositories with **thousands of files**:

- Disk usage becomes opaque
- Large files bloat git history
- IDE file browsers don't show sizes easily

The ls skill:

- **Surfaces outliers** — Find large files quickly
- **Supports cleanup** — Know what to `.gitignore` or remove
- **Enables auditing** — Understand repository composition
- **Tracks changes** — See what was modified recently

## Example: Repository State Analysis

A developer wants to understand the current state of a repository before making changes:

```text
/ls Please tell me about the current state of the repo
```

### What happens

1. **Agent interprets intent** — Understands this requires directory inventory + git state
2. **Agent generates plan** — Constructs enumeration with git status enabled
3. **Script executes deterministically** — Runs inventory at repository root
4. **Agent synthesizes results** — Combines ls output with git metadata

### Sample execution

```text
● Run ls skill on repository root
  $ cat > /tmp/ls_plan.json << 'EOF'
  {
    "schema": "ls_plan_v1",
    "ls": {
      "root": "/path/to/repo",
      "depth": 1,
      "order_by": "name",
      "git_status": true,
      "max_results": 100
    }
  }
  EOF
  $ bash scripts/skill.sh run --stdin < /tmp/ls_plan.json
   └ 75 lines...

● Check git status for current changes
  $ git status --short
   └ 4 lines...

● Check recent git commits
  $ git log --oneline -10
   └ 12 lines...
```

### Sample summary

```text
Current Repository State

✅ Overall Health: Good

Active Work:
  - Current Branch: feat/workpackage-update (synced with origin)
  - Latest Work: Updating templates, formatting improvements
  - Uncommitted: 1 modified file (docs/instructions.md)
  - Untracked: 2 directories (.cursor/, .prompts/)

Production Status:
  - Latest Release: v1.6.3 (bug fixes)
  - Recent Activity: Active hotfix cycle (v1.6.0 → v1.6.3)
  - Main Branch: Stable with tagged releases

⚠️ Areas Needing Attention
  - Dev Branch Divergence: 9 commits behind origin/dev
  - Orphaned Branches: 4+ local branches with deleted remotes
  - Multiple WIP Stashes: 5 stashed changesets from different features
  - Branch Proliferation: 10+ local feature branches

🎯 Recommended Next Actions

Immediate:
  - Commit or stash changes to docs/instructions.md
  - Add .cursor/ to .gitignore
  - Review .prompts/ (commit if needed)

Housekeeping:
  - Sync dev branch: git checkout dev && git pull origin dev
  - Prune orphaned branches: git fetch --prune
  - Review and clean up 5 stashes
  - Remove old backup branches
```

### Why this matters

In active development with **multiple contributors and branches**:

- Easy to lose track of uncommitted changes
- Stale branches accumulate silently
- Dev/main divergence causes merge conflicts later

The ls skill:

- **Provides situational awareness** — Know the state before making changes
- **Surfaces git hygiene issues** — Identify orphaned branches, stale stashes
- **Supports workflow decisions** — Know when to sync, stash, or commit
- **Enables proactive maintenance** — Catch problems before they compound

---

## Example: Recent Changes with Git Status

```text
/ls What files were modified in the last week, with their git status?
```

### Sample output

```text
● List recently modified files with git status
  $ bash scripts/skill.sh run --root /path/to/repo --order-by mtime --direction desc --git-status --max-results 50

  total: 47

  2024-01-28 14:32  M   src/auth/handler.go
  2024-01-28 14:30  M   src/auth/middleware.go
  2024-01-28 13:15  A   src/auth/oauth2_client.go
  2024-01-28 11:00  ??  notes.txt
  2024-01-27 16:45  M   config/settings.yaml
  2024-01-27 15:30      docs/README.md
  ...
```

Git status indicators:

- `M` — Modified
- `A` — Added (staged)
- `D` — Deleted
- `??` — Untracked
- `!!` — Ignored
- (blank) — Unchanged

## Usage

### Command Line

```bash
# Basic directory listing
scripts/skill.sh run --root /path/to/dir

# Largest files first
scripts/skill.sh run --root /path/to/dir --order-by size --direction desc

# Most recently modified
scripts/skill.sh run --root /path/to/dir --order-by mtime --direction desc

# With git status
scripts/skill.sh run --root /path/to/repo --git-status

# Recursive with depth limit
scripts/skill.sh run --root /path/to/dir --max-depth 3

# Files only (no directories)
scripts/skill.sh run --root /path/to/dir --type file
```

### Via Plan (stdin)

```bash
cat <<EOF | scripts/skill.sh run --stdin
{
  "schema": "ls_plan_v1",
  "ls": {
    "root": "/path/to/dir",
    "type": "any",
    "order_by": "size",
    "direction": "desc",
    "max_depth": null,
    "max_results": 100,
    "git_status": true,
    "format": "auto"
  }
}
EOF
```

## Output Formats

### Human (TTY)

```
# query_id: sha256:cde012...
# root: /path/to/dir
# order_by: size
# direction: desc

total: 20 (of 1,247)

125.4 MB  data/fixtures/large_dataset.parquet
 45.2 MB  assets/images/satellite_composite.tiff
...
```

### JSONL (pipe/file)

```json
{"kind":"param_block","param_block":{...}}
{"kind":"summary","total":20,"total_all":1247,"truncated":true}
{"kind":"entry","path":"data/fixtures/large_dataset.parquet","type":"file","size":131534438,"mtime":"2024-01-15T10:30:00Z"}
{"kind":"entry","path":"assets/images/satellite_composite.tiff","type":"file","size":47395226,"mtime":"2024-01-10T14:22:00Z"}
```

## Artifacts

Receipts are written to:

```
.aux/ls/<query_id>_receipt.json
```

## Dependencies

- **git** (optional) — Required only for `--git-status`
- **uv** — Python package manager for running the CLI
- **Python 3.10+**

## Constraints

- **Read-only** — Never modifies files or directories
- **Deterministic** — Same plan produces same output for same directory state
- **Auditable** — All parameters visible in output
- **Bounded** — Output capped by `max_results`
- **No content access** — Only reads metadata, not file contents
