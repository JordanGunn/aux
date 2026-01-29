---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Choose parameters
  - Step 3: Run enumeration
  - Step 4: Present results
  - CLI
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/find <prompt>` invocation
- Identify the target file types and scope
- Record assumptions explicitly

## Step 2: Choose parameters

- Choose root directory (default: current workspace)
- Choose include patterns (name patterns) with explicit semantics:
  - `kind=glob` (fd `--glob`)
  - `kind=regex` (fd default)
- Choose extensions (file types to include)
- Choose exclude patterns (directories/files to skip) with explicit semantics
- Choose type filter (`file`, `directory`, `any`)
- Set depth limit and result caps

## Step 3: Run enumeration

- Validate the plan against the schema (`find_plan_v2` preferred)
- Execute via `scripts/skill.sh run`
- Review the echoed parameter block

## Step 4: Present results

- Show the parameter block for reproducibility
- Present file paths sorted alphabetically
- Report counts and type distributions
- Suggest refinements if results are too broad or empty

## CLI

From `aux/find/`, run:

```bash
bash scripts/skill.sh run --root . --pattern "*.py" --type file
```

Or on Windows:

```powershell
pwsh scripts/skill.ps1 run --root . --pattern "*.py" --type file
```

### Validate

Before first use, verify dependencies:

```bash
bash scripts/skill.sh validate
```

## Output Formats

The `--format` flag controls output shape. All formats emit a `param_block` first.

### `auto` (default)

Selects `human` for interactive use, `jsonl` when piped.

### `human`

Plain text summary followed by file paths:

```text
total: 50
files: 42
directories: 8

src/main.py
src/utils/helpers.py
tests/test_main.py
```

### `jsonl`

Newline-delimited JSON for programmatic consumption:

```json
{"kind":"param_block","param_block":{...}}
{"kind":"summary","total":50,"files":42,"directories":8,"truncated":false}
{"kind":"entry","path":"src/main.py","type":"file"}
```

## Budget Flags

Control output size deterministically:

- `--max-results N` — Cap total results (default: 1000)
- `--max-depth N` — Limit directory depth

Caps are applied **after sorting**, so truncated output remains stable.

## Reproducibility

Every invocation emits:

- `param_block` — Full parameter set including `argv`
- `query_id` — SHA256 hash of normalized parameters
