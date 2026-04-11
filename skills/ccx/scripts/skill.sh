#!/usr/bin/env bash
# ccx skill - Cyclomatic + Cognitive Complexity per function (McCabe + Campbell)
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
ccx - Cyclomatic + Cognitive Complexity per function (McCabe 1976 + Campbell 2018)

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute complexity analysis

Usage (run):
  skill.sh run --root <path> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --language <lang>            Restrict to one language (repeatable)
                               Supported: python, javascript, typescript, go, rust, java
  --glob <pattern>             Override include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-results <n>            Max functions in output (post-sort cap)
  --min-ccx <n>                Filter — only return functions with ccx >= n (default: 1)

Examples:
  skill.sh run --root ./src
  skill.sh run --root ./src --language python --min-ccx 11
  skill.sh run --root ./src --max-results 20
  echo '{"root":"./src","languages":["python"]}' | skill.sh run --stdin

Execution backend: aux ccx (aux-skills CLI)
EOF
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
    aux ccx --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux ccx --plan "$plan"
    else
        # CLI argument passthrough
        aux ccx "$@"
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
