---
description: Step-by-step execution procedure.
index:
  - Steps
  - CLI reference
---

# Procedure

## Steps

**1. Get the schema**
```bash
bash scripts/skill.sh schema
```

**2. Build the plan JSON**

Two modes are available:

**Explicit mode** — provide `moves` as a list of `{src, dst}` pairs. Set `backup: true` for directories.

**Discovery mode** — provide `root` + `rules` (and optionally `globs`/`excludes`) to let `aux rename` find files and generate the moves internally. Use this when renaming many files that follow a pattern:

```json
{
  "root": "/path/to/project",
  "globs": ["pipeline/**", "connectors/**"],
  "rules": [
    {"find": "reader", "replace": "source"},
    {"find": "writer", "replace": "sink"}
  ]
}
```

Rules are applied in order to each discovered filename. Only files whose name changes are included in the move list. Globs containing `/` are treated as path-prefix filters; globs without `/` are passed to `fd` as filename patterns. Add `"regex": true` to a rule to use Python regex syntax.

**3. Phase 1 — Dry run**
```bash
echo '<plan_json>' | bash scripts/skill.sh run --stdin
```

Read the output:
- `summary.total_moves` — how many moves are planned
- `summary.conflicts` — destinations that already exist (would be blocked)
- `summary.errors` — invalid src paths or missing parent directories
- `preview` — each move's status: `ok`, `conflict`, or `error`

If the preview looks correct and conflicts/errors are zero, proceed to Phase 2.
If anything looks wrong, stop and correct the plan.

**4. Phase 2 — Apply**
```bash
echo '<plan_json>' | bash scripts/skill.sh run --stdin --apply
```

Check `receipt` in the output — every move's status (`moved`, `conflict`, `error`, `skipped`).

**5. Verify (optional but recommended)**

For file renames, verify the new path exists and the old path is gone:
```bash
ls /path/to/new_name.py   # should exist
ls /path/to/old_name.py   # should not exist
```

---

## CLI reference

```bash
# Dry run — simple mode
aux rename /path/old.py /path/new.py

# Apply — simple mode
aux rename /path/old.py /path/new.py --apply

# Dry run — plan mode, explicit (stdin)
echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
  | bash scripts/skill.sh run --stdin

# Apply — plan mode, explicit (stdin)
echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
  | bash scripts/skill.sh run --stdin --apply

# Dry run — plan mode, discovery (stdin)
echo '{"root":"/path/to/project","globs":["pipeline/**","connectors/**"],"rules":[{"find":"reader","replace":"source"},{"find":"writer","replace":"sink"}]}' \
  | bash scripts/skill.sh run --stdin

# Apply — plan mode, discovery (stdin)
echo '{"root":"/path/to/project","globs":["pipeline/**","connectors/**"],"rules":[{"find":"reader","replace":"source"},{"find":"writer","replace":"sink"}]}' \
  | bash scripts/skill.sh run --stdin --apply

# With backup
aux rename /path/old.py /path/new.py --backup --apply

# Schema
bash scripts/skill.sh schema
```

## Output shapes

**Phase 1 (dry_run):**
```json
{
  "phase": "dry_run",
  "plan_hash": "sha256:<16 hex>",
  "summary": {"total_moves": 2, "conflicts": 0, "errors": 0},
  "preview": [
    {"src": "/path/old.py", "dst": "/path/new.py", "status": "ok"},
    {"src": "/path/bad.py", "dst": "/path/taken.py", "status": "conflict"}
  ]
}
```

**Phase 2 (apply):**
```json
{
  "phase": "apply",
  "plan_hash": "sha256:<16 hex>",
  "timestamp": "2024-01-01T00:00:00Z",
  "summary": {"total_moves": 2, "applied": 1, "skipped": 0, "errors": 1},
  "receipt": [
    {"src": "/path/old.py", "dst": "/path/new.py", "status": "moved", "backup": null},
    {"src": "/path/bad.py", "dst": "/path/taken.py", "status": "conflict", "backup": null}
  ]
}
```

Status values: `"ok"` (dry-run), `"moved"`, `"conflict"`, `"error"`, `"skipped"`
