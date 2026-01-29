# Contributing to aux

Thank you for your interest in contributing to `aux`.

## Philosophy

`aux` follows the [ASI](https://github.com/JordanGunn/asi) governance model. Before contributing, familiarize yourself with the core principles:

- **Deterministic maximalism** — Scripts own execution, not agents
- **Subjective minimalism** — Agents select parameters only where humans fail
- **Reason-after-reduction** — Shrink the surface first, reason on results
- **Replayability** — Every run produces artifacts; no silent overwrites

## Skill Structure

Each skill is self-contained and follows this layout:

```text
<skill>/
  SKILL.md              # Skill manifest (name, description, metadata)
  assets/
    schemas/            # JSON schemas for plans and receipts
  references/
    00_ROUTER.md        # Entry point for agent navigation
    01_SUMMARY.md       # Identity, scope, constraints
    02_CONTRACTS.md     # Input/output contracts
    02_SCHEMAS.md       # Schema documentation
    03_TRIGGERS.md      # When to invoke the skill
    04_NEVER.md         # Explicit prohibitions
    05_ALWAYS.md        # Mandatory behaviors
    06_PROCEDURE.md     # Step-by-step execution flow
    07_FAILURES.md      # Error handling
  scripts/
    skill.sh            # Main entry point (Unix)
    skill.ps1           # Main entry point (Windows)
```

## Adding a New Skill

1. **Create the skill directory** under `aux/`
2. **Copy structure** from an existing skill (e.g., `grep/`)
3. **Write the SKILL.md** with proper frontmatter
4. **Implement scripts** in `scripts/skill.sh` and `scripts/skill.ps1`
5. **Define schemas** in `assets/schemas/`
6. **Document references** following the numbered convention
7. **Update docs/** with a new `<SKILL>.md` file

## Modifying Existing Skills

- **Never break determinism** — Output must be reproducible for the same input
- **Never add hidden state** — All parameters must be visible in invocation
- **Never mutate filesystem** — Skills are read-only by default
- **Preserve schema compatibility** — Version schemas when making breaking changes

## Code Style

### Shell Scripts

- Use `set -euo pipefail` for bash
- Use `$ErrorActionPreference = "Stop"` for PowerShell
- Validate dependencies before execution
- Emit clear error messages with actionable instructions

### Python

- Target Python 3.10+
- Use `uv` for dependency management
- Keep dependencies minimal
- Emit JSONL for machine-readable output
- Emit human-readable output when stdout is a TTY

## Testing

Before submitting changes:

1. Run `./scripts/install.sh` (or `./scripts/install.ps1`) to install the aux CLI and verify system dependencies
2. Run `scripts/skill.sh validate` to verify the skill is runnable
3. Test with representative inputs
4. Verify output matches documented schemas

## Pull Request Guidelines

1. **One skill per PR** when adding new skills
2. **Describe the change** — What problem does it solve?
3. **Include examples** — Show before/after or sample invocations
4. **Update CHANGELOG.md** — Add entry under `[Unreleased]`
5. **Update docs/** — Keep documentation in sync

## Reporting Issues

When reporting issues, include:

- Skill name and version
- Operating system and shell
- Full command invocation
- Expected vs actual behavior
- Relevant error output

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
