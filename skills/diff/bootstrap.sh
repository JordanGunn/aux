#!/usr/bin/env bash
# diff skill bootstrap - verifies aux CLI is available
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for aux CLI
if ! command -v aux &>/dev/null; then
    echo "error: aux CLI not found" >&2
    echo "Install with: pip install aux-skills" >&2
    echo "Or from source: pip install -e /path/to/aux/cli" >&2
    exit 1
fi

# Validate dependencies via CLI doctor
if ! aux doctor > /dev/null 2>&1; then
    echo "error: aux doctor check failed" >&2
    aux doctor
    exit 1
fi

echo "ok: diff skill ready (aux CLI available)"
