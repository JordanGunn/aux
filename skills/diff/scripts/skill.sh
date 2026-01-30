#!/usr/bin/env bash
# diff skill - Deterministic file/directory comparison
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
diff - Deterministic file/directory comparison

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] <path_a> <path_b> Execute a file/directory comparison

Usage (run):
  skill.sh run <path_a> <path_b> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  <path_a> <path_b>            Paths to compare (positional, required)
  --context <n>                Lines of context (default: 3)
  --ignore-whitespace          Ignore whitespace differences
  --ignore-case                Ignore case differences

Examples:
  skill.sh run ./old.txt ./new.txt
  skill.sh run /path/a /path/b --context 5 --ignore-whitespace
  echo '{"path_a":"/a","path_b":"/b"}' | skill.sh run --stdin

Execution backend: aux diff (aux-skills CLI)
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
    aux diff --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux diff --plan "$plan"
    else
        # CLI argument passthrough
        aux diff "$@"
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
