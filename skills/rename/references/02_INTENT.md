---
description: When to invoke rename and how to build the plan.
index:
  - When to use
  - Plan fields
  - Examples
---

# Intent

## When to use

Use rename when:
- A file or directory needs to be moved to a new path
- A file needs to be renamed in place (same directory, new name)
- Multiple files need to be moved in one atomic batch

Do NOT use rename when:
- The file content also needs to change (combine with `aux replace`)
- The destination parent directory does not yet exist (create it first)
- You need to copy (not move) a file — rename does not copy

## Plan fields

Run `aux rename --schema` for the authoritative schema. Key fields:

| Field       | Required | Description                                              |
|-------------|----------|----------------------------------------------------------|
| `moves`     | yes      | List of `{src, dst}` pairs (min 1)                      |
| `backup`    | no       | Copy src to `<src>.bak` before moving (default: false)  |
| `overwrite` | no       | Allow moving onto an existing dst (default: false)      |

Each move pair:

| Field | Required | Description                              |
|-------|----------|------------------------------------------|
| `src` | yes      | Source path (file or directory)          |
| `dst` | yes      | Destination path (absolute or relative)  |

## Examples

Rename a single file (dry-run):
```json
{
  "moves": [{"src": "/repo/old_name.py", "dst": "/repo/new_name.py"}]
}
```

Batch rename with backup:
```json
{
  "moves": [
    {"src": "/repo/foo.py", "dst": "/repo/bar.py"},
    {"src": "/repo/tests/test_foo.py", "dst": "/repo/tests/test_bar.py"}
  ],
  "backup": true
}
```

Move directory:
```json
{
  "moves": [{"src": "/repo/old_module", "dst": "/repo/new_module"}],
  "backup": true
}
```
