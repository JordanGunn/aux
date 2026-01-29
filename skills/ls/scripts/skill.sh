#!/usr/bin/env bash
# ls skill - Deterministic directory state inspection
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
ls - Deterministic directory state inspection (bounded inventory + ranking)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a deterministic directory inventory

Options (run):
  <path>                       Directory to list (default: .)
  --depth <n>                  Recursion depth (default: 1)
  --sort <name|size|time>      Sort order (default: name)
  --hidden                     Include hidden files
  --max-entries <n>            Max entries (default: 100)
  --stdin                      Read plan JSON from stdin

Execution backend: aux ls (aux-skills CLI)
EOF
}

cmd_validate() {
    local errors=0

    if ! command -v aux &>/dev/null; then
        echo "error: aux CLI not found. Install with: pip install aux-skills" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux ls --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux ls --plan "$plan"
    else
        # CLI argument passthrough
        aux ls "$@"
    fi
}

case "${1:-help}" in
    help)
        cmd_help
        ;;
    validate)
        cmd_validate
        ;;
    schema)
        cmd_schema
        ;;
    run)
        shift
        cmd_run "$@"
        ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'skill.sh help' for usage" >&2
        exit 1
        ;;
esac
