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

- Get the current schema: `bash scripts/skill.sh schema`
- Execute via `scripts/skill.sh run` (CLI passthrough or `--stdin` for JSON plan)
- Review the output summary

## Step 4: Present results

- Present file paths sorted alphabetically
- Report counts and type distributions
- Suggest refinements if results are too broad or empty

## CLI

**Get the schema first** (source of truth for plan structure):

```bash
bash scripts/skill.sh schema
# or directly: aux find --schema
```

**Simple mode** (options as flags):

```bash
aux find --root /path --glob "*.py" --type file
```

**Plan mode** (JSON via stdin):

```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "root": "/path/to/search",
  "globs": ["*.py", "*.go"],
  "excludes": ["**/vendor/**"],
  "type": "file",
  "max_results": 200
}
JSON
```

### Validate

Before first use, verify dependencies:

```bash
bash scripts/skill.sh validate
```

## Output Format

Output is JSON with structure:

```json
{
  "summary": {"total": 50, "files": 42, "directories": 8},
  "results": [
    {"path": "src/main.py", "type": "file"}
  ]
}
```

## Budget Flags

Control output size deterministically:

- `--max-results N` — Cap total results
- `--max-depth N` — Limit directory depth

## Options Reference

Run `aux find --help` for the complete, authoritative option list:

- `--root <path>` — Root directory (required)
- `--glob <pattern>` — Include glob (repeatable)
- `--exclude <pattern>` — Exclude glob (repeatable)
- `--type <file|directory|any>` — Entry type filter
- `--max-depth <n>` — Maximum search depth
- `--max-results <n>` — Maximum results to return
- `--hidden` — Include hidden files
- `--no-ignore` — Don't respect gitignore
