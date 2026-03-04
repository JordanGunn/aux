---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Check prerequisites
  - Step 3: Build plan
  - Step 4: Execute and interpret
  - CLI
  - Output Format
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/usages <prompt>` invocation
- Identify: what symbol name, in which root directory, scoped to which file types
- Record whether tree-sitter definition tagging is needed (default: yes)
- Record assumptions explicitly

## Step 2: Check prerequisites

Verify the CLI is available:

```bash
bash scripts/skill.sh validate
```

Get the current schema (source of truth for plan structure):

```bash
bash scripts/skill.sh schema
# or directly: aux usages --schema
```

## Step 3: Build plan

- Use `root` for the search root (required)
- Use `globs` to scope to file types (e.g. `["**/*.py"]`)
- Use `excludes` to remove noise (e.g. `["**/__pycache__/**"]`)
- Set `definitions: false` only if tree-sitter is unavailable or speed is critical
- Set `language` only if auto-detection from file extensions is insufficient

## Step 4: Execute and interpret

```bash
# Via stdin
echo '<plan_json>' | bash scripts/skill.sh run --stdin

# Direct CLI
aux usages --plan '<plan_json>'

# Simple mode
aux usages DataProcessor --root /path --glob "**/*.py"
```

Read the output:
- `summary.definitions`: number of definition sites found
- `summary.references`: number of reference sites found
- `results`: flat list ordered definitions-first, then references
- `errors`: per-file errors (grammar missing, parse failure)
- Zero definitions with non-zero references is normal for symbols defined outside scope

## CLI

**Get the schema first** (source of truth for plan structure):

```bash
bash scripts/skill.sh schema
# or directly: aux usages --schema
```

**Simple mode:**

```bash
aux usages DataProcessor --root /path/to/src --glob "**/*.py"

aux usages process_batch --root /path --glob "**/*.py" --no-definitions
```

**Plan mode:**

```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "root": "/path/to/src",
  "symbol": "DataProcessor",
  "globs": ["**/*.py"]
}
JSON
```

**Validate:**

```bash
bash scripts/skill.sh validate
```

## Output Format

```json
{
  "summary": {
    "symbol": "DataProcessor",
    "definitions": 1,
    "references": 23,
    "files": 6,
    "files_searched": 9
  },
  "results": [
    {
      "kind": "definition",
      "symbol_type": "class",
      "file": "/abs/path/pipeline/processor.py",
      "line": 24,
      "col": 0,
      "content": "class DataProcessor:"
    },
    {
      "kind": "reference",
      "file": "/abs/path/pipeline/batch_runner.py",
      "line": 13,
      "content": "from .processor import DataProcessor"
    }
  ],
  "errors": []
}
```

Fields per result entry:
- `kind` — `"definition"` or `"reference"`
- `file` — absolute path
- `line` — 1-based line number
- `content` — matched line text
- `symbol_type` — present on definitions only (`"class"`, `"function"`, etc.)
- `col` — present on definitions only, 0-based column from AST

## Options Reference

Run `aux usages --help` for the complete option list:

- `<symbol>` — Exact symbol name (positional, simple mode)
- `--root <path>` — Search root directory (required)
- `--glob <pattern>` — Include glob (repeatable)
- `--exclude <pattern>` — Exclude glob (repeatable)
- `--language <name>` — Tree-sitter language override
- `--no-definitions` — Skip AST definition tagging
- `--hidden` — Include hidden files
- `--no-ignore` — Don't respect gitignore
- `--max-results <n>` — Maximum total results
- `--plan '<json>'` — Full plan as JSON
- `--schema` — Print JSON schema for --plan
