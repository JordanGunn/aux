# usages

Symbol cross-reference skill. Returns all definition locations and all reference locations for a named symbol in one structured call.

## Overview

`usages` is the O(1) pre-flight primitive for write skills. Before renaming, replacing, or deleting a symbol, run `aux usages` to get a complete picture of where it is defined and where it is referenced — in a single call, without manual grep composition.

**Execution pipeline:**
1. `fd` — enumerate candidate files by glob
2. `rg` (fixed-string) — exhaustive text matches across all files
3. tree-sitter — tag definition entries with `symbol_type`
4. Correlation — definitions and references separated in one result

**Key properties:**
- Read-only — no filesystem writes under any circumstances
- Deterministic — same plan JSON produces same output
- Tree-sitter is a bundled core dependency — definition tagging is always available
- Language-agnostic text phase — works on any file type

## Prerequisites

```bash
pip install aux-skills   # tree-sitter is bundled — definition tagging works out of the box
```

## Usage

### Simple mode

```bash
aux usages DataProcessor --root /path/to/src --glob "**/*.py"

aux usages process_batch --root /path --glob "**/*.py" --no-definitions
```

### Plan mode

```bash
aux usages --plan '{
  "root": "/path/to/src",
  "symbol": "DataProcessor",
  "globs": ["**/*.py"]
}'
```

### Schema

```bash
aux usages --schema
```

## Plan Schema

```json
{
  "root": "/path/to/src",
  "symbol": "DataProcessor",
  "globs": ["**/*.py"],
  "excludes": [],
  "language": null,
  "definitions": true,
  "hidden": false,
  "no_ignore": false,
  "max_results": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `root` | string | yes | Search root directory |
| `symbol` | string | yes | Exact symbol name (literal, not regex) |
| `globs` | list[str] | no | Include globs |
| `excludes` | list[str] | no | Exclude globs |
| `language` | string | no | Tree-sitter language override |
| `definitions` | bool | no | Enable AST definition tagging (default: true) |
| `hidden` | bool | no | Include hidden files |
| `no_ignore` | bool | no | Don't respect gitignore |
| `max_results` | int | no | Maximum total results |

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

**Summary fields:**
- `symbol` — the searched symbol name
- `definitions` — count of definition sites
- `references` — count of reference sites
- `files` — distinct files containing at least one match
- `files_searched` — total files examined
- `truncated` — present and `true` if `max_results` was hit

**Result entry fields:**
- `kind` — `"definition"` or `"reference"`
- `file` — absolute path
- `line` — 1-based line number
- `content` — matched line text
- `symbol_type` — definition only: `"class"`, `"function"`, `"interface"`, etc.
- `col` — definition only: 0-based column from AST

## Supported Definition Languages

| Language | Extensions | Symbol types detected |
|----------|-----------|----------------------|
| Python | `.py` | `function`, `class` |
| JavaScript | `.js` | `function`, `class` |
| TypeScript | `.ts`, `.tsx` | `function`, `class`, `interface`, `type` |
| Go | `.go` | `function`, `type` |
| Rust | `.rs` | `function`, `struct`, `enum` |
| Java | `.java` | `method`, `class`, `interface` |

Other file types are fully supported for reference search — only definition tagging requires a grammar.

## Skill Interface

```bash
# Init (agent onboarding)
./skills/usages/scripts/skill.sh init

# Validate (dependency check)
./skills/usages/scripts/skill.sh validate

# Schema
./skills/usages/scripts/skill.sh schema

# Run (simple)
./skills/usages/scripts/skill.sh run DataProcessor --root /path --glob "**/*.py"

# Run (plan via stdin)
echo '{"root":"/path","symbol":"DataProcessor","globs":["**/*.py"]}' | \
  ./skills/usages/scripts/skill.sh run --stdin
```
