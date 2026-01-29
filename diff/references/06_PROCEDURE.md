---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Choose parameters
  - Step 3: Run discovery
  - Step 4: Run diff
  - Step 5: Present results
  - CLI
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/diff <prompt>` invocation
- Identify the desired comparison intent (working tree vs index, staged vs HEAD, etc.)
- Identify whether a patch is requested
- Record assumptions explicitly

## Step 2: Choose parameters

- Choose surface (v1: `git` only)
- Choose repository root / working directory
- Choose endpoints/mode (explicit)
- Choose rename detection flag (explicit)
- Choose whitespace and line-ending normalization flags (explicit)
- Choose caps (max files / max patch bytes / max lines)

## Step 3: Run discovery

- Validate the discovery plan against the schema (`diff_discovery_plan_v1`)
- Validate assets fail-closed (`scripts/skill.sh validate`)
- Detect git availability and repo root; emit discovery receipt when git is missing/not a repo
- Emit discovery artifacts under `.aux/diff`:
  - `diff_discovery.json`
  - `diff_discovery_receipt.json`
  - `diff_discovery_view.txt`

## Step 4: Run diff

- Validate the execution plan against the schema (`diff_plan_v1`)
- Execute diff generation in a bounded manner
- Emit run artifacts under `.aux/diff`:
  - `diff_summary_v1.json`
  - `diff_receipt_v1.json`
  - `diff.patch` (optional; only when requested)

## Step 5: Present results

- Show the plan parameter block for reproducibility
- Present summary counts and truncation flags
- If a patch was emitted, present it as an artifact (do not interpret)

## CLI

From `aux/diff/`, run:

```bash
bash scripts/skill.sh validate
bash scripts/skill.sh discover --stdin
bash scripts/skill.sh run --stdin
```

Or on Windows:

```powershell
pwsh scripts/skill.ps1 validate
pwsh scripts/skill.ps1 discover --stdin
pwsh scripts/skill.ps1 run --stdin
```
