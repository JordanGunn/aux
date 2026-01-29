# Quickstart

Get up and running with aux skills in minutes.

---

## Prerequisites

- **Python 3.10+** (3.11+ for diff skill)
- **uv** — Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
- **git** — For diff and ls git-status features
- **ripgrep** (`rg`) — For grep skill
- **fd** (`fd` or `fdfind`) — For find skill
  - Debian/Ubuntu: `apt install fd-find` (installs as `fdfind`)
  - macOS: `brew install fd`
  - Arch: `pacman -S fd`

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

| Skill | Purpose |
| ----- | ------- |
| **grep** | Agent-assisted text search using `rg` (ripgrep) |
| **find** | Agent-assisted file enumeration using `fd` |
| **diff** | Deterministic git diff inspection |
| **ls** | Deterministic directory state inspection with optional git status |

See [skills/](skills/) for detailed documentation on each skill.

## Next Steps

- See [skills/](skills/) for detailed documentation on each skill
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
- See [CHANGELOG.md](../CHANGELOG.md) for version history

---

> **Tip**: Skills can also be installed and managed across vendors or agentic tooling using
> the [asr CLI](https://github.com/JordanGunn/asr) (Agentic Skill Registry).
