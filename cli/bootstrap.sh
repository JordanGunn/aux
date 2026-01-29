#!/usr/bin/env bash
set -euo pipefail

echo "=== AUx CLI Bootstrap ==="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "error: python3 required"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "ok: python3 $PYTHON_VERSION"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install aux-skills in development mode
echo "Installing aux-skills..."
pip install -e "$SCRIPT_DIR" --quiet

# Verify installation
if ! command -v aux &>/dev/null; then
    echo "error: aux command not found after install"
    exit 1
fi

echo "ok: aux $(aux --version 2>&1 | head -1)"

# Run doctor to check system dependencies
echo ""
echo "Checking system dependencies..."
aux doctor

echo ""
echo "=== Bootstrap complete ==="
