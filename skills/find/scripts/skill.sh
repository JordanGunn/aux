#!/usr/bin/env bash
# find skill - Agent-assisted file enumeration
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
find - Agent-assisted file enumeration (deterministic fd wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a deterministic file enumeration

Options (run):
  --root <path>                Root directory (default: .)
  --glob <pattern>             Glob pattern for names (repeatable)
  --exclude <pattern>          Exclude pattern (repeatable)
  --type <file|directory|any>  Entry type (default: file)
  --max-depth <n>              Maximum directory depth
  --max-results <n>            Max results (default: 500)
  --hidden                     Include hidden files
  --stdin                      Read plan JSON from stdin

Execution backend: aux find (aux-skills CLI)
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
    aux find --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux find --plan "$plan"
    else
        # CLI argument passthrough
        aux find "$@"
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
