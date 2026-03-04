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

Fill in `old`, `new`, and scope (`root`+`globs` or `files`). Nothing else is required.

**3. Phase 1 — Dry run**
```bash
echo '<plan_json>' | bash scripts/skill.sh run --stdin
```

Read the output:
- `summary.files_with_changes` — how many files will be touched
- `summary.total_occurrences` — how many replacements will be made
- `diff` — every changed line, before and after

If the diff looks correct, proceed to Phase 2.
If anything looks wrong, stop and adjust the plan.

**4. Phase 2 — Apply**
```bash
echo '<plan_json>' | bash scripts/skill.sh run --stdin --apply
```

Check `receipt` in the output — every file's status (`modified`, `unchanged`, `error`).

**5. Verify (optional but recommended)**
```bash
aux search --plan '{"root":"<root>","surface":{"root":"<root>","globs":["*.py"]},"search":{"root":"<root>","patterns":[{"value":"<old_string>"}]}}'
```
Expect 0 matches.

---

## CLI reference

```bash
# Dry run — simple mode
aux replace old_name new_name --root /path --glob "*.py"

# Apply — simple mode
aux replace old_name new_name --root /path --glob "*.py" --apply

# Dry run — plan mode (stdin)
echo '{"old":"X","new":"Y","root":"/path","globs":["*.py"]}' \
  | bash scripts/skill.sh run --stdin

# Apply — plan mode (stdin)
echo '{"old":"X","new":"Y","root":"/path","globs":["*.py"]}' \
  | bash scripts/skill.sh run --stdin --apply

# Schema
bash scripts/skill.sh schema
```

## Output shapes

**Phase 1 (dry_run):**
```json
{
  "phase": "dry_run",
  "plan_hash": "sha256:<16 hex>",
  "replace": {"old": "X", "new": "Y"},
  "summary": {"files_examined": 10, "files_with_changes": 4, "total_occurrences": 12, "applied": false},
  "diff": [{"file": "/path/file.py", "occurrences": 3, "changes": [...]}],
  "files_unchanged": ["/path/other.py"]
}
```

**Phase 2 (apply):**
```json
{
  "phase": "apply",
  "plan_hash": "sha256:<16 hex>",
  "replace": {"old": "X", "new": "Y"},
  "summary": {"files_examined": 10, "files_modified": 4, "total_occurrences_replaced": 12, "applied": true},
  "receipt": [{"file": "/path/file.py", "status": "modified", "occurrences_replaced": 3, "backup": null}]
}
```
