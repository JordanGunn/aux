---
description: Canonical discovery → schema → execute flow with worked examples.
index:
  - Canonical Flow
  - Worked Examples
  - Output Structure
---

# Procedure

## Canonical Flow

```
1. Run `aux capabilities`
      → Receive skill registry (version, skills[], composition_note)

2. Select skill(s) based on intent_signals and category

3. For each selected skill, run `aux <skill> --schema`
      → Receive JSON schema for that skill's plan

4. Construct plan JSON matching the schema

5. Run `aux <skill> --plan '<json>'`
      → If mutates=true: inspect dry-run output first, then re-run with --apply
```

For lightweight checks (e.g. "does this skill exist?"):
```
aux capabilities --format names
```

## Worked Examples

### Example 1: Ambiguous intent — "find dead code"

```bash
# Step 1: Discover skills
aux capabilities
# → Registry shows: prune (analysis), usages (analysis), replace (write)

# Step 2: Fetch prune schema
aux prune --schema

# Step 3: Run prune
aux prune --root /path/to/src --glob "**/*.py"
# → Returns candidates list

# Step 4: Verify each candidate with usages
aux usages <candidate_symbol> --root /path/to/src --glob "**/*.py"
# → Returns definitions + references; zero refs confirms candidate

# Step 5 (if confirmed dead): dry-run replace
aux replace <dead_symbol> "" --root /path/to/src --glob "**/*.py"
# → Inspect diff, then add --apply
```

### Example 2: Single-skill task — "find all uses of DataProcessor"

```bash
# Skip /aux — intent is unambiguous

# Fetch schema
aux usages --schema

# Execute
aux usages DataProcessor --root /path/to/src --glob "**/*.py"
```

### Example 3: Multi-file rename — "rename OldClass to NewClass everywhere"

```bash
# Step 1: Impact analysis
aux usages OldClass --root /path/to/src --glob "**/*.py"
# → Shows 12 references in 5 files

# Step 2: Dry-run replace
aux replace OldClass NewClass --root /path/to/src --glob "**/*.py"
# → Shows diff: 12 occurrences in 5 files

# Step 3: Apply (after user confirmation)
aux replace OldClass NewClass --root /path/to/src --glob "**/*.py" --apply

# Step 4: Rename file if needed
aux rename old_class.py new_class.py --apply
```

## Output Structure

`aux capabilities` returns:

```json
{
  "version": "0.2.0",
  "skills": [
    {
      "name": "usages",
      "description": "...",
      "category": "analysis",
      "intent_signals": ["..."],
      "requires": ["root", "symbol"],
      "optional_deps": ["tree-sitter"],
      "compose_with": ["replace", "rename"],
      "mutates": false,
      "schema_cmd": "aux usages --schema"
    }
  ],
  "composition_note": "Fetch --schema for each selected skill before constructing a plan."
}
```

`aux capabilities --format names` returns:
```json
["files", "search", "find", "replace", "rename", "curl", "usages", "prune", "deps", "delta"]
```
