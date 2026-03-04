---
description: Canonical execution path for this skill.
index:
  - Step 1: Gather intent
  - Step 2: Check prerequisites
  - Step 3: Build query plan
  - Step 4: Execute and interpret
  - CLI
  - Output Format
---

# Procedure

## Step 1: Gather intent

- Parse the user's `/find <prompt>` invocation
- Identify: what structural pattern, in which files, with what scope
- Determine the target language (or verify auto-detection from extensions is sufficient)
- Record assumptions explicitly

## Step 2: Check prerequisites

Verify grammar is available for the target language:

```bash
bash scripts/skill.sh validate
aux find --languages
```

If the grammar is unavailable, report this and suggest:
```
pip install 'aux-skills[query]'
```

Get the current schema (source of truth for plan structure):
```bash
bash scripts/skill.sh schema
# or directly: aux find --schema
```

## Step 3: Build query plan

- Get the schema: `bash scripts/skill.sh schema`
- Choose file targets: explicit `files` list or `root` + `globs`
- Write the tree-sitter query string with appropriate captures
- Set `language` override only if auto-detection is insufficient
- Set `max_matches` to limit output for large codebases

## Step 4: Execute and interpret

```bash
# Via stdin
echo '<plan_json>' | bash scripts/skill.sh run --stdin

# Direct CLI
aux find --plan '<plan_json>'

# Simple mode
aux find "(function_definition name: (identifier) @name)" --root /path --glob "*.py"
```

Read the output:
- `total_matches`: how many patterns matched
- `matches`: list of match groups with capture name, text, line, col
- `errors`: grammar or parse errors (per-file)
- Zero matches is valid — report it as the finding

## CLI

**Get the schema first** (source of truth for plan structure):

```bash
bash scripts/skill.sh schema
# or directly: aux find --schema
```

**Check available grammars:**

```bash
aux find --languages
```

**Simple mode:**

```bash
aux find "(function_definition name: (identifier) @name)" \
    --root /path/to/src --glob "*.py"

aux find "(call_expression function: (identifier) @fn)" \
    --root /path/to/src --glob "*.js" --max-matches 50
```

**Plan mode:**

```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "query": "(function_definition name: (identifier) @name)",
  "root": "/path/to/src",
  "globs": ["*.py"],
  "max_matches": 100
}
JSON
```

**Explicit files:**

```bash
cat <<'JSON' | bash scripts/skill.sh run --stdin
{
  "query": "(import_statement name: (dotted_name) @module)",
  "files": ["/path/to/module.py"]
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
  "files_searched": 12,
  "files_with_matches": 5,
  "total_matches": 23,
  "matches": [
    {
      "file": "/abs/path/module.py",
      "language": "python",
      "captures": [
        {"name": "name", "text": "my_function", "line": 10, "col": 4}
      ]
    },
    {
      "file": "/abs/path/util.py",
      "language": "python",
      "captures": [
        {"name": "name", "text": "helper", "line": 3, "col": 0}
      ]
    }
  ]
}
```

On grammar error (per-file):
```json
{
  "files_searched": 3,
  "files_with_matches": 0,
  "total_matches": 0,
  "matches": [],
  "errors": ["/abs/path/file.py: grammar not installed for language 'rust'"]
}
```

## Options Reference

Run `aux find --help` for the complete option list:

- `<query>` — Tree-sitter query string (positional, simple mode)
- `--file <path>` — Explicit file to search (repeatable)
- `--root <path>` — Root directory for glob targeting
- `--glob <pattern>` — Include glob (repeatable)
- `--exclude <pattern>` — Exclude glob (repeatable)
- `--language <name>` — Language override (auto-detected if omitted)
- `--max-matches <n>` — Maximum total matches
- `--plan '<json>'` — Full plan as JSON
- `--schema` — Print JSON schema for --plan
- `--languages` — List available/unavailable grammar packages
