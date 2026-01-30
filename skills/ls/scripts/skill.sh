#!/usr/bin/env bash
# ls skill - Deterministic directory state inspection
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'HELP'
ls - Deterministic directory state inspection (bounded inventory + ranking)

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] [path]            Execute a deterministic directory inventory

Usage (run):
  skill.sh run [path] [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  [path]                       Directory to list (positional, default: .)
  --depth <n>                  Recursion depth (default: 1)
  --sort <name|size|time>      Sort order (default: name)
  --hidden                     Include hidden files
  --size                       Show file sizes (default: true)
  --time                       Show modification times
  --max-entries <n>            Max entries to return

Examples:
  skill.sh run ./src
  skill.sh run /path --depth 2 --sort size --hidden
  echo '{"path":"/path","depth":3}' | skill.sh run --stdin

Execution backend: aux ls (aux-skills CLI)
HELP
}

cmd_init() {
    local refs_dir="$SKILL_DIR/references"
    local idx=1

    # Emit TOC header first
    echo "# References"
    echo ""
    for f in "$refs_dir"/[0-9][0-9]_*.md; do
        [[ "$(basename "$f")" == "00_ROUTER.md" ]] && continue
        [[ -f "$f" ]] || continue
        local name desc
        name=$(basename "$f" .md | sed 's/^[0-9]*_//')
        desc=$(grep -m1 '^description:' "$f" 2>/dev/null | sed 's/^description:[[:space:]]*//' || echo "")
        echo "${idx}. **${name}** — ${desc}"
        idx=$((idx + 1))
    done
    echo ""
    echo "---"
    echo ""

    # Emit content
    for f in "$refs_dir"/[0-9][0-9]_*.md; do
        [[ "$(basename "$f")" == "00_ROUTER.md" ]] && continue
        [[ -f "$f" ]] || continue
        cat "$f"
        echo ""
    done
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
    init)
        cmd_init
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
