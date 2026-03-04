# find

Read-only tree-sitter structural search. Executes AST queries over a codebase and returns matched captures without modifying any files.

## Overview

`find` is the structural search complement to `search`. Where `search` matches text patterns, `find` matches AST shapes — functions with specific names, call expressions, import statements, class definitions, and any other syntactic construct expressible in tree-sitter's query language.

**Key properties:**
- Read-only — no filesystem writes under any circumstances
- Deterministic — same plan JSON produces same output
- Language-aware — parses source into AST before matching
- Grammar-optional — files with no installed grammar are silently skipped

## Prerequisites

```bash
pip install 'aux-skills[query]'   # installs tree-sitter + grammar packages
aux find --languages               # verify which grammars are available
```

## Usage

### Simple mode

```bash
aux find "(function_definition name: (identifier) @name)" \
    --root /path/to/src --glob "*.py"

aux find "(call_expression function: (identifier) @fn)" \
    --root /path/to/src --glob "*.js" --max-matches 50
```

### Plan mode

```bash
aux find --plan '{
  "query": "(function_definition name: (identifier) @name)",
  "root": "/path/to/src",
  "globs": ["*.py"],
  "max_matches": 100
}'
```

### Grammar introspection

```bash
aux find --languages
```

Output:
```json
{
  "available": ["python", "javascript", "typescript"],
  "unavailable": ["rust", "go"],
  "install": "pip install 'aux-skills[query]'"
}
```

### Schema

```bash
aux find --schema
```

## Plan Schema

```json
{
  "query": "(function_definition name: (identifier) @name)",
  "files": [],
  "root": "/path/to/src",
  "globs": ["*.py"],
  "excludes": ["**/test_*.py"],
  "language": null,
  "max_matches": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | yes | Tree-sitter query string |
| `files` | list[str] | no | Explicit file paths |
| `root` | string | no | Root directory for glob targeting |
| `globs` | list[str] | no | Include globs (requires `root`) |
| `excludes` | list[str] | no | Exclude globs |
| `language` | string | no | Language override (auto-detected if null) |
| `max_matches` | int | no | Maximum total matches |

Either `files` or `root` must be provided.

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
    }
  ]
}
```

Each entry in `matches` is one match group (one pattern firing). Each `captures` entry is one captured node, with:
- `name` — capture name from the query (e.g. `"name"`)
- `text` — the matched source text
- `line` — 1-based line number
- `col` — 0-based column offset

## Supported Languages

| Language | Extension(s) | Grammar package |
|----------|-------------|-----------------|
| Python | `.py` | `tree_sitter_python` |
| JavaScript | `.js` | `tree_sitter_javascript` |
| TypeScript | `.ts`, `.tsx` | `tree_sitter_typescript` |
| Rust | `.rs` | `tree_sitter_rust` |
| Go | `.go` | `tree_sitter_go` |
| Java | `.java` | `tree_sitter_java` |
| C | `.c`, `.h` | `tree_sitter_c` |
| C++ | `.cpp`, `.cc`, `.cxx` | `tree_sitter_cpp` |
| Ruby | `.rb` | `tree_sitter_ruby` |
| Bash | `.sh`, `.bash` | `tree_sitter_bash` |

## Tree-Sitter Query Syntax

Basic patterns:

```
(node_type)                             # match any node of this type
(node_type) @capture                    # match and capture
(parent field: (child) @capture)        # match with field name
(node (#eq? @cap "value"))              # predicate: exact match
(node (#match? @cap "^prefix"))         # predicate: regex match
```

Example queries:

```
# All Python function names
(function_definition name: (identifier) @name)

# All JavaScript arrow functions
(arrow_function) @fn

# All Python imports
(import_statement name: (dotted_name) @module)

# Functions named "test_*"
(function_definition name: (identifier) @name (#match? @name "^test_"))

# All class method definitions
(class_definition body: (block (function_definition name: (identifier) @method)))
```

## Skill Interface

```bash
# Init (agent onboarding)
./skills/find/scripts/skill.sh init

# Validate (dependency check)
./skills/find/scripts/skill.sh validate

# Schema
./skills/find/scripts/skill.sh schema

# Run (simple)
./skills/find/scripts/skill.sh run "(function_definition name: (identifier) @name)" --root /path --glob "*.py"

# Run (plan via stdin)
echo '{"query":"...","root":"/path","globs":["*.py"]}' | ./skills/find/scripts/skill.sh run --stdin
```
