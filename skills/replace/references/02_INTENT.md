---
description: When to invoke replace and how to build the plan.
index:
  - When to use
  - Plan fields
  - Examples
---

# Intent

## When to use

Use replace when:
- A function, class, variable, or constant needs to be renamed everywhere
- A string literal needs to be updated consistently across many files
- The old string is an exact, unambiguous match (no partial matches that should be skipped)

Do NOT use replace when:
- Some occurrences of the old string should NOT be replaced (do it manually with Read + Edit)
- The replacement requires understanding context (do it manually with Read + Edit)

## Plan fields

Run `aux replace --schema` for the authoritative schema. Key fields:

| Field     | Required | Description                                      |
|-----------|----------|--------------------------------------------------|
| `old`     | yes      | Exact string to find (literal, not regex)        |
| `new`     | yes      | Replacement string                               |
| `root`    | one of   | Root directory — searches recursively with globs |
| `files`   | one of   | Explicit list of file paths                      |
| `globs`   | no       | File patterns to include (e.g. `["*.py"]`)       |
| `excludes`| no       | File patterns to exclude                         |
| `backup`  | no       | Write `.bak` before modifying (default: false)   |

Either `root` or `files` must be present. Not both required.

## Examples

Replace a Python function name across all `.py` files:
```json
{
  "old": "parse_config",
  "new": "load_config",
  "root": "/path/to/repo",
  "globs": ["*.py"]
}
```

Replace across specific files only:
```json
{
  "old": "OLD_API_KEY",
  "new": "API_KEY",
  "files": ["/path/to/config.py", "/path/to/settings.py"]
}
```

Replace with backup:
```json
{
  "old": "DeprecatedClass",
  "new": "NewClass",
  "root": "/path/to/repo",
  "globs": ["*.py", "*.pyi"],
  "backup": true
}
```
