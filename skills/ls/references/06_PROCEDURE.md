---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Choose parameters
  - Step 3: Run inventory
  - Step 4: Present results
  - CLI
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/ls <prompt>` invocation
- Identify the desired scope (root + depth) and ranking intent (mtime/size/name, asc/desc)
- Decide whether git mapping is desired
- Record assumptions explicitly

## Step 2: Choose parameters

- Choose root directory (default: current workspace)
- Choose depth limit
- Decide whether to include hidden entries
- Choose ranking fields (`mtime`, `size`, `name`) and order (`asc`, `desc`)
- Choose `top_n` cap and scan caps
- Choose symlink behavior (default: do not follow)
- Choose git status mapping mode (default: auto/disabled)

## Step 3: Run inventory

- Validate the plan against the schema (`ls_plan_v1`)
- Validate dependencies (`scripts/skill.sh validate` delegates to `aux doctor`)
- Load and validate config (`ls_config_v1`)
- Execute via `scripts/skill.sh run`
- Emit artifacts under `.aux/ls`:
  - `ls_inventory.json`
  - `ls_receipt.json`
  - `ls_view.txt`

When `ls.git_status` is `auto|on` and `git` is available and the root is a work tree, the executor MAY annotate entries with:

- `git_xy` (two-character XY from porcelain v1)
- `git_rename_from` (for renames/copies)

## Step 4: Present results

- Show the parameter block for reproducibility
- Present a ranked list with truncation flags
- Report counts and any caps/truncation applied
- Suggest one narrowing/widening axis if results are empty or too broad

## CLI

From `aux/ls/`, run:

```bash
bash scripts/skill.sh validate
bash scripts/skill.sh run --stdin
```

Or on Windows:

```powershell
pwsh scripts/skill.ps1 validate
pwsh scripts/skill.ps1 run --stdin
```
