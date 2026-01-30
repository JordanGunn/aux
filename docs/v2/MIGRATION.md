# Migration Strategy: ASI-Compliant Skills + Unified CLI

## Overview

This document describes the migration from standalone skill implementations to ASI-compliant skills that invoke the unified `aux` CLI as their execution backend.

**Key insight**: The CLI is Layer 3 (deterministic execution). Skills are Layer 2 + Layer 4 (reasoning contracts, judgment contracts, guardrails). They are complementary, not interchangeable.

---

## Current State

### What We Have

```
aux/
├── cli/                          # ✓ Unified execution backend
│   ├── src/aux/                  # aux grep, aux find, aux diff, aux ls, aux scan
│   ├── pyproject.toml
│   └── skills/                   # ✗ NOT actual skills (just CLI docs)
│       ├── grep/SKILL.md
│       ├── find/SKILL.md
│       └── ...
│
└── skills/                       # ✓ ASI-compliant structure (old)
    ├── grep/
    │   ├── SKILL.md
    │   ├── references/           # Full progressive disclosure
    │   ├── assets/schemas/       # Entropy control
    │   └── scripts/src/cli.py    # ✗ Standalone Python (not CLI)
    ├── find/
    ├── diff/
    └── ls/
```

### Problems

1. `cli/skills/` contains thin SKILL.md files that lack ASI governance (no references, no contracts, no guardrails)
2. `skills/*/scripts/` invoke standalone Python implementations, not the unified CLI
3. Two implementations of the same logic (standalone + CLI kernels)

---

## Target State

```
aux/
├── cli/                          # Execution backend (Layer 3)
│   ├── src/aux/
│   │   ├── cli.py               # Entry point
│   │   ├── kernels/             # Pure functions
│   │   ├── commands/            # CLI wrappers
│   │   ├── plans/               # Pydantic schemas
│   │   └── output/              # Formatting
│   ├── pyproject.toml
│   └── README.md                # CLI documentation only
│
└── skills/                       # ASI-compliant skills (Layer 2 + 4)
    ├── grep/
    │   ├── SKILL.md             # Thin pointer to references
    │   ├── references/
    │   │   ├── 00_ROUTER.md     # Entry routing
    │   │   ├── 01_SUMMARY.md    # Quick overview
    │   │   ├── 02_CONTRACTS.md  # Reasoning contract
    │   │   ├── 03_TRIGGERS.md   # When to use
    │   │   ├── 04_NEVER.md      # Guardrails
    │   │   ├── 05_ALWAYS.md     # Invariants
    │   │   ├── 06_PROCEDURE.md  # Invokes CLI
    │   │   └── 07_FAILURES.md   # Error handling
    │   ├── assets/
    │   │   ├── schemas/         # JSON schemas (entropy control)
    │   │   └── templates/       # Plan templates
    │   └── scripts/
    │       ├── skill.sh         # → aux grep --plan
    │       ├── skill.ps1        # → aux grep --plan
    │       └── src/             # (optional) validation helpers
    ├── find/
    ├── diff/
    ├── ls/
    └── scan/
```

---

## Migration Steps

### Phase 1: Remove False Skills

Delete `cli/skills/` — these are not skills, just documentation that was misplaced.

```bash
rm -rf cli/skills/
```

The CLI README already documents usage. Skills don't belong inside the CLI.

---

### Phase 2: Update Skill Scripts

For each skill in `skills/`, replace the standalone Python invocation with CLI invocation.

#### 2.1 Create `scripts/skill.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Subcommands
case "${1:-}" in
  validate)
    # Read-only self-check
    aux doctor
    ;;
  schema)
    # Emit JSON schema for plan
    aux grep --schema
    ;;
  run)
    shift
    if [[ "${1:-}" == "--stdin" ]]; then
      # Plan-based invocation (recommended)
      aux grep --plan "$(cat)"
    else
      # CLI argument passthrough
      aux grep "$@"
    fi
    ;;
  *)
    echo "Usage: skill.sh {validate|schema|run}" >&2
    exit 1
    ;;
esac
```

#### 2.2 Create `scripts/skill.ps1`

```powershell
param(
    [Parameter(Position=0)]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

switch ($Command) {
    "validate" {
        aux doctor
    }
    "schema" {
        aux grep --schema
    }
    "run" {
        if ($Args[0] -eq "--stdin") {
            $plan = $input | Out-String
            aux grep --plan $plan
        } else {
            aux grep @Args
        }
    }
    default {
        Write-Error "Usage: skill.ps1 {validate|schema|run}"
        exit 1
    }
}
```

---

### Phase 3: Align Schemas

The CLI uses Pydantic schemas. Skills should have matching JSON schemas in `assets/schemas/`.

#### 3.1 Export CLI Schemas

```bash
aux grep --schema > skills/grep/assets/schemas/grep_plan.schema.json
aux find --schema > skills/find/assets/schemas/find_plan.schema.json
aux diff --schema > skills/diff/assets/schemas/diff_plan.schema.json
aux ls --schema > skills/ls/assets/schemas/ls_plan.schema.json
aux scan --schema > skills/scan/assets/schemas/scan_plan.schema.json
```

#### 3.2 Create Plan Templates

For each schema, create a template in `assets/templates/`:

```json
{
  "$comment": "grep_plan template - fill in values",
  "root": "/path/to/search",
  "patterns": [
    {"kind": "regex", "value": ""}
  ],
  "globs": ["**/*"],
  "excludes": [],
  "case": "smart",
  "context_lines": 0,
  "max_matches": 1000
}
```

---

### Phase 4: Update References

#### 4.1 Update `06_PROCEDURE.md`

Each skill's procedure should invoke the CLI, not standalone Python:

```markdown
## Execution

### Step 1: Validate environment

```bash
scripts/skill.sh validate
```

### Step 2: Generate plan

Agent generates a plan conforming to the schema in `assets/schemas/grep_plan.schema.json`.

### Step 3: Execute

```bash
echo '<plan_json>' | scripts/skill.sh run --stdin
```

Or with CLI arguments:

```bash
scripts/skill.sh run --root /path --pattern "TODO" --glob "**/*.py"
```
```

#### 4.2 Update `02_CONTRACTS.md`

Reference the CLI schema as the reasoning contract:

```markdown
## Reasoning Contract

The agent must translate natural language intent into a plan conforming to:

- Schema: `assets/schemas/grep_plan.schema.json`
- Template: `assets/templates/grep_plan.template.json`

### Derivation Rules

| Field | Derivation |
|-------|------------|
| `root` | From user-specified path or current working directory |
| `patterns` | From user search terms; agent chooses `regex` vs `fixed` |
| `globs` | From user file type hints; default `["**/*"]` |
| `excludes` | From user exclusion hints; common defaults for `vendor/`, `node_modules/` |
| `case` | Default `smart` unless user specifies case sensitivity |
```

---

### Phase 5: Remove Standalone Implementations

Once skills invoke the CLI, remove the old standalone Python:

```bash
rm -rf skills/grep/scripts/src/cli.py
rm -rf skills/find/scripts/src/cli.py
rm -rf skills/diff/scripts/src/cli.py
rm -rf skills/ls/scripts/src/cli.py
```

Keep `scripts/src/` only if needed for validation helpers.

---

### Phase 6: Update Install

Use the repository install scripts to ensure the CLI is installed:

```bash
./scripts/install.sh
```

---

## Skill-CLI Contract

### What the Skill Provides

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Routing** | `00_ROUTER.md` | Progressive disclosure, scope control |
| **Reasoning Contract** | `02_CONTRACTS.md`, `assets/schemas/` | Bounds agent interpretation |
| **Guardrails** | `04_NEVER.md`, `05_ALWAYS.md` | Behavioral constraints |
| **Procedure** | `06_PROCEDURE.md` | Execution steps (invokes CLI) |
| **Error Handling** | `07_FAILURES.md` | Recovery guidance |

### What the CLI Provides

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Execution** | `aux <cmd>` | Deterministic execution |
| **Schema** | `--schema` | JSON schema for plans |
| **Validation** | `--plan` | Schema-validated input |
| **Doctor** | `aux doctor` | Dependency checking |

### Interface Contract

```
Skill                           CLI
  │                              │
  │  aux grep --schema           │
  │ ─────────────────────────────►
  │                              │
  │  ◄───────── JSON Schema ─────┤
  │                              │
  │  Agent generates plan        │
  │  conforming to schema        │
  │                              │
  │  aux grep --plan '<json>'    │
  │ ─────────────────────────────►
  │                              │
  │  ◄───── Structured output ───┤
  │                              │
```

---

## Migration Checklist

### Per-Skill Checklist

- [ ] `scripts/skill.sh` invokes `aux <cmd>`
- [ ] `scripts/skill.ps1` invokes `aux <cmd>`
- [ ] `assets/schemas/` contains CLI-exported schema
- [ ] `assets/templates/` contains plan template
- [ ] `06_PROCEDURE.md` references CLI invocation
- [ ] `02_CONTRACTS.md` references schema for reasoning contract
- [ ] Old standalone Python removed (or moved to validation helpers)
- [ ] `./scripts/install.sh` installs the CLI and verifies dependencies

### Global Checklist

- [ ] `cli/skills/` removed (not actual skills)
- [ ] CLI installed and `aux doctor` passes
- [ ] All skills validate: `scripts/skill.sh validate`
- [ ] End-to-end test: plan → skill → CLI → output

---

## Benefits

1. **Single source of truth** — CLI kernels are the execution backend; no duplicate implementations
2. **ASI compliance** — Skills retain full governance structure (references, contracts, guardrails)
3. **Entropy control** — Schemas bound agent interpretation before execution
4. **Progressive disclosure** — Router enables incremental loading
5. **Portability** — Skills can be distributed independently; CLI is a declared dependency
6. **Testability** — CLI can be tested in isolation; skills test the contract layer

---

## Open Questions

1. **Schema versioning** — Should skills maintain multiple schema versions (v1, v2) or track CLI version?
2. **Offline mode** — Should skills bundle a fallback if CLI is unavailable?
3. **Composite skills** — `scan` is a composite (find → grep). Should it have its own skill or be documented as a CLI feature?

---

## Next Steps

1. Execute Phase 1: Remove `cli/skills/`
2. Execute Phase 2: Create `skill.sh` / `skill.ps1` for each skill
3. Execute Phase 3: Export and align schemas
4. Execute Phase 4: Update references to use CLI
5. Execute Phase 5: Remove standalone implementations
6. Test end-to-end
