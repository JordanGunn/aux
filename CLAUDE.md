# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and Installation

```bash
# Install aux CLI and validate system dependencies (requires uv, rg, fd/fdfind, git, diff)
./scripts/install.sh

# Verify dependencies post-install
aux doctor
```

## Common Commands

```bash
# Run all tests
cd cli && python -m pytest

# Run a single test file
cd cli && python -m pytest tests/path/to/test_file.py

# Lint
cd cli && ruff check src/

# Get schema for any skill (source of truth)
aux grep --schema
aux find --schema
aux diff --schema
aux ls --schema

# Validate a skill is runnable
./skills/grep/scripts/skill.sh validate

# Emit all reference docs for a skill (agent onboarding)
./skills/grep/scripts/skill.sh init
```

## Architecture

### CLI Layer (`cli/`)

Python package (`aux-skills`, Python ≥3.10) installed via `uv tool install`. Entry point: `aux.cli:main`.

Each command follows the same layered pattern:

```
commands/<skill>.py   → arg parsing, plan construction, output formatting
plans/schemas.py      → Pydantic models (GrepPlan, FindPlan, SearchPlan, ...)
kernels/<skill>.py    → deterministic execution (uses ThreadPoolExecutor for concurrency)
util/subprocess.py    → subprocess wrapper for system tools (rg, fd, git diff)
output/               → format_output(), TTY detection, truncation
```

**Two invocation modes for every command:**
- Simple: `aux grep "pattern" --root /path --glob "*.py"`
- Plan: `aux grep --plan '<json>'` — accepts a full plan JSON matching the Pydantic schema

`--schema` flag on any command prints the JSON schema for that skill's plan.

### Skills Layer (`skills/`)

Each skill is fully self-contained and independent:

```
skills/<name>/
  SKILL.md                  # Frontmatter manifest (name, version, scripts, keywords)
  references/
    01_SUMMARY.md           # Identity, scope, constraints
    02_INTENT.md            # When and why to invoke
    03_POLICIES.md          # Explicit prohibitions and mandates
    04_PROCEDURE.md         # Step-by-step execution flow
  scripts/
    skill.sh                # Main entry (Unix): init | validate | schema | run
    skill.ps1               # Main entry (Windows)
```

`skill.sh init` concatenates all reference docs — this is the agent onboarding entrypoint. `skill.sh run` delegates to the `aux` CLI backend.

### `search` Command

Hierarchical pipeline: `fd` → `rg` [→ `tree-sitter`]. Defined in `commands/search.py`
and uses `find_kernel`, `grep_kernel`, and optionally `query_kernel`.

## Core Constraints

These apply to all skills and the CLI:

- **Read-only by default** — no filesystem mutation
- **Deterministic** — same input must produce same output; no hidden state
- **Schema is source of truth** — run `aux <skill> --schema` before assuming field names
- **Agents select parameters; scripts execute** — kernels own execution, not the agent

## Adding a New Skill

1. Copy structure from an existing skill (e.g., `skills/grep/`)
2. Implement `scripts/skill.sh` and `scripts/skill.ps1`
3. Add a Pydantic plan model to `cli/src/aux/plans/schemas.py`
4. Implement the kernel in `cli/src/aux/kernels/<skill>.py`
5. Register the command parser in `cli/src/aux/commands/<skill>.py` and wire it in `cli.py`
6. Write numbered reference docs under `skills/<name>/references/`
7. Add a `docs/skills/<SKILL>.md` documentation file

## ASI Alignment

Skills follow the [ASI (Agentic Skill Interface)](https://github.com/JordanGunn/asi) governance model. Before designing a new skill, consult the ASI framework for determinism, replayability, and scope-bounding requirements.
