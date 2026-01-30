---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Choose parameters
  - Step 3: Run search
  - Step 4: Present results
  - CLI
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/grep <prompt>` invocation
- Identify the target concept and minimum evidence needed
- Record assumptions explicitly

## Step 2: Choose parameters

- Choose root directory (default: current workspace)
- Choose content patterns with explicit semantics per pattern:
  - `kind=fixed` (literal)
  - `kind=regex` (pattern)
- Choose include globs (file types to search) — file selection only
- Choose exclude globs (directories/files to skip) — file selection only
- Choose case behavior (`sensitive`, `insensitive`, `smart`)
- Set budget caps

## Step 3: Run search

- Get the current schema: `bash scripts/skill.sh schema`
- Execute via `scripts/skill.sh run` (CLI passthrough or `--stdin` for JSON plan)
- Review the output summary

## Step 4: Present results

- Show the parameter block for reproducibility
- Present matches with file paths and line numbers
- Report counts and distributions
- Suggest refinements if results are too broad or empty

## CLI

**Get the schema first** (source of truth for plan structure):

```bash
bash scripts/skill.sh schema
# or directly: aux grep --schema
```

**Simple mode** (pattern as positional argument):

```bash
aux grep "pattern" --root /path --glob "*.py" --case smart
```

**Plan mode** (JSON via stdin):

```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "root": "/path/to/search",
  "patterns": [{"kind": "fixed", "value": "term"}],
  "globs": ["*.py", "*.go"],
  "excludes": ["**/vendor/**"],
  "case": "smart",
  "max_matches": 200
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
  "summary": {"files": 12, "matches": 47, "patterns": 1},
  "results": [
    {"file": "./path/file.py", "line": 10, "content": "matched line", "pattern": "term"}
  ]
}
```

## Budget Flags

Control output size deterministically:

- `--max-matches N` — Stop after N total matches

## Options Reference

Run `aux grep --help` for the complete, authoritative option list:

- `<pattern>` — Search pattern (positional, required in simple mode)
- `--root <path>` — Root directory (required)
- `--glob <pattern>` — Include glob (repeatable)
- `--exclude <pattern>` — Exclude glob (repeatable)
- `--case <smart|sensitive|insensitive>` — Case behavior
- `--context <n>` — Lines of context around matches
- `--fixed` — Treat pattern as literal (default: regex)
- `--hidden` — Search hidden files
- `--no-ignore` — Don't respect gitignore
- `--max-matches <n>` — Maximum matches to return
