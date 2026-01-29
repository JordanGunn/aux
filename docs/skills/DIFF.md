# diff

**Deterministic git diff inspection**

## Overview

The diff skill performs deterministic, bounded git diff inspection. It converts natural language intent into an explicit diff plan and emits a reproducible summary with optional patch artifacts.

The output is structured change information suitable for **change review** — understanding what has been modified before making decisions.

## When to Use

- "What files have I changed?"
- "Show me the staged changes"
- "Summarize the diff between these branches"
- "What's different from the last commit?"

## Key Capabilities

- **Endpoint comparison** — Working tree vs index, index vs HEAD, commit vs commit
- **Bounded summaries** — Change counts and file lists without full patches
- **Optional patches** — Full diff content when needed
- **Rename detection** — Track file renames across changes
- **Whitespace handling** — Normalize or preserve whitespace differences

## Example: Comprehensive Repository State Analysis

A developer wants to understand all uncommitted changes and branch divergence before deciding what to commit or rebase:

```text
/diff please analyze the areas needing attention
```

### What happens

1. **Agent interprets intent** — Understands multiple comparisons needed (working tree, dev branch, main branch)
2. **Agent generates discovery plan** — Enumerates git surfaces to analyze
3. **Agent generates diff plans** — Creates comparison plans for each surface
4. **Script executes deterministically** — Runs git diff with schema-compliant output
5. **Agent synthesizes results** — Provides actionable summary

### Sample execution

```text
● Run diff discovery to check git status
  $ cat > /tmp/diff_discovery_plan.json << 'EOF'
  {
    "schema": "diff_discovery_plan_v1",
    "discovery": {
      "surface": "git",
      "root": "/path/to/repo"
    }
  }
  EOF
  $ bash scripts/skill.sh discover --stdin < /tmp/diff_discovery_plan.json
   └ 25 lines...

● Run diff on uncommitted changes with patch
  $ cat > /tmp/diff_plan.json << 'EOF'
  {
    "schema": "diff_plan_v1",
    "diff": {
      "surface": "git",
      "root": "/path/to/repo",
      "compare": "working_vs_head",
      "include_patch": true
    }
  }
  EOF
  $ bash scripts/skill.sh run --stdin < /tmp/diff_plan.json
   └ 57 lines...

● Run diff between local dev and origin/dev
  $ cat > /tmp/diff_dev_plan.json << 'EOF'
  {
    "schema": "diff_plan_v1",
    "diff": {
      "surface": "git",
      "root": "/path/to/repo",
      "compare": "ref_vs_ref",
      "from_ref": "dev",
      "to_ref": "origin/dev"
    }
  }
  EOF
  $ bash scripts/skill.sh run --stdin < /tmp/diff_dev_plan.json
   └ 59 lines...
```

### Sample summary

```text
Diff Skill Analysis - Areas Needing Attention

✅ Diff Skill Validated and Operational

1. Uncommitted Changes (Verified by diff skill)
   - File: docs/instructions.md
   - Changes: +33 lines (documentation updates)
   - Insertions: 33
   - Deletions: 0
   - Status: Modified, safe to commit

   Diff skill confirmed:
   {
     "files_changed": 1,
     "insertions": 33,
     "deletions": 0,
     "status": "modified"
   }

2. Dev Branch Divergence (Critical)
   - 9 commits behind origin/dev
   - 39 files affected: +676 insertions, -194 deletions
   - Critical hotfixes missing: v1.6.1, v1.6.2, v1.6.3

   Areas affected:
     - Authentication (auth/claims.go, auth/roles.go)
     - Compute routers (172 lines changed)
     - IAM controllers
     - Frontend services
     - New migration: v1_6/platform.go

3. Current Branch vs Main
   - 1 commit behind main
   - Missing: Storage backup fix
   - Mixed scope: Feature branch contains multiple unrelated changes

Priority Actions:
  🔴 CRITICAL: git checkout dev && git pull origin/dev
  ⚠️ HIGH: git add docs/instructions.md && git commit -m "docs: update instructions"
  ⚠️ MEDIUM: git rebase main on current feature branch
```

### Why this matters

In active development with **multiple branches and contributors**:

- Branch divergence causes merge conflicts
- Missing hotfixes can reintroduce bugs
- Uncommitted changes get lost in context switches

The diff skill:

- **Bounds output** — Summary first, patch on demand
- **Compares any refs** — Working tree, branches, tags, commits
- **Surfaces divergence** — Know when branches need syncing
- **Produces artifacts** — Patches and receipts for audit trails
- **Enables informed decisions** — Commit, rebase, or sync with confidence

---

## Example: Pre-Commit Review

A developer has made changes and wants a quick review before committing:

```text
/diff What have I changed since the last commit?
```

### Sample output

```text
● Diff working tree against HEAD
  $ bash scripts/skill.sh run --compare working_vs_head

  Summary:
    files_changed: 7
    insertions: 142
    deletions: 38

  Changed files:
    M  src/auth/handler.go          (+45, -12)
    M  src/auth/middleware.go       (+23, -8)
    A  src/auth/oauth2_client.go    (+67, -0)
    M  config/settings.yaml         (+3, -2)
    M  tests/auth_test.go           (+4, -16)
    D  src/auth/legacy_auth.go      (0, -0)
    R  docs/AUTH.md -> docs/AUTHENTICATION.md

  Patch written to: .aux/diff/working_vs_head.patch
```

The diff skill:

- **Tracks renames** — Detects when files move
- **Supports review workflows** — Know what to check before committing
- **Produces artifacts** — Patches saved for later reference

## Usage

### Command Line

```bash
# Working tree vs index (unstaged changes)
scripts/skill.sh run --compare working_vs_index

# Index vs HEAD (staged changes)
scripts/skill.sh run --compare index_vs_head

# Working tree vs HEAD (all uncommitted changes)
scripts/skill.sh run --compare working_vs_head

# Between commits
scripts/skill.sh run --compare commit_vs_commit --from abc123 --to def456

# Include full patch output
scripts/skill.sh run --compare working_vs_head --include-patch
```

### Via Plan (stdin)

```bash
cat <<EOF | scripts/skill.sh run --stdin
{
  "schema": "diff_plan_v1",
  "diff": {
    "root": "/path/to/repo",
    "compare": "working_vs_head",
    "from_ref": null,
    "to_ref": null,
    "include_patch": true,
    "rename_detection": true,
    "whitespace": "ignore"
  }
}
EOF
```

## Output Formats

### Human (TTY)

```
# query_id: sha256:789abc...
# root: /path/to/repo
# compare: working_vs_head

Summary:
  files_changed: 7
  insertions: 142
  deletions: 38

Changed files:
  M  src/auth/handler.go          (+45, -12)
  A  src/auth/oauth2_client.go    (+67, -0)
  ...
```

### JSONL (pipe/file)

```json
{"kind":"param_block","param_block":{...}}
{"kind":"summary","files_changed":7,"insertions":142,"deletions":38}
{"kind":"file","path":"src/auth/handler.go","status":"modified","insertions":45,"deletions":12}
{"kind":"file","path":"src/auth/oauth2_client.go","status":"added","insertions":67,"deletions":0}
```

## Artifacts

When `--include-patch` is specified, the full patch is written to:

```
.aux/diff/<comparison>.patch
```

Receipts are written to:

```
.aux/diff/<comparison>_receipt.json
```

## Dependencies

- **git** — Must be installed and available in PATH
- **uv** — Python package manager for running the CLI
- **Python 3.11+**

## Constraints

- **Read-only** — Never modifies repository state
- **Deterministic** — Same plan produces same output for same repo state
- **Auditable** — All comparison parameters visible in output
- **Bounded** — Summaries are compact; patches are opt-in
- **No mutation** — Does not stage, commit, or modify working tree
