#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

cmd_help() {
    cat <<'EOF'
find - Agent-assisted file enumeration (deterministic fd wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  run [opts]                   Execute a deterministic file enumeration

Options (run):
  --root <path>                Root directory (default: .)
  --pattern <pattern>          Glob pattern for names (repeatable)
  --extension <ext>            File extension without dot (repeatable)
  --exclude <pattern>          Exclude pattern (repeatable)
  --type <file|directory|any>  Entry type (default: file)
  --max-depth <n>              Maximum directory depth
  --max-results <n>            Max results (default: 1000)
  --format <auto|human|jsonl>  Output format (default: auto)
  --hidden                     Include hidden files
  --follow                     Follow symlinks
  --no-ignore                  Ignore .gitignore rules
  --stdin                      Read plan JSON from stdin
EOF
}

cmd_validate() {
    local errors=0

    if ! command -v uv &>/dev/null; then
        echo "error: uv not found. Install from https://docs.astral.sh/uv/" >&2
        errors=$((errors + 1))
    fi

    if ! command -v fd &>/dev/null && ! command -v fdfind &>/dev/null; then
        echo "error: fd not found. Install fd-find (binary may be 'fdfind' on Debian/Ubuntu)." >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SRC_DIR/pyproject.toml" ]]; then
        echo "error: missing $SRC_DIR/pyproject.toml" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SRC_DIR/cli.py" ]]; then
        echo "error: missing $SRC_DIR/cli.py" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    echo "ok: find skill is runnable"
}

cmd_run() {
    uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/cli.py" run "$@"
}

case "${1:-help}" in
    help)
        cmd_help
        ;;
    validate)
        cmd_validate
        ;;
    run)
        shift
        cmd_run "$@"
        ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'find help' for usage" >&2
        exit 1
        ;;
esac
