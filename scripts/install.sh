#!/usr/bin/env bash
# AUx Skills - Unified Installation
# Installs the aux CLI and validates system dependencies
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CLI_DIR="$ROOT_DIR/cli"

echo "AUx Skills Installation"
echo "======================="
echo

# -----------------------------------------------------------------------------
# Phase 1: Check system dependencies
# -----------------------------------------------------------------------------
echo "Checking system dependencies..."

errors=0

# Check for uv (required for installation)
if ! command -v uv &>/dev/null; then
    echo "  ✗ uv not found"
    echo "    Install from: https://docs.astral.sh/uv/"
    errors=$((errors + 1))
else
    echo "  ✓ uv: $(uv --version 2>/dev/null | head -1)"
fi

# Check for ripgrep (required for grep skill)
if ! command -v rg &>/dev/null; then
    echo "  ✗ rg (ripgrep) not found"
    echo "    Install: apt install ripgrep | brew install ripgrep"
    errors=$((errors + 1))
else
    echo "  ✓ rg: $(rg --version 2>/dev/null | head -1)"
fi

# Check for fd (required for find skill)
if command -v fd &>/dev/null; then
    echo "  ✓ fd: $(fd --version 2>/dev/null | head -1)"
elif command -v fdfind &>/dev/null; then
    echo "  ✓ fdfind: $(fdfind --version 2>/dev/null | head -1)"
else
    echo "  ✗ fd/fdfind not found"
    echo "    Install: apt install fd-find | brew install fd"
    errors=$((errors + 1))
fi

# Check for git (required for diff skill)
if ! command -v git &>/dev/null; then
    echo "  ✗ git not found"
    errors=$((errors + 1))
else
    echo "  ✓ git: $(git --version 2>/dev/null)"
fi

# Check for diff (required for diff skill)
if ! command -v diff &>/dev/null; then
    echo "  ✗ diff not found"
    errors=$((errors + 1))
else
    echo "  ✓ diff: $(diff --version 2>/dev/null | head -1)"
fi

echo

if [[ $errors -gt 0 ]]; then
    echo "ERROR: $errors missing system dependencies"
    echo "Please install the missing dependencies and re-run this script."
    exit 1
fi

echo "All system dependencies available."
echo

# -----------------------------------------------------------------------------
# Phase 2: Install aux CLI
# -----------------------------------------------------------------------------
echo "Installing aux CLI..."

if [[ ! -f "$CLI_DIR/pyproject.toml" ]]; then
    echo "ERROR: CLI not found at $CLI_DIR"
    echo "Ensure you're running this from the aux repository root."
    exit 1
fi

# Install as a tool using uv (creates isolated environment)
cd "$CLI_DIR"
uv tool install --editable ".[query,curl,dev]" --force --quiet

echo "  ✓ aux CLI installed (via uv tool)"
echo

# -----------------------------------------------------------------------------
# Phase 3: Verify installation
# -----------------------------------------------------------------------------
echo "Verifying installation..."

if ! command -v aux &>/dev/null; then
    echo "  ✗ aux command not found in PATH"
    echo "    You may need to activate your virtual environment or add ~/.local/bin to PATH"
    exit 1
fi

echo "  ✓ aux: $(aux --version 2>/dev/null)"

# Run doctor to verify all dependencies
echo
echo "Running aux doctor..."
aux doctor

echo
echo "======================="
echo "Installation complete!"
echo
echo "Available skills:"
echo "  - search:       Find files by pattern (fd → rg [→ tree-sitter])"
echo "  - files:        Enumerate files by name/glob"
echo "  - find:         AST structural search (tree-sitter)"
echo "  - usages:       Symbol cross-reference (definitions + references)"
echo "  - deps:         Import graph — coupling, cycles, blast radius"
echo "  - delta:        Semantic git diff (files + symbols changed)"
echo "  - prune:        Dead code candidates (advisory)"
echo "  - robert:       Robert C. Martin package design metrics"
echo "  - replace:      Bulk fixed-string replacement (dry-run by default)"
echo "  - rename:       Move/rename files and directories (dry-run by default)"
echo "  - curl:         HTTP fetch with progressive disclosure"
echo "  - capabilities: Skill registry for agent discovery"
echo
echo "Usage:"
echo "  aux search \"pattern\" --root /path --glob \"**/*.py\""
echo "  aux files --root /path --glob \"**/*.go\""
echo "  aux deps --root /path --language python"
echo "  aux robert --root /path --language go"
echo
echo "For skill invocation via scripts:"
echo "  ./skills/search/scripts/skill.sh run \"pattern\" --root /path"
