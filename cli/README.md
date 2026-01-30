# AUx CLI

Unified command-line interface for AUx (Agentic Unix) skills.

## Installation

```bash
pip install aux-skills
```

Or for development:

```bash
../scripts/install.sh
```

## Usage

```bash
# Help
aux --help
aux grep --help

# Get JSON schema for plan-based invocation
aux grep --schema

# Simple invocation
aux grep "pattern" --root /path --glob "**/*.py"
aux find --root /path --glob "**/*.go" --type file
aux ls /path --depth 2 --sort size
aux diff /path/a /path/b

# Plan-based invocation (for agents)
aux grep --plan '{"root":"/path","patterns":[{"kind":"regex","value":"TODO"}]}'

# Composite pipeline (find → grep)
aux scan --plan '{"root":"/path","surface":{"globs":["**/*.go"]},"search":{"patterns":[{"value":"auth"}]}}'

# System check
aux doctor
```

## Commands

| Command | Description |
|---------|-------------|
| `grep` | Search patterns in files (ripgrep) |
| `find` | Locate files by name/glob (fd) |
| `diff` | Compare files or directories |
| `ls` | List directory contents with metadata |
| `scan` | Composite: find → grep (in-process pipeline) |
| `doctor` | Verify system dependencies |

## Architecture

The CLI uses a kernel-based architecture:

- **Kernels** (`src/aux/kernels/`): Pure functions operating on data structures
- **Commands** (`src/aux/commands/`): Thin CLI wrappers around kernels
- **Plans** (`src/aux/plans/`): Pydantic schemas for structured input
- **Output** (`src/aux/output/`): Formatting and truncation utilities

Composition happens at the kernel level, enabling in-process pipelines without intermediate I/O.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUX_OUTPUT` | Output format: `json`, `text`, `summary` | `json` |
| `AUX_MAX_MATCHES` | Maximum matches to return | unlimited |

## System Dependencies

- `rg` (ripgrep) - for grep command
- `fd` (fd-find) - for find command
- `git` - for diff features
- `diff` - for diff command

Run `aux doctor` to check availability.
