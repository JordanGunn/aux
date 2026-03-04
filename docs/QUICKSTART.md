# Quickstart

Get up and running with aux skills in minutes.

---

## Prerequisites

- **Python 3.10+**
- **uv** — Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- **ripgrep** (`rg`) — For search, usages, prune, replace
- **fd** (`fd` or `fdfind`) — For files, search, prune, deps, rename
  - Debian/Ubuntu: `apt install fd-find` (installs as `fdfind`)
  - macOS: `brew install fd`
  - Arch: `pacman -S fd`
- **git** — For delta skill

---

## Install

From the repository root, run the install script to set up the `aux` CLI:

```bash
# Unix/Linux/macOS
./scripts/install.sh

# Windows PowerShell
./scripts/install.ps1
```

This will:

1. Validate that required tools are installed
2. Install the `aux` CLI as a `uv` tool
3. Run `aux doctor` to verify system dependencies

---

## How Skills Are Invoked

All skills in the `AUx` collection are designed to be called by agents or agentic tooling.

Each skill:

- **Self-validates** on invocation — no manual validation step required
- **Receives plans** from the agent in JSON format
- **Emits structured output** for agent consumption

The agent interprets natural language, generates an appropriate plan, invokes the skill, and synthesizes the results.

## What You Get

| Skill | Category | Purpose |
| ----- | -------- | ------- |
| **files** | read | Enumerate files by name/glob (fd) |
| **search** | read | Hierarchical pipeline: fd → rg [→ tree-sitter AST] |
| **find** | read | Tree-sitter AST structural search |
| **usages** | analysis | Symbol cross-reference: definitions + references |
| **prune** | analysis | Dead code candidate audit (advisory) |
| **deps** | analysis | Module dependency graph: coupling, cycles, blast radius |
| **delta** | analysis | Semantic git diff: files changed + symbols added/removed |
| **replace** | write | Bulk fixed-string replacement (dry-run by default) |
| **rename** | write | Move/rename files or directories (dry-run by default) |
| **curl** | network | Agent-optimised HTTP fetch with progressive disclosure |
| **capabilities** | meta | Emit skill registry for agent discovery/routing |

See [skills/](../skills/) for detailed documentation on each skill.

## Next Steps

- See [skills/](skills/) for detailed documentation on each skill
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
- See [CHANGELOG.md](../CHANGELOG.md) for version history

---

> **Tip**: Skills can also be installed and managed across vendors or agentic tooling using
> the [asr CLI](https://github.com/JordanGunn/asr) (Agentic Skill Registry).
