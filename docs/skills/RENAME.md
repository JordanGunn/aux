# rename

Move or rename files and directories with a mandatory dry-run gate.

## Overview

`aux rename` replaces the three-step read-write-delete pattern agents use to rename files. A single plan invocation previews all moves, surfaces conflicts, and applies on explicit instruction. It wraps `shutil.move` with validation, optional backup, and conflict detection.

## Invocation modes

```bash
# Simple mode (single file, dry-run)
aux rename <src> <dst>

# Simple mode (apply)
aux rename <src> <dst> --apply

# Plan mode — explicit (batch, dry-run)
aux rename --plan '{"moves":[{"src":"...","dst":"..."}]}'

# Plan mode — explicit (apply)
aux rename --plan '{"moves":[{"src":"...","dst":"..."}]}' --apply

# Plan mode — discovery (dry-run): find files and rename by rules
aux rename --plan '{"root":"/path","globs":["pipeline/**"],"rules":[{"find":"reader","replace":"source"}]}'

# Plan mode — discovery (apply)
aux rename --plan '{"root":"/path","globs":["pipeline/**"],"rules":[{"find":"reader","replace":"source"}]}' --apply

# Schema
aux rename --schema
```

## Two-phase workflow

**Phase 1 — dry-run (default)**

Returns a preview of what would happen. No writes.

```bash
aux rename /path/old.py /path/new.py
```

Output:
```json
{
  "phase": "dry_run",
  "plan_hash": "sha256:abcdef1234567890",
  "summary": {"total_moves": 1, "conflicts": 0, "errors": 0},
  "preview": [{"src": "/path/old.py", "dst": "/path/new.py", "status": "ok"}]
}
```

**Phase 2 — apply**

Uses the same plan. The `plan_hash` must match Phase 1.

```bash
aux rename /path/old.py /path/new.py --apply
```

Output:
```json
{
  "phase": "apply",
  "plan_hash": "sha256:abcdef1234567890",
  "timestamp": "2024-01-01T00:00:00Z",
  "summary": {"total_moves": 1, "applied": 1, "skipped": 0, "errors": 0},
  "receipt": [{"src": "/path/old.py", "dst": "/path/new.py", "status": "moved", "backup": null}]
}
```

## Plan schema

Two modes — exactly one must be used per plan.

**Explicit mode** (provide `moves`):
```json
{
  "moves": [
    {"src": "/path/to/source", "dst": "/path/to/destination"}
  ],
  "backup": false,
  "overwrite": false
}
```

**Discovery mode** (provide `root` + `rules`):
```json
{
  "root": "/path/to/project",
  "globs": ["pipeline/**", "connectors/**", "workers/**"],
  "excludes": [],
  "rules": [
    {"find": "reader", "replace": "source"},
    {"find": "writer", "replace": "sink"},
    {"find": "read_worker", "replace": "source_worker", "regex": false}
  ],
  "backup": false,
  "overwrite": false
}
```

`rules` are applied in order to each discovered filename. Only files whose name changes under the rules are included in the rename operation. Globs containing `/` are treated as path-prefix filters (e.g. `pipeline/**` restricts discovery to the `pipeline/` subdirectory). Set `"regex": true` on a rule to use Python regex syntax in `find`.

Run `aux rename --schema` for the full JSON schema.

## Options

| Flag          | Description                                     |
|---------------|-------------------------------------------------|
| `--apply`     | Apply moves to disk (default: dry-run)          |
| `--backup`    | Copy src to `<src>.bak` before moving           |
| `--overwrite` | Allow moving onto an existing destination       |
| `--plan`      | JSON plan string (batch mode, overrides positionals) |
| `--schema`    | Print JSON schema for `--plan` and exit         |

## Safety constraints

- **No parent creation**: `dst.parent` must already exist
- **No silent overwrites**: `dst` existing without `--overwrite` is a conflict surfaced in dry-run
- **Sequential execution**: moves run in declaration order to avoid filesystem races
- **Backup recommended for directories**: use `--backup` or `backup: true` when renaming directories

## Skill scripts

```bash
# Onboarding (agents)
./skills/rename/scripts/skill.sh init

# Validate dependencies
./skills/rename/scripts/skill.sh validate

# Schema
./skills/rename/scripts/skill.sh schema

# Dry-run via stdin
echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
  | ./skills/rename/scripts/skill.sh run --stdin

# Apply via stdin
echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
  | ./skills/rename/scripts/skill.sh run --stdin --apply
```
