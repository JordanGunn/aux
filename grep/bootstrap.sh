#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/scripts/src"

if ! command -v uv &>/dev/null; then
    echo "error: uv not found. Install from https://docs.astral.sh/uv/" >&2
    exit 1
fi

if [[ ! -f "$SRC_DIR/pyproject.toml" ]]; then
    echo "error: missing $SRC_DIR/pyproject.toml" >&2
    exit 1
fi

cd "$SRC_DIR"
uv sync

echo "ok: grep bootstrap complete"
