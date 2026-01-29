#!/usr/bin/env bash
# grep skill - Agent-assisted text search
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
grep - Agent-assisted text search (deterministic ripgrep wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a deterministic text search

Options (run):
  --root <path>                Root directory (default: .)
  --pattern <text>             Search pattern (repeatable)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --case <sensitive|insensitive|smart>  Case behavior (default: smart)
  --context <n>                Lines of context (default: 0)
  --max-matches <n>            Max matches (default: 1000)
  --stdin                      Read plan JSON from stdin

Execution backend: aux grep (aux-skills CLI)
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
    aux grep --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux grep --plan "$plan"
    else
        # CLI argument passthrough
        aux grep "$@"
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
